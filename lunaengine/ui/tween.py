"""
tween.py - Tween Animation System for LunaEngine (Inspired by Roblox Studio)

ENGINE PATH:
lunaengine -> ui -> tween.py

DESCRIPTION:
A comprehensive tween animation system inspired by Roblox Studio, providing
smooth property animations with various easing functions, sequencing, 
and lifecycle management.

FEATURES:
- 25+ easing types (Linear, Quadratic, Cubic, Elastic, Bounce, etc.)
- Property animations: position, size, rotation, opacity, colors, custom properties
- Lifecycle callbacks: on_start, on_update, on_complete, on_loop
- Animation control: play, pause, resume, cancel, stop
- Sequencing: parallel and sequential animation groups
- Looping: finite loops, infinite loops, yoyo effect
- Progress tracking: get current animation progress percentage
- Global management: AnimationHandler for engine-wide animation control

USAGE EXAMPLES:
# Simple animation
tween = Tween.create(button)
tween.to(x=100, y=200, duration=1.0, easing=EasingType.QUAD_IN_OUT)
tween.play()

# Sequence of animations
sequence = Tween.sequence([
    Tween.create(element).to(x=100, duration=0.5),
    Tween.create(element).to(y=200, duration=0.5),
])

# Animation with callbacks and loops
tween = Tween.create(element)
tween.to(rotation=360, duration=2.0, easing=EasingType.ELASTIC_OUT)
tween.set_loops(3, yoyo=True)
tween.set_callbacks(
    on_start=lambda: print("Animation started"),
    on_complete=lambda: print("Animation completed")
)
tween.play()
"""

import pygame as pg
import math
import time
from typing import Dict, List, Tuple, Optional, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass

class EasingType(Enum):
    """Easing function types inspired by Roblox Studio."""
    
    # Linear
    LINEAR = "Linear"
    
    # Quadratic
    QUAD_IN = "QuadIn"
    QUAD_OUT = "QuadOut"
    QUAD_IN_OUT = "QuadInOut"
    
    # Cubic
    CUBIC_IN = "CubicIn"
    CUBIC_OUT = "CubicOut"
    CUBIC_IN_OUT = "CubicInOut"
    
    # Quartic
    QUART_IN = "QuartIn"
    QUART_OUT = "QuartOut"
    QUART_IN_OUT = "QuartInOut"
    
    # Quintic
    QUINT_IN = "QuintIn"
    QUINT_OUT = "QuintOut"
    QUINT_IN_OUT = "QuintInOut"
    
    # Sine
    SINE_IN = "SineIn"
    SINE_OUT = "SineOut"
    SINE_IN_OUT = "SineInOut"
    
    # Exponential
    EXPO_IN = "ExpoIn"
    EXPO_OUT = "ExpoOut"
    EXPO_IN_OUT = "ExpoInOut"
    
    # Circular
    CIRC_IN = "CircIn"
    CIRC_OUT = "CircOut"
    CIRC_IN_OUT = "CircInOut"
    
    # Elastic
    ELASTIC_IN = "ElasticIn"
    ELASTIC_OUT = "ElasticOut"
    ELASTIC_IN_OUT = "ElasticInOut"
    
    # Back
    BACK_IN = "BackIn"
    BACK_OUT = "BackOut"
    BACK_IN_OUT = "BackInOut"
    
    # Bounce
    BOUNCE_IN = "BounceIn"
    BOUNCE_OUT = "BounceOut"
    BOUNCE_IN_OUT = "BounceInOut"

@dataclass
class TweenProperty:
    """Represents a property to be animated with its start and end values."""
    
    start: Any
    end: Any
    original_start: Any
    original_end: Any

class Tween:
    """
    Main tween class for animating object properties.
    
    Provides Roblox Studio-like API for creating and controlling animations.
    """
    
    # Static cache of all active tweens for global management
    _active_tweens: List['Tween'] = []
    
    def __init__(self, target: Any):
        """
        Initialize a new tween animation.
        
        Args:
            target: The object to animate (UIElement or any object with properties)
        """
        self.target = target
        self.properties: Dict[str, TweenProperty] = {}
        self.duration: float = 0.0
        self.start_time: Optional[float] = None
        self.easing: EasingType = EasingType.LINEAR
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.loops: int = 0          # 0 = no loop, -1 = infinite loop, n = n loops
        self.current_loop: int = 0
        self.yoyo: bool = False      # Reverse animation on each loop
        self.yoyo_forward: bool = True  # Current yoyo direction
        self.is_completed: bool = False
        
        # Lifecycle callbacks
        self.on_start: Optional[Callable] = None
        self.on_update: Optional[Callable[['Tween', float], None]] = None
        self.on_complete: Optional[Callable] = None
        self.on_loop: Optional[Callable[[int], None]] = None
        self.on_stop: Optional[Callable] = None
        
        # Internal state
        self._elapsed_before_pause: float = 0.0
        self._last_update_time: float = 0.0
    
    @classmethod
    def create(cls, target: Any) -> 'Tween':
        """
        Factory method to create a new tween (Roblox Studio style).
        
        Args:
            target: Object to animate
            
        Returns:
            Tween: New tween instance
        """
        return cls(target)
    
    def to(self, **kwargs) -> 'Tween':
        """
        Set target values for the animation (Roblox Studio style).
        
        Args:
            **kwargs: Properties to animate with their target values
                     Special parameters: duration, easing
                     Example: x=100, y=200, duration=1.0, easing=EasingType.QUAD_IN_OUT
            
        Returns:
            Tween: Self for method chaining
        """
        # Extract special parameters
        self.duration = kwargs.pop('duration', 1.0)
        easing_str = kwargs.pop('easing', 'Linear')
        
        # Convert string to EasingType if needed
        if isinstance(easing_str, str):
            try:
                self.easing = EasingType[easing_str.upper()]
            except KeyError:
                self.easing = EasingType.LINEAR
        else:
            self.easing = easing_str
        
        # Setup properties to animate
        for prop_name, end_value in kwargs.items():
            # Get initial value from target
            start_value = getattr(self.target, prop_name, None)
            if start_value is not None:
                self.properties[prop_name] = TweenProperty(
                    start=start_value,
                    end=end_value,
                    original_start=start_value,
                    original_end=end_value
                )
        
        return self
    
    def set_delay(self, delay: float) -> 'Tween':
        """
        Add a delay to the animation.
        
        Args:
            delay: Delay in seconds
            
        Returns:
            Tween: Self for method chaining
        """
        self.duration += delay
        return self
    
    def play(self) -> 'Tween':
        """
        Start playing the animation.
        
        Returns:
            Tween: Self for method chaining
        """
        if not self.is_playing:
            self.start_time = time.time() - self._elapsed_before_pause
            self._last_update_time = self.start_time
            self.is_playing = True
            self.is_paused = False
            self.is_completed = False
            
            # Reset loops for restart
            if self._elapsed_before_pause == 0:
                self.current_loop = 0
                self.yoyo_forward = True
                
                # Reset properties to original values if starting fresh
                for prop_name, prop in self.properties.items():
                    prop.start = prop.original_start
                    prop.end = prop.original_end
            
            # Add to active tweens list
            if self not in Tween._active_tweens:
                Tween._active_tweens.append(self)
            
            # Fire start callback
            if self.on_start:
                self.on_start()
        
        return self
    
    def pause(self) -> 'Tween':
        """
        Pause the animation.
        
        Returns:
            Tween: Self for method chaining
        """
        if self.is_playing and not self.is_paused:
            self._elapsed_before_pause = self._get_elapsed_time()
            self.is_paused = True
        
        return self
    
    def resume(self) -> 'Tween':
        """
        Resume a paused animation.
        
        Returns:
            Tween: Self for method chaining
        """
        if self.is_playing and self.is_paused:
            self.is_paused = False
        
        return self
    
    def cancel(self) -> 'Tween':
        """
        Cancel the animation and reset properties to initial state.
        
        Returns:
            Tween: Self for method chaining
        """
        return self.stop(reset=True)
    
    def stop(self, reset: bool = False) -> 'Tween':
        """
        Stop the animation.
        
        Args:
            reset: If True, reset properties to initial values
            
        Returns:
            Tween: Self for method chaining
        """
        was_playing = self.is_playing
        
        self.is_playing = False
        self.is_paused = False
        self.is_completed = True
        
        # Remove from active tweens list
        if self in Tween._active_tweens:
            Tween._active_tweens.remove(self)
        
        # Reset properties if requested
        if reset:
            for prop_name, prop in self.properties.items():
                setattr(self.target, prop_name, prop.original_start)
        
        # Fire stop callback
        if was_playing and self.on_stop:
            self.on_stop()
        
        return self
    
    def set_duration(self, duration: float) -> 'Tween':
        """
        Change the duration of the animation.
        
        Args:
            duration: New duration in seconds (must be positive)
            
        Returns:
            Tween: Self for method chaining
            
        Raises:
            ValueError: If duration is not positive
        """
        if duration <= 0:
            raise ValueError("Duration must be positive")
        
        # Update the duration
        old_duration = self.duration
        self.duration = duration
        
        # If animation is playing, adjust timing to maintain progress
        if self.is_playing and not self.is_paused:
            if old_duration > 0:
                # Calculate current progress
                elapsed = self._get_elapsed_time()
                progress = min(max(elapsed / old_duration, 0.0), 1.0)
                
                # Calculate new elapsed time to maintain same progress
                new_elapsed = progress * duration
                
                # Adjust start time
                if self.start_time:
                    self.start_time = time.time() - new_elapsed
                self._elapsed_before_pause = 0.0
            else:
                # If old duration was 0, restart animation
                self.start_time = time.time()
                self._elapsed_before_pause = 0.0
        
        return self
    
    def _get_elapsed_time(self) -> float:
        """
        Get elapsed time since animation started.
        
        Returns:
            float: Elapsed time in seconds
        """
        if not self.start_time or not self.is_playing:
            return self._elapsed_before_pause
        
        if self.is_paused:
            return self._elapsed_before_pause
        
        return time.time() - self.start_time
    
    def get_progress(self) -> float:
        """
        Get current animation progress as a percentage (0.0 to 1.0).
        
        Returns:
            float: Animation progress (0.0 = start, 1.0 = end)
        """
        if not self.is_playing or self.duration == 0:
            return 0.0
        
        elapsed = self._get_elapsed_time()
        
        # Calculate raw progress within current iteration
        iteration_duration = self.duration
        iteration_elapsed = elapsed % iteration_duration
        raw_progress = min(max(iteration_elapsed / iteration_duration, 0.0), 1.0)
        
        # For yoyo animations, adjust progress based on direction
        if self.yoyo:
            # Determine which half of the loop we're in
            loop_number = int(elapsed / iteration_duration)
            
            # If loop number is odd (1, 3, 5...), we're going backward
            if loop_number % 2 == 1:
                # Reverse direction for yoyo
                raw_progress = 1.0 - raw_progress
        
        return raw_progress
    
    def get_progress_percentage(self) -> float:
        """
        Get current animation progress as a percentage (0 to 100).
        
        Returns:
            float: Animation progress percentage (0 to 100)
        """
        return self.get_progress() * 100
    
    def update(self, dt: Optional[float] = None) -> bool:
        """
        Update the animation state.
        
        Args:
            dt: Delta time in seconds (optional, uses real time if None)
            
        Returns:
            bool: True if animation is complete, False otherwise
        """
        if not self.is_playing or self.is_paused or self.is_completed:
            return False
        
        # Get current time
        current_time = time.time()
        
        # Calculate elapsed time since start
        elapsed = current_time - self.start_time if self.start_time else 0
        
        # Calculate total iterations (including yoyo halves)
        iteration_duration = self.duration
        total_iterations = 2 * abs(self.loops) if self.yoyo and self.loops != 0 else abs(self.loops)
        
        # Check if animation should be complete
        if self.loops != -1:  # Not infinite
            if self.yoyo:
                # For yoyo, each loop counts as 2 iterations (forward + backward)
                max_time = total_iterations * iteration_duration
                if elapsed >= max_time:
                    self._complete_animation()
                    return True
            else:
                # For non-yoyo, simple duration check
                max_time = self.loops * iteration_duration
                if elapsed >= max_time:
                    self._complete_animation()
                    return True
        
        # Calculate progress for current iteration
        iteration_elapsed = elapsed % iteration_duration if iteration_duration > 0 else 0
        raw_progress = min(max(iteration_elapsed / iteration_duration, 0.0), 1.0)
        
        # For yoyo animations, determine direction
        if self.yoyo:
            # Calculate which half of yoyo we're in
            half_iteration = int(elapsed / iteration_duration)
            
            # Update yoyo direction
            self.yoyo_forward = (half_iteration % 2 == 0)
            
            # Reverse progress for backward motion
            if not self.yoyo_forward:
                raw_progress = 1.0 - raw_progress
        
        # Apply easing function
        eased_progress = self._apply_easing(raw_progress)
        
        # Update all animated properties
        for prop_name, prop in self.properties.items():
            self._update_property(prop_name, prop, eased_progress)
        
        # Update loop counter
        current_iteration = int(elapsed / iteration_duration) if iteration_duration > 0 else 0
        if current_iteration != self.current_loop:
            self.current_loop = current_iteration
            # Fire loop callback for non-yoyo or for each yoyo cycle
            if self.on_loop and (not self.yoyo or current_iteration % 2 == 0):
                self.on_loop(current_iteration // (2 if self.yoyo else 1))
        
        # Fire update callback
        if self.on_update:
            self.on_update(self, eased_progress)
        
        self._last_update_time = current_time
        return False
    
    def _update_property(self, prop_name: str, prop: TweenProperty, progress: float):
        """
        Update a specific property based on animation progress.
        
        Args:
            prop_name: Name of the property
            prop: TweenProperty object
            progress: Eased animation progress (0.0 to 1.0)
        """
        # Handle numeric properties
        if isinstance(prop.start, (int, float)) and isinstance(prop.end, (int, float)):
            value = prop.start + (prop.end - prop.start) * progress
            setattr(self.target, prop_name, value)
        
        # Handle tuple properties (positions, colors, etc.)
        elif isinstance(prop.start, tuple) and isinstance(prop.end, tuple):
            if len(prop.start) == len(prop.end):
                value = tuple(
                    start + (end - start) * progress
                    for start, end in zip(prop.start, prop.end)
                )
                setattr(self.target, prop_name, value)
        
        # Handle list properties
        elif isinstance(prop.start, list) and isinstance(prop.end, list):
            if len(prop.start) == len(prop.end):
                value = [
                    start + (end - start) * progress
                    for start, end in zip(prop.start, prop.end)
                ]
                setattr(self.target, prop_name, value)
    
    def _complete_animation(self):
        """Mark animation as complete and fire callbacks."""
        self.is_playing = False
        self.is_completed = True
        
        # Set final values
        final_progress = 1.0 if self.yoyo_forward else 0.0
        for prop_name, prop in self.properties.items():
            self._update_property(prop_name, prop, final_progress)
        
        # Fire completion callback
        if self.on_complete:
            self.on_complete()
        
        # Remove from active tweens
        if self in Tween._active_tweens:
            Tween._active_tweens.remove(self)
    
    def _apply_easing(self, t: float) -> float:
        """
        Apply easing function to raw progress.
        
        Args:
            t: Raw progress (0.0 to 1.0)
            
        Returns:
            float: Eased progress
        """
        if self.easing == EasingType.LINEAR:
            return t
        
        # Quadratic easing
        elif self.easing == EasingType.QUAD_IN:
            return t * t
        elif self.easing == EasingType.QUAD_OUT:
            return t * (2 - t)
        elif self.easing == EasingType.QUAD_IN_OUT:
            return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t
        
        # Cubic easing
        elif self.easing == EasingType.CUBIC_IN:
            return t * t * t
        elif self.easing == EasingType.CUBIC_OUT:
            t -= 1
            return t * t * t + 1
        elif self.easing == EasingType.CUBIC_IN_OUT:
            if t < 0.5:
                return 4 * t * t * t
            t -= 1
            return 4 * t * t * t + 1
        
        # Quartic easing
        elif self.easing == EasingType.QUART_IN:
            return t * t * t * t
        elif self.easing == EasingType.QUART_OUT:
            t -= 1
            return 1 - t * t * t * t
        elif self.easing == EasingType.QUART_IN_OUT:
            if t < 0.5:
                return 8 * t * t * t * t
            t -= 1
            return 1 - 8 * t * t * t * t
        
        # Quintic easing
        elif self.easing == EasingType.QUINT_IN:
            return t * t * t * t * t
        elif self.easing == EasingType.QUINT_OUT:
            t -= 1
            return 1 + t * t * t * t * t
        elif self.easing == EasingType.QUINT_IN_OUT:
            if t < 0.5:
                return 16 * t * t * t * t * t
            t -= 1
            return 1 + 16 * t * t * t * t * t
        
        # Sine easing
        elif self.easing == EasingType.SINE_IN:
            return 1 - math.cos((t * math.pi) / 2)
        elif self.easing == EasingType.SINE_OUT:
            return math.sin((t * math.pi) / 2)
        elif self.easing == EasingType.SINE_IN_OUT:
            return -(math.cos(math.pi * t) - 1) / 2
        
        # Exponential easing
        elif self.easing == EasingType.EXPO_IN:
            return 0 if t == 0 else math.pow(2, 10 * (t - 1))
        elif self.easing == EasingType.EXPO_OUT:
            return 1 if t == 1 else 1 - math.pow(2, -10 * t)
        elif self.easing == EasingType.EXPO_IN_OUT:
            if t == 0 or t == 1:
                return t
            if t < 0.5:
                return math.pow(2, 20 * t - 10) / 2
            return (2 - math.pow(2, -20 * t + 10)) / 2
        
        # Circular easing
        elif self.easing == EasingType.CIRC_IN:
            return 1 - math.sqrt(1 - t * t)
        elif self.easing == EasingType.CIRC_OUT:
            t -= 1
            return math.sqrt(1 - t * t)
        elif self.easing == EasingType.CIRC_IN_OUT:
            if t < 0.5:
                return (1 - math.sqrt(1 - 4 * t * t)) / 2
            t -= 1
            return (math.sqrt(1 - 4 * t * t) + 1) / 2
        
        # Elastic easing
        elif self.easing == EasingType.ELASTIC_IN:
            if t == 0 or t == 1:
                return t
            return -math.pow(2, 10 * (t - 1)) * math.sin((t - 1.1) * 5 * math.pi)
        elif self.easing == EasingType.ELASTIC_OUT:
            if t == 0 or t == 1:
                return t
            return math.pow(2, -10 * t) * math.sin((t - 0.1) * 5 * math.pi) + 1
        elif self.easing == EasingType.ELASTIC_IN_OUT:
            if t == 0 or t == 1:
                return t
            if t < 0.5:
                return -0.5 * math.pow(2, 20 * t - 10) * math.sin((20 * t - 11.125) * math.pi / 4.5)
            return 0.5 * math.pow(2, -20 * t + 10) * math.sin((20 * t - 11.125) * math.pi / 4.5) + 1
        
        # Back easing
        elif self.easing == EasingType.BACK_IN:
            s = 1.70158
            return t * t * ((s + 1) * t - s)
        elif self.easing == EasingType.BACK_OUT:
            s = 1.70158
            t -= 1
            return t * t * ((s + 1) * t + s) + 1
        elif self.easing == EasingType.BACK_IN_OUT:
            s = 1.70158 * 1.525
            if t < 0.5:
                t2 = t * 2
                return 0.5 * (t2 * t2 * ((s + 1) * t2 - s))
            t2 = t * 2 - 2
            return 0.5 * (t2 * t2 * ((s + 1) * t2 + s) + 2)
        
        # Bounce easing
        elif self.easing == EasingType.BOUNCE_IN:
            return 1 - Tween._bounce_out(1 - t)
        elif self.easing == EasingType.BOUNCE_OUT:
            return Tween._bounce_out(t)
        elif self.easing == EasingType.BOUNCE_IN_OUT:
            if t < 0.5:
                return (1 - Tween._bounce_out(1 - 2 * t)) / 2
            return (1 + Tween._bounce_out(2 * t - 1)) / 2
        
        # Default to linear
        return t
    
    @staticmethod
    def _bounce_out(t: float) -> float:
        """
        Bounce out easing function.
        
        Args:
            t: Input value (0.0 to 1.0)
            
        Returns:
            float: Bounced value
        """
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375
    
    # Configuration methods (Roblox Studio style)
    def set_easing(self, easing: Union[EasingType, str]) -> 'Tween':
        """
        Set the easing function for the animation.
        
        Args:
            easing: EasingType enum or string name
            
        Returns:
            Tween: Self for method chaining
        """
        if isinstance(easing, str):
            try:
                self.easing = EasingType[easing.upper()]
            except KeyError:
                self.easing = EasingType.LINEAR
        else:
            self.easing = easing
        return self
    
    def set_loops(self, loops: int, yoyo: bool = False) -> 'Tween':
        """
        Set number of loops and yoyo mode.
        
        Args:
            loops: Number of loops (0 = no loop, -1 = infinite)
            yoyo: If True, reverse animation on each loop
            
        Returns:
            Tween: Self for method chaining
        """
        self.loops = loops
        self.yoyo = yoyo
        return self
    
    def set_callbacks(self, 
                     on_start: Optional[Callable] = None,
                     on_update: Optional[Callable[['Tween', float], None]] = None,
                     on_complete: Optional[Callable] = None,
                     on_loop: Optional[Callable[[int], None]] = None,
                     on_stop: Optional[Callable] = None) -> 'Tween':
        """
        Set lifecycle callbacks for the animation.
        
        Args:
            on_start: Called when animation starts
            on_update: Called each frame with (tween, progress)
            on_complete: Called when animation completes
            on_loop: Called after each loop with loop number
            on_stop: Called when animation is stopped
            
        Returns:
            Tween: Self for method chaining
        """
        self.on_start = on_start
        self.on_update = on_update
        self.on_complete = on_complete
        self.on_loop = on_loop
        self.on_stop = on_stop
        return self
    
    # Static methods for global management
    @classmethod
    def update_all(cls, dt: Optional[float] = None):
        """
        Update all active tweens.
        
        Args:
            dt: Delta time in seconds (optional)
        """
        # Create copy to avoid modification during iteration
        tweens_to_update = cls._active_tweens.copy()
        
        for tween in tweens_to_update:
            if tween in cls._active_tweens:  # Check if still active
                tween.update(dt)
    
    @classmethod
    def cancel_all(cls):
        """
        Cancel all active tweens.
        """
        for tween in cls._active_tweens:
            tween.cancel()
        cls._active_tweens.clear()
    
    @classmethod
    def pause_all(cls):
        """
        Pause all active tweens.
        """
        for tween in cls._active_tweens:
            tween.pause()
    
    @classmethod
    def resume_all(cls):
        """
        Resume all paused tweens.
        """
        for tween in cls._active_tweens:
            tween.resume()
    
    @classmethod
    def get_active_count(cls) -> int:
        """
        Get number of active tweens.
        
        Returns:
            int: Number of active tweens
        """
        return len(cls._active_tweens)
    
    # Utility methods (Roblox Studio style)
    @classmethod
    def sequence(cls, tweens: List['Tween']) -> 'TweenSequence':
        """
        Create a sequence of tweens (executes one after another).
        
        Args:
            tweens: List of tweens to execute sequentially
            
        Returns:
            TweenSequence: Sequence controller
        """
        return TweenSequence(tweens)
    
    @classmethod
    def parallel(cls, tweens: List['Tween']) -> 'TweenParallel':
        """
        Create a parallel group of tweens (executes all simultaneously).
        
        Args:
            tweens: List of tweens to execute in parallel
            
        Returns:
            TweenParallel: Parallel group controller
        """
        return TweenParallel(tweens)

class AnimationHandler:
    """
    Global animation handler for managing all tweens in the engine.
    
    Integrates with LunaEngine to provide centralized animation control.
    """
    
    def __init__(self, engine=None):
        """
        Initialize the animation handler.
        
        Args:
            engine: Reference to LunaEngine instance (optional)
        """
        self.engine = engine
        self._animations: Dict[str, Tween] = {}
    
    def add(self, name: str, tween: Tween, auto_play: bool = True) -> Tween:
        """
        Add a tween to the handler with a name.
        
        Args:
            name: Unique name for the animation
            tween: Tween instance
            auto_play: If True, start playing immediately
            
        Returns:
            Tween: The added tween
        """
        if name in self._animations:
            # Stop existing animation with same name
            self._animations[name].stop()
        
        self._animations[name] = tween
        
        if auto_play:
            tween.play()
        
        return tween
    
    def get(self, name: str) -> Optional[Tween]:
        """
        Get a tween by name.
        
        Args:
            name: Animation name
            
        Returns:
            Optional[Tween]: Tween instance or None if not found
        """
        return self._animations.get(name)
    
    def remove(self, name: str, stop: bool = True) -> bool:
        """
        Remove a tween by name.
        
        Args:
            name: Animation name
            stop: If True, stop the animation before removing
            
        Returns:
            bool: True if animation was found and removed
        """
        if name in self._animations:
            if stop:
                self._animations[name].stop()
            del self._animations[name]
            return True
        return False
    
    def pause(self, name: str) -> bool:
        """
        Pause a specific animation.
        
        Args:
            name: Animation name
            
        Returns:
            bool: True if animation was found and paused
        """
        tween = self.get(name)
        if tween:
            tween.pause()
            return True
        return False
    
    def resume(self, name: str) -> bool:
        """
        Resume a specific animation.
        
        Args:
            name: Animation name
            
        Returns:
            bool: True if animation was found and resumed
        """
        tween = self.get(name)
        if tween:
            tween.resume()
            return True
        return False
    
    def stop(self, name: str, reset: bool = False) -> bool:
        """
        Stop a specific animation.
        
        Args:
            name: Animation name
            reset: If True, reset properties to initial values
            
        Returns:
            bool: True if animation was found and stopped
        """
        tween = self.get(name)
        if tween:
            tween.stop(reset=reset)
            return True
        return False
    
    def cancel(self, name: str) -> bool:
        """
        Cancel a specific animation (stops and resets).
        
        Args:
            name: Animation name
            
        Returns:
            bool: True if animation was found and canceled
        """
        return self.stop(name, reset=True)
    
    def is_playing(self, name: str) -> bool:
        """
        Check if an animation is currently playing.
        
        Args:
            name: Animation name
            
        Returns:
            bool: True if animation exists and is playing
        """
        tween = self.get(name)
        return tween and tween.is_playing and not tween.is_paused
    
    def is_paused(self, name: str) -> bool:
        """
        Check if an animation is paused.
        
        Args:
            name: Animation name
            
        Returns:
            bool: True if animation exists and is paused
        """
        tween = self.get(name)
        return tween and tween.is_paused
    
    def update(self, dt: Optional[float] = None):
        """
        Update all animations managed by this handler.
        
        Args:
            dt: Delta time in seconds
        """
        # Update all tweens in the global system
        Tween.update_all(dt)
        
        # Clean up completed animations without names
        self._cleanup_completed()
        
    def _cleanup_completed(self):
        """Remove completed animations from the named dictionary."""
        completed = []
        for name, tween in self._animations.items():
            if not tween.is_playing:
                completed.append(name)
        
        for name in completed:
            del self._animations[name]
    
    def pause_all(self):
        """Pause all animations."""
        Tween.pause_all()
    
    def resume_all(self):
        """Resume all animations."""
        Tween.resume_all()
    
    def stop_all(self, reset: bool = False):
        """Stop all animations."""
        for tween in self._animations.values():
            tween.stop(reset=reset)
        self._animations.clear()
        Tween.cancel_all()
    
    def cancel_all(self):
        """Cancel all animations (stop and reset)."""
        self.stop_all(reset=True)
    
    def get_active_count(self) -> int:
        """
        Get number of active animations.
        
        Returns:
            int: Number of active animations
        """
        return Tween.get_active_count()
    
    def clear(self):
        """Clear all animations from the handler."""
        self._animations.clear()

class TweenGroup:
    """Base class for groups of tweens (sequential or parallel)."""
    
    def __init__(self, tweens: List[Tween]):
        """
        Initialize a tween group.
        
        Args:
            tweens: List of tweens in the group
        """
        self.tweens = tweens
        self.is_playing = False
        self.current_index = 0
        
        # Group callbacks
        self.on_start: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None
    
    def play(self):
        """Start playing the tween group."""
        self.is_playing = True
        self.current_index = 0
        self._play_current()
    
    def _play_current(self):
        """Start playing the current tween in the group."""
        pass
    
    def update(self, dt: Optional[float] = None) -> bool:
        """
        Update the tween group.
        
        Args:
            dt: Delta time
            
        Returns:
            bool: True if group is complete
        """
        pass
    
    def cancel(self):
        """Cancel the tween group."""
        self.is_playing = False
        for tween in self.tweens:
            tween.cancel()

class TweenSequence(TweenGroup):
    """Plays tweens in sequence (one after another)."""
    
    def _play_current(self):
        """Start playing the current tween in sequence."""
        if self.current_index < len(self.tweens):
            current_tween = self.tweens[self.current_index]
            
            # Store original callback
            original_callback = current_tween.on_complete
            
            def sequence_callback():
                # Call original callback if exists
                if original_callback:
                    original_callback()
                
                # Move to next tween
                self.current_index += 1
                self._play_current()
            
            # Set our callback to chain tweens
            current_tween.on_complete = sequence_callback
            
            # Start the tween
            current_tween.play()
        else:
            # Sequence complete
            self.is_playing = False
            if self.on_complete:
                self.on_complete()
    
    def update(self, dt: Optional[float] = None) -> bool:
        """
        Update the tween sequence.
        
        Args:
            dt: Delta time
            
        Returns:
            bool: True if sequence is complete
        """
        if not self.is_playing or self.current_index >= len(self.tweens):
            return True
        
        # Update current tween
        current_tween = self.tweens[self.current_index]
        if not current_tween.is_playing:
            return True
        
        return current_tween.update(dt)

class TweenParallel(TweenGroup):
    """Plays tweens in parallel (all at the same time)."""
    
    def play(self):
        """Start playing all tweens in parallel."""
        self.is_playing = True
        
        # Track completed tweens
        self._completed_count = 0
        total_tweens = len(self.tweens)
        
        def parallel_callback(tween_idx):
            def callback():
                self._completed_count += 1
                if self._completed_count >= total_tweens:
                    self.is_playing = False
                    if self.on_complete:
                        self.on_complete()
            return callback
        
        # Start all tweens with completion tracking
        for i, tween in enumerate(self.tweens):
            # Store original callback
            original_callback = tween.on_complete
            
            def create_callback(idx, orig_cb):
                def callback():
                    if orig_cb:
                        orig_cb()
                    parallel_callback(idx)()
                return callback
            
            tween.on_complete = create_callback(i, original_callback)
            tween.play()
    
    def update(self, dt: Optional[float] = None) -> bool:
        """
        Update all tweens in parallel.
        
        Args:
            dt: Delta time
            
        Returns:
            bool: True if all tweens are complete
        """
        if not self.is_playing:
            return True
        
        all_complete = True
        for tween in self.tweens:
            if tween.is_playing:
                tween.update(dt)
                if tween.is_playing:
                    all_complete = False
        
        return all_complete