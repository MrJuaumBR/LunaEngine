import threading
import queue
from typing import Callable, Any

class Task:
    def __init__(self, func: Callable, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.exception = None
        
    def execute(self):
        """Execute the task"""
        try:
            self.result = self.func(*self.args, **self.kwargs)
        except Exception as e:
            self.exception = e

class ThreadPool:
    def __init__(self, num_threads: int = 4):
        self.num_threads = num_threads
        self.task_queue = queue.Queue()
        self.threads = []
        self.running = False
        
    def start(self):
        """Start the thread pool"""
        self.running = True
        for _ in range(self.num_threads):
            thread = threading.Thread(target=self._worker)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
            
    def stop(self):
        """Stop the thread pool"""
        self.running = False
        for _ in range(self.num_threads):
            self.task_queue.put(None)
            
        for thread in self.threads:
            thread.join()
            
    def submit(self, task: Task):
        """Submit a task to the thread pool"""
        self.task_queue.put(task)
        
    def _worker(self):
        """Worker thread function"""
        while self.running:
            task = self.task_queue.get()
            if task is None:
                break
                
            task.execute()
            self.task_queue.task_done()