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
        
        # Hardware info cache (won't change during runtime)
        self._hardware_info = None
        self._hardware_cache_time = 0
        self._cache_duration = 30.0  # Refresh hardware info every 30 seconds
        
    def update_frame(self):
        """Update frame timing - optimized version"""
        current_time = time.perf_counter()
        frame_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        # Store frame time in milliseconds
        frame_time_ms = frame_time * 1000.0
        
        # Calculate current FPS
        current_fps = 1000.0 / frame_time_ms if frame_time_ms > 0 else 0
        
        # Add to history
        self.frame_times.append(frame_time_ms)
        self.fps_history.append(current_fps)
        
        return current_fps, frame_time_ms
    
    def get_stats(self) -> Dict[str, float]:
        """Get FPS statistics with optimized calculations"""
        if not self.fps_history:
            return self._get_empty_stats()
        
        current_fps = self.fps_history[-1] if self.fps_history else 0
        
        # Calculate averages using efficient methods
        fps_list = list(self.fps_history)
        frame_times_list = list(self.frame_times)
        
        avg_fps = sum(fps_list) / len(fps_list)
        min_fps = min(fps_list)
        max_fps = max(fps_list)
        
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
            'current': current_fps,
            'average': avg_fps,
            'min': min_fps,
            'max': max_fps,
            'percentile_1': percentile_1,
            'percentile_01': percentile_01,
            'frame_time_ms': frame_times_list[-1] if frame_times_list else 0,
            'frame_count': len(fps_list)
        }
    
    def _get_empty_stats(self) -> Dict[str, float]:
        """Return empty stats structure"""
        return {
            'current': 0.0,
            'average': 0.0,
            'min': 0.0,
            'max': 0.0,
            'percentile_1': 0.0,
            'percentile_01': 0.0,
            'frame_time_ms': 0.0,
            'frame_count': 0
        }
    
    def get_hardware_info(self) -> Dict[str, str]:
        """Get hardware information (cached)"""
        current_time = time.time()
        
        # Return cached info if still valid
        if (self._hardware_info is not None and 
            current_time - self._hardware_cache_time < self._cache_duration):
            return self._hardware_info.copy()
        
        # Gather hardware info
        hardware_info = {}
        
        try:
            # System info
            hardware_info['system'] = platform.system()
            hardware_info['platform'] = platform.platform()
            hardware_info['processor'] = platform.processor()
            
            # CPU info
            if platform.system() == "Windows":
                hardware_info['cpu_cores'] = str(self._get_windows_cpu_cores())
            elif platform.system() == "Linux":
                hardware_info['cpu_cores'] = str(self._get_linux_cpu_cores())
            else:
                hardware_info['cpu_cores'] = "Unknown"
            
            # Memory info
            if platform.system() == "Windows":
                hardware_info['memory_gb'] = self._get_windows_memory()
            elif platform.system() == "Linux":
                hardware_info['memory_gb'] = self._get_linux_memory()
            else:
                hardware_info['memory_gb'] = "Unknown"
                
            # Python info
            hardware_info['python_version'] = platform.python_version()
            hardware_info['pygame_version'] = pygame.version.ver
            
        except Exception as e:
            # Fallback if any hardware detection fails
            hardware_info['error'] = f"Hardware detection failed: {e}"
            hardware_info['system'] = platform.system()
            hardware_info['python_version'] = platform.python_version()
        
        # Cache the results
        self._hardware_info = hardware_info.copy()
        self._hardware_cache_time = current_time
        
        return hardware_info
    
    def _get_windows_cpu_cores(self) -> int:
        """Get CPU cores on Windows"""
        try:
            
            return psutil.cpu_count(logical=False) or 0
        except (ImportError, AttributeError):
            # Fallback without psutil
            
            return int(os.environ.get('NUMBER_OF_PROCESSORS', 1))
    
    def _get_linux_cpu_cores(self) -> int:
        """Get CPU cores on Linux"""
        try:
            
            return psutil.cpu_count(logical=False) or 0
        except (ImportError, AttributeError):
            # Fallback without psutil
            try:
                
                return os.cpu_count() or 1
            except:
                return 1
    
    def _get_windows_memory(self) -> str:
        """Get memory info on Windows"""
        try:
            memory_gb = psutil.virtual_memory().total / (1024**3)
            return f"{memory_gb:.1f} GB"
        except (ImportError, AttributeError):
            return "Unknown"
    
    def _get_linux_memory(self) -> str:
        """Get memory info on Linux"""
        try:
            
            memory_gb = psutil.virtual_memory().total / (1024**3)
            return f"{memory_gb:.1f} GB"
        except (ImportError, AttributeError):
            try:
                # Parse /proc/meminfo as fallback
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            memory_kb = int(line.split()[1])
                            memory_gb = memory_kb / (1024**2)
                            return f"{memory_gb:.1f} GB"
            except:
                pass
            return "Unknown"

class GarbageCollector:
    """Manages cleanup of unused resources"""
    
    def __init__(self):
        self.unused_fonts = set()
        self.unused_surfaces = set()
        self.cleanup_interval = 300  # Cleanup every 300 frames
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