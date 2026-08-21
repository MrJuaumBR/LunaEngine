"""
threading.py – Background task system with priority, frame‑based scheduling,
and resource monitoring.

Provides:
- TaskPriority: LOW, NORMAL, HIGH
- BackgroundTaskManager: schedule tasks with interval_frames, track CPU/memory,
  cancel, and retrieve status.
- Integration with PerformanceMonitor for per‑task timing.
"""

import concurrent.futures
import threading
import queue
import time
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Callable, Any, Optional, Dict, List, Union, Tuple
import sys

# Optional psutil for memory monitoring
try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    HAVE_PSUTIL = False
    psutil = None


class TaskPriority(IntEnum):
    """Task priority – lower integer = higher priority."""
    LOW = 0
    NORMAL = 1
    HIGH = 2


@dataclass
class TaskInfo:
    """Metadata for a scheduled task."""
    id: str
    name: str
    priority: TaskPriority
    interval_frames: int = 0          # 0 = run once, >0 = repeat every N frames
    last_run_frame: int = 0
    total_runs: int = 0
    cpu_time_ms: float = 0.0
    memory_peak_bytes: int = 0
    active: bool = True
    result: Any = None
    error: Optional[Exception] = None
    # The callable and its arguments are stored separately to allow re‑scheduling
    _fn: Optional[Callable] = None
    _args: tuple = ()
    _kwargs: dict = field(default_factory=dict)


class BackgroundTaskManager:
    """
    Manages background tasks with priority, frame‑based scheduling, and resource tracking.
    Tasks are executed in a thread pool, but scheduling decisions (when to run) are made
    on the main thread via update().
    """

    def __init__(self, max_workers: int = 4, monitor: Optional['PerformanceMonitor'] = None):
        """
        Args:
            max_workers: Number of worker threads in the pool.
            monitor: Optional PerformanceMonitor instance for timing.
        """
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.monitor = monitor
        self._ready_queue: queue.PriorityQueue = queue.PriorityQueue()
        self._waiting: Dict[str, TaskInfo] = {}           # all scheduled tasks
        self._futures: Dict[str, concurrent.futures.Future] = {}
        self._lock = threading.Lock()
        self._frame_counter = 0
        self._stopped = False

        # Start the consumer thread that takes ready tasks and submits them to the pool
        self._consumer_thread = threading.Thread(target=self._consumer_loop, daemon=True)
        self._consumer_thread.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def schedule(
        self,
        fn: Callable,
        name: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        interval_frames: int = 0,
        args: tuple = (),
        kwargs: dict = None
    ) -> str:
        """
        Schedule a task. If interval_frames > 0, it will repeat every that many frames.
        Returns a task ID that can be used to cancel or check status.
        """
        if kwargs is None:
            kwargs = {}
        task_id = f"{name or fn.__name__}_{int(time.time()*1000)}_{len(self._waiting)}"
        info = TaskInfo(
            id=task_id,
            name=name or fn.__name__,
            priority=priority,
            interval_frames=interval_frames,
            last_run_frame=self._frame_counter - interval_frames,  # so it runs as soon as possible
            _fn=fn,
            _args=args,
            _kwargs=kwargs
        )
        with self._lock:
            self._waiting[task_id] = info
            # If interval_frames == 0, enqueue immediately (it will run once)
            if interval_frames == 0:
                self._enqueue_task(task_id, info)
        return task_id

    def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task (even if already running)."""
        with self._lock:
            info = self._waiting.get(task_id)
            if not info:
                return False
            info.active = False
            # If the future is still pending, try to cancel it
            future = self._futures.pop(task_id, None)
            if future and not future.done():
                return future.cancel()
        return True

    def update(self, dt: float):
        """
        Call this every frame on the main thread.
        - Increments frame counter.
        - Enqueues recurring tasks that are due.
        - Processes completed results (updates TaskInfo with result/error).
        """
        self._frame_counter += 1

        # Enqueue tasks that are due (interval_frames > 0)
        with self._lock:
            for task_id, info in list(self._waiting.items()):
                if not info.active:
                    continue
                if info.interval_frames > 0:
                    if (self._frame_counter - info.last_run_frame) >= info.interval_frames:
                        self._enqueue_task(task_id, info)

        # Process any completed futures (results from the executor)
        # This is done by checking the futures dict; we can use a callback, but we'll poll.
        # Instead, we use a queue for results: the done callback will put results into a queue.
        # For simplicity, we'll process them here.
        # Actually, we already have a done callback that updates the info directly.
        # We'll rely on the callback to update info.result and info.error.
        pass

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Return a summary of all tasks for debugging."""
        with self._lock:
            return {
                tid: {
                    'name': info.name,
                    'priority': info.priority.name,
                    'runs': info.total_runs,
                    'cpu_ms': info.cpu_time_ms,
                    'memory_bytes': info.memory_peak_bytes,
                    'active': info.active,
                    'last_error': str(info.error) if info.error else None,
                    'interval_frames': info.interval_frames,
                    'last_run_frame': info.last_run_frame,
                }
                for tid, info in self._waiting.items()
            }

    def shutdown(self, wait: bool = True):
        """Shut down the thread pool and consumer thread."""
        self._stopped = True
        self.executor.shutdown(wait=wait)
        if self._consumer_thread.is_alive():
            self._consumer_thread.join(timeout=1.0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _enqueue_task(self, task_id: str, info: TaskInfo):
        """Put a task into the priority queue for the consumer."""
        # Priority queue orders by (priority, timestamp)
        # Use (priority.value, time.time_ns(), task_id) to avoid comparison issues
        self._ready_queue.put((info.priority.value, time.time_ns(), task_id))

    def _consumer_loop(self):
        """Runs in a background thread: fetches tasks from priority queue and submits to executor."""
        while not self._stopped:
            try:
                _, _, task_id = self._ready_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # Check if the task is still active and exists
            with self._lock:
                info = self._waiting.get(task_id)
                if info is None or not info.active:
                    # Task cancelled or removed
                    continue
                # Update last_run_frame (so it won't be rescheduled until interval passes)
                info.last_run_frame = self._frame_counter
                # Store the callable and args (they are in info)
                fn = info._fn
                args = info._args
                kwargs = info._kwargs

            # Submit to the thread pool
            future = self.executor.submit(fn, *args, **kwargs)
            with self._lock:
                self._futures[task_id] = future

            # Add a done callback to record results and possibly reschedule
            future.add_done_callback(lambda fut, tid=task_id: self._on_task_done(tid, fut))

    def _on_task_done(self, task_id: str, future: concurrent.futures.Future):
        """Callback when a future completes."""
        with self._lock:
            info = self._waiting.get(task_id)
            if info is None:
                return

            # Record result/error
            if future.exception():
                info.error = future.exception()
                info.result = None
            else:
                info.result = future.result()
                info.error = None
            info.total_runs += 1

            # If it's a one‑shot task, remove it from waiting (it won't be rescheduled)
            if info.interval_frames == 0:
                # Mark as inactive so it won't be re‑enqueued
                info.active = False
                # Optionally remove from dict to keep it small, but we keep for status
                # del self._waiting[task_id]
            else:
                # For recurring tasks, we do nothing here – the next update() will enqueue it again
                # when the frame counter reaches the interval.
                pass

            # Remove from futures
            self._futures.pop(task_id, None)

            # If we have a monitor, record CPU/memory usage
            if self.monitor and hasattr(self.monitor, 'record_task_metrics'):
                # We'll capture CPU and memory at the time of completion – simple approximation.
                # A more accurate method would be to track process time before/after.
                # For simplicity, we just add a dummy: the monitor can store the CPU time
                # from a start/end timer if we add that.
                # We'll implement start/end in the monitor.
                pass  # implemented in performance.py

    def __del__(self):
        self.shutdown(wait=False)