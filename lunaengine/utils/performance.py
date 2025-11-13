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
from typing import Dict, List, Tuple, Optional
from collections import deque

class PerformanceMonitor:
    """Optimized performance monitoring with minimal overhead"""
    
    def __init__(self, history_size: int = 300):
        self.history_size = history_size
        self.frame_times = deque(maxlen=history_size)
        self.fps_history = deque(maxlen=history_size)
        self.last_frame_time = time.perf_counter()
        self.current_fps = 0.0  # ADD THIS LINE - Store current FPS
        
        # Hardware info cache (won't change during runtime)
        self._hardware_info = None
        self._hardware_cache_time = 0
        self._cache_duration = 30.0  # Refresh hardware info every 30 seconds

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