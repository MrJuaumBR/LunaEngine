# performance

## Overview

*File: `lunaengine\utils\performance.py`*
*Lines: 221*

## Classes

### GarbageCollector

Manages cleanup of unused resources

*Line: 187*

#### Methods

##### Method `mark_surface_unused`

Mark a surface as potentially unused

*Line: 200*

##### Method `mark_font_unused`

Mark a font as potentially unused

*Line: 196*

##### Method `__init__`

Private method.

*Line: 190*

##### Method `cleanup`

Clean up unused resources

*Line: 204*

---

### PerformanceMonitor

Optimized performance monitoring with minimal overhead

*Line: 5*

#### Methods

##### Method `_get_windows_cpu_cores`

Get CPU cores on Windows

*Line: 137*

##### Method `_get_empty_stats`

Return empty stats structure

*Line: 74*

##### Method `update_frame`

Update frame timing - optimized version

*Line: 19*

##### Method `get_hardware_info`

Get hardware information (cached)

*Line: 87*

##### Method `get_stats`

Get FPS statistics with optimized calculations

*Line: 37*

##### Method `__init__`

Private method.

*Line: 8*

##### Method `_get_windows_memory`

Get memory info on Windows

*Line: 160*

##### Method `_get_linux_memory`

Get memory info on Linux

*Line: 168*

##### Method `_get_linux_cpu_cores`

Get CPU cores on Linux

*Line: 147*

---

## Functions

### Function `_get_windows_memory`

Get memory info on Windows

*Line: 160*

### Function `__init__`

Private method.

*Line: 190*

### Function `_get_linux_cpu_cores`

Get CPU cores on Linux

*Line: 147*

### Function `_get_windows_cpu_cores`

Get CPU cores on Windows

*Line: 137*

### Function `__init__`

Private method.

*Line: 8*

### Function `update_frame`

Update frame timing - optimized version

*Line: 19*

### Function `_get_empty_stats`

Return empty stats structure

*Line: 74*

### Function `cleanup`

Clean up unused resources

*Line: 204*

### Function `mark_font_unused`

Mark a font as potentially unused

*Line: 196*

### Function `_get_linux_memory`

Get memory info on Linux

*Line: 168*

### Function `get_stats`

Get FPS statistics with optimized calculations

*Line: 37*

### Function `get_hardware_info`

Get hardware information (cached)

*Line: 87*

### Function `mark_surface_unused`

Mark a surface as potentially unused

*Line: 200*

