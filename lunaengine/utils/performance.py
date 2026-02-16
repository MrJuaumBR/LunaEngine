"""
Performance Monitoring - System Optimization and Resource Management

LOCATION: lunaengine/utils/performance.py

DESCRIPTION:
Comprehensive performance monitoring system that tracks frame rates,
system resources, and provides optimization utilities. Includes hardware
detection, garbage collection, and performance statistics.

KEY COMPONENTS:
- PerformanceMonitor: Real-time FPS tracking and hardware monitoring
- GarbageCollector: Automatic resource cleanup and memory management
- Hardware detection for system-specific optimizations
- Frame time analysis and performance statistics

LIBRARIES USED:
- psutil: System resource monitoring (CPU, memory)
- pygame: Version detection and integration
- platform: System information and platform detection
- time: Precise timing measurements
- threading: Background monitoring capabilities
- collections: Efficient data structures for performance tracking

USAGE:
>>> monitor = PerformanceMonitor()
>>> stats = monitor.get_stats()
>>> hardware = monitor.get_hardware_info()
>>> gc = GarbageCollector()
>>> gc.cleanup()
"""
import sys, psutil, subprocess, platform, time, pygame, threading, os
from typing import Dict, List, Tuple, Optional, Any, Literal
from collections import deque
from dataclasses import dataclass
from enum import Enum

class TimeProfile:
    def __init__(self, category: str = "", max_history: int = 60):
        self.category = category
        self.start_time = 0.0
        self.end_time = 0.0
        self.history = deque(maxlen=max_history)   # store per-frame durations
        self._used_this_frame = False

    def start(self):
        self.start_time = time.perf_counter()
        self._used_this_frame = True

    def stop(self):
        self.end_time = time.perf_counter()
        self._used_this_frame = False   # will be recorded at end_frame
        self._insert_new_history()
        
    def _insert_new_history(self):
        if len(self.history) >= self.history.maxlen:
            del self.history[0]
        self.history.append((self.end_time - self.start_time) * 1000.0)        
        
    end = stop

    @property
    def duration(self) -> float:
        # Return last recorded duration from history (safe for display)
        return self.history[-1] if self.history else 0.0

    def record_current(self):
        """Record the current duration into history."""
        if self.start_time > 0 and self.end_time > 0 and self.end_time > self.start_time:
            self.history.append((self.end_time - self.start_time) * 1000.0)
        # Reset for next frame
        self.start_time = 0.0
        self.end_time = 0.0
        self._used_this_frame = False
        
class PerformanceProfiler:
    """Performance profiling with detailed timing breakdown"""
    
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
        """Begin a new frame of profiling"""
        if not self._enabled:
            return
    
    def end_frame(self):
        """End current frame: record all used timers and store durations."""
        if not self._enabled:
            return
        self._last_frame_timings.clear()
        for cat, timer in self.timers.items():
            if timer._used_this_frame:
                timer.record_current()
            # Always provide a value (use last known duration if available)
            self._last_frame_timings[cat] = timer.duration
            
    def get_frame_timings(self) -> Dict[str, float]:
        """Get durations (ms) of the last completed frame."""
        return self._last_frame_timings.copy()

        
    def get_timing_stats(self, category: Literal["update", "render"]) -> Dict[str, Any]:
        stats = {}
        for timer in self.timers.values():
            if timer.category.startswith(category):
                stats[timer.category] = {
                    "start_time": timer.start_time,
                    "end_time": timer.end_time,
                    "duration": timer.duration
                }
        return stats

class PerformanceMonitor:
    """Optimized performance monitoring with minimal overhead"""
    
    def __init__(self, history_size: int = 300):
        self.history_size = history_size
        self.frame_times = deque(maxlen=history_size)
        self.fps_history = deque(maxlen=history_size)
        self.last_frame_time = time.perf_counter()
        self.current_fps = 0.0
        
        # Performance profiler
        self.profiler = PerformanceProfiler(max_history=100)
        
        # Hardware info cache
        self._hardware_info = None
        self._hardware_cache_time = 0
        self._cache_duration = 30.0

    def get_frame_timing_breakdown(self) -> Dict[str, float]:
        """Convenience: get last frame's timing per category."""
        return self.profiler.get_frame_timings()

    def get_performance_summary(self) -> Dict[str, Any]:
        """Comprehensive summary including FPS and last frame timings."""
        return {
            "fps": self.get_stats(),
            "frame_timings": self.get_frame_timing_breakdown(),
            "hardware": self.get_hardware_info(),
            "profiling_enabled": self.is_profiling_enabled()
        }

    def enable_profiling(self, enabled: bool = True):
        """Enable or disable detailed performance profiling"""
        if enabled:
            self.profiler.enable()
        else:
            self.profiler.disable()
    
    def is_profiling_enabled(self) -> bool:
        """Check if detailed profiling is enabled"""
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
        """Get update timing statistics"""
        return self.profiler.get_timing_stats('update')
    
    def get_render_timing_stats(self) -> Dict[str, Any]:
        """Get render timing statistics"""
        return self.profiler.get_timing_stats('render')
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            "fps": self.get_stats(),
            "update_times": self.get_update_timing_stats(),
            "render_times": self.get_render_timing_stats(),
            "hardware": self.get_hardware_info(),
            "profiling_enabled": self.is_profiling_enabled()
        }

    def get_hardware_info(self) -> Dict[str, str]:
        """Get system hardware information with caching"""
        current_time = time.time()
        if (self._hardware_info is not None and 
            (current_time - self._hardware_cache_time) < self._cache_duration):
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
            
            # CPU Info
            info['cpu_cores'] = str(psutil.cpu_count(logical=False))
            info['cpu_logical_cores'] = str(psutil.cpu_count(logical=True))
            info['cpu_freq'] = f"{psutil.cpu_freq().max:.2f} MHz"
            
            # Memory Info
            mem = psutil.virtual_memory()
            info['memory_total_gb'] = f"{mem.total / (1024**3):.2f} GB"
            info['memory_available_gb'] = f"{mem.available / (1024**3):.2f} GB"
            
        except Exception as e:
            info['error'] = str(e)
        
        self._hardware_info = info
        self._hardware_cache_time = current_time
        return info
        
    def update_frame(self):
        """Update frame timing - FIXED VERSION"""
        # Begin profiling for new frame
        self.profiler.begin_frame()
        
        current_time = time.perf_counter()
        frame_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        # Store frame time in milliseconds
        frame_time_ms = frame_time * 1000.0
        
        # Calculate current FPS - FIXED: Handle division by zero
        if frame_time_ms > 0:
            self.current_fps = 1000.0 / frame_time_ms
        else:
            self.current_fps = 0.0
        
        # Add to history
        self.frame_times.append(frame_time_ms)
        self.fps_history.append(self.current_fps)
        
        return self.current_fps, frame_time_ms
    
    def end_frame(self):
        """End the current frame and record profiling data"""
        self.profiler.end_frame()
    
    def get_stats(self) -> Dict[str, float]:
        """Get FPS statistics with optimized calculations - FIXED"""
        if not self.fps_history:
            return self._get_empty_stats()
        
        # Use the stored current_fps instead of history
        current_fps = self.current_fps
        
        # Calculate averages using efficient methods
        fps_list = list(self.fps_history)
        frame_times_list = list(self.frame_times)
        
        avg_fps = sum(fps_list) / len(fps_list) if fps_list else 0.0
        min_fps = min(fps_list) if fps_list else 0.0
        max_fps = max(fps_list) if fps_list else 0.0
        
        # Calculate percentiles efficiently
        if len(fps_list) > 10:  # Only calculate percentiles with sufficient data
            sorted_fps = sorted(fps_list)
            idx_1 = max(0, int(len(sorted_fps) * 0.01))
            idx_01 = max(0, int(len(sorted_fps) * 0.001))
            percentile_1 = sorted_fps[idx_1]
            percentile_01 = sorted_fps[idx_01]
        else:
            percentile_1 = min_fps
            percentile_01 = min_fps
        
        return {
            'current_fps': current_fps,  # FIXED: Changed from 'current' to 'current_fps'
            'average_fps': avg_fps,      # FIXED: Changed from 'average' to 'average_fps'
            'min_fps': min_fps,          # FIXED: Changed from 'min' to 'min_fps'
            'max_fps': max_fps,          # FIXED: Changed from 'max' to 'max_fps'
            'percentile_1': percentile_1,
            'percentile_01': percentile_01,
            'frame_time_ms': frame_times_list[-1] if frame_times_list else 0,
            'frame_count': len(fps_list)
        }
    
    def _get_empty_stats(self) -> Dict[str, float]:
        """Return empty stats structure - FIXED"""
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

class GarbageCollector:
    """Manages cleanup of unused resources"""
    
    def __init__(self):
        self.unused_fonts = set()
        self.unused_surfaces = set()
        self.cleanup_interval = 300
        self.frame_count = 0
        
    def mark_font_unused(self, font):
        """Mark a font as potentially unused"""
        self.unused_fonts.add(font)
        
    def mark_surface_unused(self, surface):
        """Mark a surface as potentially unused"""
        self.unused_surfaces.add(surface)
        
    def cleanup(self, force: bool = False):
        """Clean up unused resources"""
        self.frame_count += 1
        
        # Only cleanup periodically unless forced
        if not force and self.frame_count % self.cleanup_interval != 0:
            return
        
        # Clean fonts (Pygame fonts don't need explicit cleanup in most cases)
        # But we can clear our tracking sets
        self.unused_fonts.clear()
        self.unused_surfaces.clear()
        
        # Optional: Force Python garbage collection
        import gc
        gc.collect()
        
        self.frame_count = 0