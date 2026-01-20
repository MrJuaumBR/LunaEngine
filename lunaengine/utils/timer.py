"""
Timer system for LunaEngine

LOCATION: lunaengine/utils/timer.py

This module provides a timer management system for the LunaEngine framework.
It allows creating, managing, and triggering timers with callbacks.
"""

import time
from typing import Callable, Optional, Dict, List, Any, Union
from dataclasses import dataclass, field


@dataclass
class TimeCounter:
    """
    Represents a single timer instance.
    
    Attributes:
        name (str): Unique identifier for the timer
        start_time (float): When the timer was started (in seconds since epoch)
        duration (float): How long the timer runs (in seconds)
        callback (Optional[Callable]): Function to call when timer completes
        callback_args (tuple): Arguments to pass to the callback function
        callback_kwargs (dict): Keyword arguments to pass to the callback function
        repeats (bool): Whether the timer should restart after completion
        paused (bool): Whether the timer is currently paused
        paused_time (float): How long the timer has been paused
        destroyed (bool): Whether the timer has been marked for removal
    """
    name: str
    start_time: float
    duration: float
    callback: Optional[Callable] = None
    callback_args: tuple = field(default_factory=tuple)
    callback_kwargs: dict = field(default_factory=dict)
    repeats: bool = False
    paused: bool = False
    paused_time: float = 0.0
    destroyed: bool = False


class Timer:
    """
    Main timer manager for LunaEngine.
    
    Manages multiple timers, updates them, and triggers callbacks.
    Should be updated every frame in the game loop via update() method.
    
    Example:
        >>> timer = Timer()
        >>> timer.add("enemy_spawn", 2.0, spawn_enemy, repeats=True)
        >>> # In game loop:
        >>> while running:
        >>>     timer.update()
    """
    
    def __init__(self) -> None:
        """Initialize a new Timer manager with empty timer dictionary."""
        self.timers: Dict[str, TimeCounter] = {}
        self._last_update_time: float = time.time()
    
    def add(
        self, 
        name: str, 
        duration: float, 
        callback: Optional[Callable] = None, 
        callback_args: tuple = (), 
        callback_kwargs: dict = None,
        repeats: bool = False
    ) -> bool:
        """
        Add a new timer to the system.
        
        Args:
            name (str): Unique identifier for the timer
            duration (float): Timer duration in seconds
            callback (Optional[Callable]): Function to call when timer completes
            callback_args (tuple): Arguments to pass to the callback function
            callback_kwargs (dict): Keyword arguments to pass to the callback function
            repeats (bool): Whether the timer should restart after completion
            
        Returns:
            bool: True if timer was added, False if a timer with this name already exists
            
        Example:
            >>> timer.add("powerup", 10.0, remove_powerup, repeats=False)
        """
        if name in self.timers:
            return False
        
        if callback_kwargs is None:
            callback_kwargs = {}
            
        self.timers[name] = TimeCounter(
            name=name,
            start_time=time.time(),
            duration=duration,
            callback=callback,
            callback_args=callback_args,
            callback_kwargs=callback_kwargs,
            repeats=repeats
        )
        return True
    
    def add_timer_to(
        self,
        duration: float,
        callback: Callable,
        callback_args: tuple = (),
        callback_kwargs: dict = None,
        repeats: bool = False
    ) -> str:
        """
        Add a timer with an auto-generated name and return its name.
        
        Args:
            duration (float): Timer duration in seconds
            callback (Callable): Function to call when timer completes
            callback_args (tuple): Arguments to pass to the callback function
            callback_kwargs (dict): Keyword arguments to pass to the callback function
            repeats (bool): Whether the timer should restart after completion
            
        Returns:
            str: The auto-generated name of the timer
            
        Example:
            >>> timer_id = timer.add_timer_to(5.0, lambda: print("5 seconds passed"))
        """
        if callback_kwargs is None:
            callback_kwargs = {}
            
        name = f"timer_{int(time.time() * 1000)}_{len(self.timers)}"
        self.add(name, duration, callback, callback_args, callback_kwargs, repeats)
        return name
    
    def remove(self, name: str) -> bool:
        """
        Remove a timer from the system.
        
        Args:
            name (str): Name of the timer to remove
            
        Returns:
            bool: True if timer was removed, False if timer didn't exist
        """
        if name in self.timers:
            del self.timers[name]
            return True
        return False
    
    def destroy(self, name: str) -> bool:
        """
        Mark a timer for destruction (will be removed on next update).
        
        Args:
            name (str): Name of the timer to destroy
            
        Returns:
            bool: True if timer was marked for destruction, False if timer didn't exist
        """
        if name in self.timers:
            self.timers[name].destroyed = True
            return True
        return False
    
    def pause(self, name: str) -> bool:
        """
        Pause a running timer.
        
        Args:
            name (str): Name of the timer to pause
            
        Returns:
            bool: True if timer was paused, False if timer didn't exist or was already paused
        """
        if name in self.timers and not self.timers[name].paused:
            self.timers[name].paused = True
            self.timers[name].paused_time = time.time()
            return True
        return False
    
    def resume(self, name: str) -> bool:
        """
        Resume a paused timer.
        
        Args:
            name (str): Name of the timer to resume
            
        Returns:
            bool: True if timer was resumed, False if timer didn't exist or wasn't paused
        """
        if name in self.timers and self.timers[name].paused:
            self.timers[name].paused = False
            # Adjust start_time to account for pause duration
            pause_duration = time.time() - self.timers[name].paused_time
            self.timers[name].start_time += pause_duration
            self.timers[name].paused_time = 0.0
            return True
        return False
    
    def reset(self, name: str) -> bool:
        """
        Reset a timer to start counting from now.
        
        Args:
            name (str): Name of the timer to reset
            
        Returns:
            bool: True if timer was reset, False if timer didn't exist
        """
        if name in self.timers:
            self.timers[name].start_time = time.time()
            self.timers[name].paused = False
            self.timers[name].paused_time = 0.0
            return True
        return False
    
    def get_elapsed(self, name: str) -> Optional[float]:
        """
        Get elapsed time for a timer.
        
        Args:
            name (str): Name of the timer
            
        Returns:
            Optional[float]: Elapsed time in seconds, or None if timer doesn't exist
        """
        if name not in self.timers:
            return None
            
        timer = self.timers[name]
        if timer.paused:
            return timer.paused_time - timer.start_time
        return time.time() - timer.start_time
    
    def get_remaining(self, name: str) -> Optional[float]:
        """
        Get remaining time for a timer.
        
        Args:
            name (str): Name of the timer
            
        Returns:
            Optional[float]: Remaining time in seconds, or None if timer doesn't exist
        """
        if name not in self.timers:
            return None
            
        timer = self.timers[name]
        if timer.paused:
            elapsed = timer.paused_time - timer.start_time
        else:
            elapsed = time.time() - timer.start_time
            
        remaining = timer.duration - elapsed
        return max(0.0, remaining)
    
    def is_done(self, name: str) -> Optional[bool]:
        """
        Check if a timer has completed.
        
        Args:
            name (str): Name of the timer
            
        Returns:
            Optional[bool]: True if timer is done, False if still running, None if timer doesn't exist
        """
        remaining = self.get_remaining(name)
        if remaining is None:
            return None
        return remaining <= 0
    
    def exists(self, name: str) -> bool:
        """
        Check if a timer exists.
        
        Args:
            name (str): Name of the timer
            
        Returns:
            bool: True if timer exists
        """
        return name in self.timers
    
    def is_paused(self, name: str) -> Optional[bool]:
        """
        Check if a timer is paused.
        
        Args:
            name (str): Name of the timer
            
        Returns:
            Optional[bool]: True if timer is paused, False if running, None if timer doesn't exist
        """
        if name in self.timers:
            return self.timers[name].paused
        return None
    
    def clear(self) -> None:
        """Remove all timers from the system."""
        self.timers.clear()
    
    def update(self) -> List[str]:
        """
        Update all timers. Should be called every frame in the game loop.
        
        Checks all timers for completion, triggers callbacks, and removes destroyed timers.
        
        Returns:
            List[str]: Names of timers that completed during this update
            
        Example:
            >>> completed_timers = timer.update()
            >>> for timer_name in completed_timers:
            >>>     print(f"Timer {timer_name} completed!")
        """
        current_time = time.time()
        dt = current_time - self._last_update_time
        self._last_update_time = current_time
        
        completed = []
        timers_to_remove = []
        
        for name, timer in list(self.timers.items()):
            # Skip destroyed timers
            if timer.destroyed:
                timers_to_remove.append(name)
                continue
                
            # Skip paused timers
            if timer.paused:
                continue
            
            # Check if timer is done
            elapsed = current_time - timer.start_time
            if elapsed >= timer.duration:
                completed.append(name)
                
                # Trigger callback if exists
                if timer.callback is not None:
                    try:
                        timer.callback(*timer.callback_args, **timer.callback_kwargs)
                    except Exception as e:
                        print(f"Error in timer callback for '{name}': {e}")
                
                # Handle repeating timers
                if timer.repeats:
                    timer.start_time = current_time
                else:
                    timers_to_remove.append(name)
        
        # Remove destroyed and completed non-repeating timers
        for name in timers_to_remove:
            if name in self.timers:
                del self.timers[name]
        
        return completed
    
    def wait_for_end(self, name: str, timeout: float = 0.0) -> bool:
        """
        Block until a timer completes.
        
        Warning: This blocks the main thread! Use sparingly.
        
        Args:
            name (str): Name of the timer to wait for
            timeout (float): Maximum time to wait in seconds (0 = no timeout)
            
        Returns:
            bool: True if timer completed, False if timeout reached or timer doesn't exist
            
        Example:
            >>> timer.add("wait_test", 3.0)
            >>> timer.wait_for_end("wait_test")  # Blocks for 3 seconds
        """
        if name not in self.timers:
            return False
        
        start_wait = time.time()
        while not self.is_done(name):
            if timeout > 0 and (time.time() - start_wait) > timeout:
                return False
            time.sleep(0.001)  # Small sleep to prevent CPU hogging
            self.update()
        
        return True
    
    def get_all_timers(self) -> List[str]:
        """
        Get names of all active timers.
        
        Returns:
            List[str]: List of timer names
        """
        return list(self.timers.keys())
    
    def get_timer_count(self) -> int:
        """
        Get the number of active timers.
        
        Returns:
            int: Number of timers
        """
        return len(self.timers)


# Convenience function for creating a global timer instance
_singleton_timer: Optional[Timer] = None

def get_global_timer() -> Timer:
    """
    Get or create the global singleton timer instance.
    
    Returns:
        Timer: Global timer instance
        
    Example:
        >>> from lunaengine.utils.timer import get_global_timer
        >>> timer = get_global_timer()
        >>> timer.add("global_timer", 1.0, lambda: print("Global timer fired!"))
    """
    global _singleton_timer
    if _singleton_timer is None:
        _singleton_timer = Timer()
    return _singleton_timer