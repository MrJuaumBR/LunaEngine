"""
performance.py – Performance monitoring, profiling, and garbage collection.

Provides:
- PerformanceMonitor: FPS tracking, hardware info, and task timing.
- GarbageCollector: automatic cleanup of caches.
- Integration with BackgroundTaskManager for per‑task CPU/memory metrics.
"""

import sys
import time
import platform
import threading
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any, Callable

try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    HAVE_PSUTIL = False
    psutil = None

import pygame
from . import math_utils

# ----------------------------------------------------------------------
# TimeProfile (unchanged, but kept for completeness)
# ----------------------------------------------------------------------

class TimeProfile:
    def __init__(self, category: str = "", max_history: int = 60):
        self.category = category
        self.start_time = 0.0
        self.end_time = 0.0
        self.history = deque(maxlen=max_history)
        self._used_this_frame = False

    def start(self):
        self.start_time = time.perf_counter()
        self._used_this_frame = True

    def stop(self):
        self.end_time = time.perf_counter()
        self._used_this_frame = False
        self._insert_new_history()

    def _insert_new_history(self):
        if len(self.history) >= self.history.maxlen:
            self.history.popleft()
        self.history.append((self.end_time - self.start_time) * 1000.0)

    end = stop

    @property
    def duration(self) -> float:
        return self.history[-1] if self.history else 0.0

    def record_current(self):
        if self.start_time > 0 and self.end_time > 0 and self.end_time > self.start_time:
            self.history.append((self.end_time - self.start_time) * 1000.0)
        self.start_time = 0.0
        self.end_time = 0.0
        self._used_this_frame = False


# ----------------------------------------------------------------------
# PerformanceProfiler (unchanged)
# ----------------------------------------------------------------------

class PerformanceProfiler:
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.timers: Dict[str, TimeProfile] = {}
        self._enabled = False
        self._last_frame_timings = {}

    def enable(self, enabled: bool = True):
        self._enabled = enabled

    def disable(self):
        self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    def get_timer(self, category: str) -> TimeProfile:
        if category not in self.timers:
            self.timers[category] = TimeProfile(category)
        return self.timers[category]

    def get_all_timers(self) -> Dict[str, TimeProfile]:
        return self.timers

    def get_timers_list(self) -> List[TimeProfile]:
        return list(self.timers.values())

    def start_timer(self, category: str):
        if not self._enabled:
            return
        self.create_timer(category)
        self.timers[category].start()

    def stop_timer(self, category: str):
        if not self._enabled:
            return
        if category in self.timers:
            self.timers[category].stop()

    def create_timer(self, category: str):
        if category not in self.timers:
            self.timers[category] = TimeProfile(category, self.max_history)

    def begin_frame(self):
        pass

    def end_frame(self):
        if not self._enabled:
            return
        self._last_frame_timings.clear()
        for cat, timer in self.timers.items():
            if timer._used_this_frame:
                timer.record_current()
            self._last_frame_timings[cat] = timer.duration

    def get_frame_timings(self) -> Dict[str, float]:
        return self._last_frame_timings.copy()

    def get_timing_stats(self, category_prefix: str) -> Dict[str, Any]:
        stats = {}
        for timer in self.timers.values():
            if timer.category.startswith(category_prefix):
                stats[timer.category] = {
                    "duration": timer.duration,
                    "history": list(timer.history)
                }
        return stats


# ----------------------------------------------------------------------
# PerformanceMonitor (extended with task metrics)
# ----------------------------------------------------------------------

class PerformanceMonitor:
    def __init__(self, history_size: int = 300):
        self.history_size = history_size
        self.frame_times = deque(maxlen=history_size)
        self.fps_history = deque(maxlen=history_size)
        self.last_frame_time = time.perf_counter()
        self.current_fps = 0.0

        # Profiler
        self.profiler = PerformanceProfiler(max_history=100)

        # Hardware info cache
        self._hardware_info = None
        self._hardware_cache_time = 0
        self._cache_duration = 30.0

        # Task metrics (for background tasks)
        self._task_timers: Dict[str, Dict] = {}   # task_id -> {'cpu_start', 'mem_start'}
        self._task_metrics: Dict[str, Dict] = {}  # task_id -> {'cpu_ms', 'mem_bytes'}

    # ------------------------------------------------------------------
    # Task metric tracking
    # ------------------------------------------------------------------

    def start_task_timer(self, task_id: str):
        """Start measuring CPU time and memory for a background task."""
        if not HAVE_PSUTIL:
            return
        self._task_timers[task_id] = {
            'cpu_start': time.process_time(),
            'mem_start': psutil.Process().memory_info().rss,
        }

    def end_task_timer(self, task_id: str) -> Optional[Dict[str, float]]:
        """Stop measuring and return {'cpu_ms': ..., 'mem_bytes': ...}."""
        data = self._task_timers.pop(task_id, None)
        if not data or not HAVE_PSUTIL:
            return None
        cpu_used = (time.process_time() - data['cpu_start']) * 1000.0  # ms
        mem_used = psutil.Process().memory_info().rss - data['mem_start']
        metrics = {'cpu_ms': cpu_used, 'mem_bytes': mem_used}
        self._task_metrics[task_id] = metrics
        return metrics

    def get_task_metrics(self, task_id: str) -> Optional[Dict[str, float]]:
        """Return the last recorded metrics for a task."""
        return self._task_metrics.get(task_id)

    def clear_task_metrics(self):
        """Clear all stored task metrics."""
        self._task_metrics.clear()

    # ------------------------------------------------------------------
    # Original methods (unchanged)
    # ------------------------------------------------------------------

    def get_frame_timing_breakdown(self) -> Dict[str, float]:
        return self.profiler.get_frame_timings()

    def get_performance_summary(self) -> Dict[str, Any]:
        return {
            "fps": self.get_stats(),
            "frame_timings": self.get_frame_timing_breakdown(),
            "hardware": self.get_hardware_info(),
            "profiling_enabled": self.is_profiling_enabled()
        }

    def enable_profiling(self, enabled: bool = True):
        self.profiler.enable(enabled)

    def is_profiling_enabled(self) -> bool:
        return self.profiler.is_enabled()

    def create_timer(self, category: str):
        return self.profiler.create_timer(category)

    def start_timer(self, category: str):
        self.profiler.start_timer(category)

    def end_timer(self, category: str):
        self.profiler.stop_timer(category)

    def get_all_timers(self) -> Dict[str, TimeProfile]:
        return self.profiler.get_all_timers()

    def get_list_timers(self) -> List[TimeProfile]:
        return self.profiler.get_timers_list()

    def timers_names(self) -> List[str]:
        return list(self.profiler.get_all_timers().keys())

    def get_update_timing_stats(self) -> Dict[str, Any]:
        return self.profiler.get_timing_stats('update')

    def get_timing(self, category: str) -> Optional[TimeProfile]:
        return self.profiler.get_timer(category)

    def get_render_timing_stats(self) -> Dict[str, Any]:
        return self.profiler.get_timing_stats('render')

    def get_hardware_info(self) -> Dict[str, str]:
        if self._hardware_info is not None and (time.time() - self._hardware_cache_time) < self._cache_duration:
            return self._hardware_info
        info = {}
        try:
            info['system'] = platform.system()
            info['release'] = platform.release()
            info['version'] = platform.version()
            info['machine'] = platform.machine()
            info['processor'] = platform.processor()
            info['python_version'] = platform.python_version()
            info['pygame_version'] = pygame.version.ver
            if HAVE_PSUTIL:
                info['cpu_cores'] = str(psutil.cpu_count(logical=False))
                info['cpu_logical_cores'] = str(psutil.cpu_count(logical=True))
                info['cpu_freq'] = f"{psutil.cpu_freq().max:.2f} MHz"
                mem = psutil.virtual_memory()
                info['memory_total_gb'] = f"{mem.total / (1024**3):.2f} GB"
                info['memory_available_gb'] = f"{mem.available / (1024**3):.2f} GB"
            else:
                info['cpu_cores'] = "N/A (psutil not installed)"
                info['memory_total_gb'] = "N/A"
        except Exception as e:
            info['error'] = str(e)
        self._hardware_info = info
        self._hardware_cache_time = time.time()
        return info

    def update_frame(self):
        current_time = time.perf_counter()
        frame_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        frame_time_ms = frame_time * 1000.0
        self.current_fps = 1000.0 / frame_time_ms if frame_time_ms > 0 else 0.0
        self.frame_times.append(frame_time_ms)
        self.fps_history.append(self.current_fps)
        self.profiler.begin_frame()
        return self.current_fps, frame_time_ms

    def end_frame(self):
        self.profiler.end_frame()

    def get_stats(self) -> Dict[str, float]:
        if not self.fps_history:
            return self._get_empty_stats()
        fps_list = list(self.fps_history)
        frame_times_list = list(self.frame_times)
        avg_fps = sum(fps_list) / len(fps_list) if fps_list else 0.0
        min_fps = min(fps_list) if fps_list else 0.0
        max_fps = max(fps_list) if fps_list else 0.0
        if len(fps_list) > 10:
            sorted_fps = sorted(fps_list)
            idx_1 = max(0, int(len(sorted_fps) * 0.01))
            idx_01 = max(0, int(len(sorted_fps) * 0.001))
            percentile_1 = sorted_fps[idx_1]
            percentile_01 = sorted_fps[idx_01]
        else:
            percentile_1 = min_fps
            percentile_01 = min_fps
        return {
            'current_fps': self.current_fps,
            'average_fps': avg_fps,
            'min_fps': min_fps,
            'max_fps': max_fps,
            'percentile_1': percentile_1,
            'percentile_01': percentile_01,
            'frame_time_ms': frame_times_list[-1] if frame_times_list else 0,
            'frame_count': len(fps_list)
        }
        
    def _getMemUsageClass(self, classM, humanize: bool = True) -> Dict[str, Any]:
        """
        Workaround to access internal usage data of a class instance.
        Used by the UI demo; returns sizes of attributes in bytes (or humanised).
        """
        import sys
        from . import math_utils

        usage_data = {}
        total = 0

        def loop(d):
            if isinstance(d, dict):
                return {key: loop(val) for key, val in d.items()}
            else:
                return math_utils.humanize_size(d) if humanize else d

        for k, v in classM.__dict__.items():
            if type(v) in (list, tuple, set):
                size = sys.getsizeof(v, 0)
                usage_data[k] = size
                total += size
            elif type(v) in (staticmethod, classmethod):
                inner = self._getMemUsageClass(v.__func__, humanize=False)
                usage_data[k] = inner
                total += inner.get('total', 0)
            elif type(v) == dict:
                dsize = {key: sys.getsizeof(val, 0) for key, val in v.items()}
                usage_data[k] = dsize
                total += sum(dsize.values())
            # else ignore (simple types, etc.)

        usage_data['header'] = sys.getsizeof(classM.__dict__, 0)
        usage_data['total'] = total + usage_data['header']

        if humanize:
            for k, v in usage_data.items():
                usage_data[k] = loop(v)

        return usage_data

    def _get_empty_stats(self) -> Dict[str, float]:
        return {
            'current_fps': 0.0,
            'average_fps': 0.0,
            'min_fps': 0.0,
            'max_fps': 0.0,
            'percentile_1': 0.0,
            'percentile_01': 0.0,
            'frame_time_ms': 0.0,
            'frame_count': 0
        }


# ----------------------------------------------------------------------
# GarbageCollector (enhanced to clean renderer caches)
# ----------------------------------------------------------------------

class GarbageCollector:
    def __init__(self, engine=None):
        self.engine = engine
        self.cleanup_interval = 300
        self.frame_count = 0
        self.unused_fonts = set()
        self.unused_surfaces = set()

    def mark_font_unused(self, font):
        self.unused_fonts.add(font)

    def mark_surface_unused(self, surface):
        self.unused_surfaces.add(surface)

    def cleanup(self, force: bool = False):
        self.frame_count += 1
        if not force and self.frame_count % self.cleanup_interval != 0:
            return

        # 1. Python garbage collection
        import gc
        gc.collect()

        # 2. Clean renderer caches (if engine and renderer exist)
        if self.engine and hasattr(self.engine, 'renderer'):
            renderer = self.engine.renderer
            if hasattr(renderer, '_cleanup_texture_cache'):
                renderer._cleanup_texture_cache(force_cleanup=force)
            # Clean text cache if exists
            if hasattr(renderer, '_text_cache'):
                # We could expire old entries, but for simplicity we clear if force
                if force:
                    renderer._text_cache.clear()
                    renderer._text_cache_last_used.clear()
            # Circle and polygon caches
            if hasattr(renderer, '_circle_cache') and force:
                for vao, vbo, ebo, _ in renderer._circle_cache.values():
                    from OpenGL.GL import glDeleteVertexArrays, glDeleteBuffers
                    glDeleteVertexArrays(1, [vao])
                    glDeleteBuffers(1, [vbo])
                    glDeleteBuffers(1, [ebo])
                renderer._circle_cache.clear()
            if hasattr(renderer, '_polygon_cache') and force:
                # Similar cleanup
                pass  # for brevity

        # 3. Clear our tracking sets
        self.unused_fonts.clear()
        self.unused_surfaces.clear()
        self.frame_count = 0