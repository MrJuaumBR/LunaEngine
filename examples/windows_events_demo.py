"""
Window Events Demo - Comprehensive Testing of Window Event Decorators

ENGINE PATH:
lunaengine/examples/window_events_demo.py

DESCRIPTION:
This demo showcases all window event features with decorators, including:
- Window focus/blur events
- Window resize events
- Window move events
- Minimize/maximize/restore events
- Mouse enter/leave window
- Window close events
- Window state tracking

FEATURES:
+ Decorator-based event handling
+ Real-time window state monitoring
+ Event logging with timestamps
+ Interactive event testing
+ Window manipulation controls
+ Performance monitoring during window events
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
from lunaengine.backend.types import WindowEventData, WindowEventType
import pygame

class WindowEventsDemo(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        
        # Demo state
        self.event_log = []
        self.max_log_entries = 15
        self.window_state = {
            'focused': True,
            'minimized': False,
            'maximized': False,
            'visible': True,
            'position': (0, 0),
            'size': (800, 600)
        }
        self.event_counters = {
            'resize': 0,
            'move': 0,
            'focus': 0,
            'blur': 0,
            'minimize': 0,
            'maximize': 0,
            'restore': 0,
            'enter': 0,
            'leave': 0,
            'close': 0
        }
        self.perf_stats = {}
        
        # Set up UI and register events
        self.setup_ui()
        self.register_window_events()
        
        # Initial update
        self.update_window_state_display()
        
    def on_enter(self, previous_scene: str = None):
        print("=== Window Events Demo ===")
        print("Testing window event decorators with LunaEngine")
        print("\nTry these actions:")
        print("+ Click outside window to trigger blur/focus events")
        print("+ Resize the window")
        print("+ Move the window around")
        print("+ Minimize/Restore the window")
        print("+ Mouse in/out of window")
        print("+ Click the 'Test Events' buttons")
        
        # Log initial entry
        self.log_event("System", "Scene loaded - window events ready")
        
    def on_exit(self, next_scene: str = None):
        print("Exiting Window Events Demo")
        self.log_event("System", "Exiting scene")
        
    def register_window_events(self):
        """Register all window event handlers using decorators."""
        
        # Window focus events
        @self.engine.on_window_focus
        def on_focus(event: WindowEventData):
            self.event_counters['focus'] += 1
            self.window_state['focused'] = True
            self.log_event("WINDOW FOCUS", "Window gained focus", event)
            print("(W++) Window focused")
            
            # Example: Resume game audio when window is focused
            # if hasattr(self, 'audio_manager'):
            #     self.audio_manager.unpause_all()
        
        @self.engine.on_window_blur
        def on_blur(event: WindowEventData):
            self.event_counters['blur'] += 1
            self.window_state['focused'] = False
            self.log_event("WINDOW BLUR", "Window lost focus", event)
            print("(W--)  Window blurred")
            
            # Example: Pause game when window loses focus
            # self.engine.fps = 30  # Reduce FPS when not focused
        
        # Window resize events
        @self.engine.on_window_resize
        def on_resize(event: WindowEventData):
            self.event_counters['resize'] += 1
            self.window_state['size'] = event.size
            old_size = event.data.get('old_size', (0, 0))
            self.log_event("WINDOW RESIZE", f"Resized from {old_size} to {event.size}", event)
            print(f"(W+-) Window resized: {event.size}")
            
            # Example: Update UI layout on resize
            if hasattr(self, 'resize_ui_layout'):
                self.resize_ui_layout(event.size)
        
        # Window move events
        @self.engine.on_window_move
        def on_move(event: WindowEventData):
            self.event_counters['move'] += 1
            self.window_state['position'] = event.position
            self.log_event("WINDOW MOVE", f"Moved to {event.position}", event)
            print(f"(W/) Window moved: {event.position}")
        
        # Window minimize/maximize/restore events
        @self.engine.on_window_minimize
        def on_minimize(event: WindowEventData):
            self.event_counters['minimize'] += 1
            self.window_state['minimized'] = True
            self.window_state['maximized'] = False
            self.log_event("WINDOW MINIMIZE", "Window minimized", event)
            print("(W-) Window minimized")
            
            # Example: Save battery when minimized
            self.engine.fps = 30
            self.engine.show_info("Window minimized - reducing FPS to save power", 2)
        
        @self.engine.on_window_maximize
        def on_maximize(event: WindowEventData):
            self.event_counters['maximize'] += 1
            self.window_state['maximized'] = True
            self.window_state['minimized'] = False
            self.log_event("WINDOW MAXIMIZE", "Window maximized", event)
            print("(W+) Window maximized")
            
            self.engine.show_success("Window maximized", 2)
        
        @self.engine.on_window_restore
        def on_restore(event: WindowEventData):
            self.event_counters['restore'] += 1
            self.window_state['minimized'] = False
            self.window_state['maximized'] = False
            self.log_event("WINDOW RESTORE", "Window restored", event)
            print("(W) Window restored")
            
            # Restore normal FPS
            self.engine.fps = 60
            self.engine.show_info("Window restored - normal FPS", 2)
        
        # Mouse enter/leave window
        @self.engine.on_window_enter
        def on_enter(event: WindowEventData):
            self.event_counters['enter'] += 1
            self.log_event("MOUSE ENTER", "Mouse entered window", event)
            print("(M) Mouse entered window")
            
            # Example: Show custom cursor
            # pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
        
        @self.engine.on_window_leave
        def on_leave(event: WindowEventData):
            self.event_counters['leave'] += 1
            self.log_event("MOUSE LEAVE", "Mouse left window", event)
            print("(M) Mouse left window")
            
            # Example: Hide custom cursor
            # pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        # Window close event (with confirmation example)
        @self.engine.on_window_close
        def on_close(event: WindowEventData):
            self.event_counters['close'] += 1
            self.log_event("WINDOW CLOSE", "Close requested", event)
            print("(X) Window close requested")
            
            self.engine.show_warning("Close event received (would show confirmation dialog)", 3)
            
            
        # Store references to prevent garbage collection
        self._event_handlers = [
            on_focus, on_blur, on_resize, on_move, 
            on_minimize, on_maximize, on_restore,
            on_enter, on_leave, on_close
        ]
    
    def setup_ui(self):
        """Set up all UI elements for the demo."""
        
        # Title
        title = TextLabel(400, 20, "Window Events Demo", 32, root_point=(0.5, 0))
        self.add_ui_element(title)
        
        subtitle = TextLabel(400, 50, "Test Window Event Decorators", 18, (200, 200, 255), root_point=(0.5, 0))
        self.add_ui_element(subtitle)
        
        # Event Log Section
        log_label = TextLabel(20, 90, "Event Log (Last 15 events):", 20, (255, 255, 0))
        self.add_ui_element(log_label)
        
        # Event log display area (simulated with TextLabels)
        self.event_log_labels = []
        for i in range(self.max_log_entries):
            label = TextLabel(30, 120 + i * 22, "", 14, (200, 200, 200))
            self.add_ui_element(label)
            self.event_log_labels.append(label)
        
        # Event Counters Section
        counters_label = TextLabel(450, 90, "Event Counters:", 20, (255, 255, 0))
        self.add_ui_element(counters_label)
        
        self.counter_labels = {}
        events_y = 120
        for i, (event_name, count) in enumerate(self.event_counters.items()):
            label = TextLabel(450, events_y + i * 22, f"{event_name}: 0", 16, (200, 200, 200))
            self.add_ui_element(label)
            self.counter_labels[event_name] = label
        
        # Window State Display
        state_label = TextLabel(450, 350, "Window State:", 20, (255, 255, 0))
        self.add_ui_element(state_label)
        
        self.state_labels = {}
        state_info = [
            ('focused', 'Focused:'),
            ('minimized', 'Minimized:'), 
            ('maximized', 'Maximized:'),
            ('visible', 'Visible:'),
            ('position', 'Position:'),
            ('size', 'Size:')
        ]
        
        for i, (key, label_text) in enumerate(state_info):
            label = TextLabel(450, 380 + i * 25, f"{label_text} --", 16, (200, 200, 200))
            self.add_ui_element(label)
            self.state_labels[key] = label
        
        # Interactive Controls Section
        controls_label = TextLabel(20, 450, "Interactive Controls:", 20, (255, 255, 0))
        self.add_ui_element(controls_label)
        
        # Row 1: Focus/Blur test buttons
        focus_btn = Button(20, 490, 180, 35, "Test Focus Event")
        focus_btn.set_on_click(self.trigger_focus_event)
        focus_btn.set_simple_tooltip("Simulate window focus event")
        self.add_ui_element(focus_btn)
        
        blur_btn = Button(220, 490, 180, 35, "Test Blur Event")
        blur_btn.set_on_click(self.trigger_blur_event)
        blur_btn.set_simple_tooltip("Simulate window blur event")
        self.add_ui_element(blur_btn)
        
        # Row 2: Resize/Move test buttons
        resize_btn = Button(20, 540, 180, 35, "Test Resize Event")
        resize_btn.set_on_click(self.trigger_resize_event)
        resize_btn.set_simple_tooltip("Simulate window resize")
        self.add_ui_element(resize_btn)
        
        move_btn = Button(220, 540, 180, 35, "Test Move Event")
        move_btn.set_on_click(self.trigger_move_event)
        move_btn.set_simple_tooltip("Simulate window move")
        self.add_ui_element(move_btn)
        
        # Row 3: Minimize/Restore/Close buttons
        minimize_btn = Button(20, 590, 120, 35, "Minimize")
        minimize_btn.set_on_click(self.minimize_window)
        minimize_btn.set_simple_tooltip("Minimize the window")
        self.add_ui_element(minimize_btn)
        
        restore_btn = Button(150, 590, 120, 35, "Restore")
        restore_btn.set_on_click(self.restore_window)
        restore_btn.set_simple_tooltip("Restore window")
        self.add_ui_element(restore_btn)
        
        toggle_fullscreen_btn = Button(280, 590, 120, 35, "Toggle Fullscreen")
        toggle_fullscreen_btn.set_on_click(self.toggle_fullscreen)
        toggle_fullscreen_btn.set_simple_tooltip("Toggle fullscreen mode")
        self.add_ui_element(toggle_fullscreen_btn)
        
        # Clear log button
        clear_btn = Button(450, 540, 150, 35, "Clear Event Log")
        clear_btn.set_on_click(self.clear_event_log)
        clear_btn.set_simple_tooltip("Clear all event logs")
        self.add_ui_element(clear_btn)
        
        # Performance Stats
        perf_label = TextLabel(20, 640, "Performance During Events:", 18, (255, 255, 0))
        self.add_ui_element(perf_label)
        
        self.perf_fps = TextLabel(20, 670, "FPS: --", 16, (100, 255, 100))
        self.add_ui_element(self.perf_fps)
        
        self.perf_frame_time = TextLabel(20, 695, "Frame Time: -- ms", 16, (200, 150, 255))
        self.add_ui_element(self.perf_frame_time)
        
        # Instructions
        instructions = [
            "Try these window actions:",
            "+ Click outside window → Blur event",
            "+ Click back on window → Focus event",
            "+ Resize window → Resize event",
            "+ Move window → Move event",
            "+ Minimize window → Minimize event",
            "+ Restore window → Restore event",
            "+ Mouse in/out → Enter/Leave events"
        ]
        
        for i, instruction in enumerate(instructions):
            instruction_label = TextLabel(650, 120 + i * 25, instruction, 14, (150, 200, 150))
            self.add_ui_element(instruction_label)
    
    def log_event(self, event_type: str, message: str, event_data: WindowEventData = None):
        """Add an event to the log display."""
        timestamp = time.strftime("%H:%M:%S")
        
        if event_data:
            log_entry = f"[{timestamp}] {event_type}: {message}"
        else:
            log_entry = f"[{timestamp}] {event_type}: {message}"
        
        # Add to log list
        self.event_log.append(log_entry)
        
        # Keep only last N entries
        if len(self.event_log) > self.max_log_entries:
            self.event_log = self.event_log[-self.max_log_entries:]
        
        # Update display
        for i, label in enumerate(self.event_log_labels):
            if i < len(self.event_log):
                label.set_text(self.event_log[i])
            else:
                label.set_text("")
        
        # Update counter displays
        for event_name, label in self.counter_labels.items():
            label.set_text(f"{event_name}: {self.event_counters[event_name]}")
    
    def update_window_state_display(self):
        """Update the window state display."""
        state_display = {
            'focused': "Yes" if self.window_state['focused'] else "No",
            'minimized': "Yes" if self.window_state['minimized'] else "No",
            'maximized': "Yes" if self.window_state['maximized'] else "No",
            'visible': "Yes" if self.window_state['visible'] else "No",
            'position': f"{self.window_state['position'][0]}, {self.window_state['position'][1]}",
            'size': f"{self.window_state['size'][0]}x{self.window_state['size'][1]}"
        }
        
        for key, label in self.state_labels.items():
            if key in state_display:
                # Extract the label text before the colon
                label_text = label.text.split(":")[0] if ":" in label.text else label.text
                label.set_text(f"{label_text}: {state_display[key]}")
    
    def trigger_focus_event(self):
        """Manually trigger a focus event (simulated)."""
        # This would normally come from the OS, but we can simulate it
        fake_event = WindowEventData(
            event_type=WindowEventType.FOCUS_GAINED,
            timestamp=pygame.time.get_ticks(),
            window_id=0,
            data={}
        )
        
        # Call focus handlers directly
        for handler in self._event_handlers:
            if hasattr(handler, '__name__') and 'on_focus' in handler.__name__:
                try:
                    handler(fake_event)
                except Exception as e:
                    print(f"Error triggering focus event: {e}")
        
        self.engine.show_info("Focus event triggered", 1)
    
    def trigger_blur_event(self):
        """Manually trigger a blur event (simulated)."""
        fake_event = WindowEventData(
            event_type=WindowEventType.FOCUS_LOST,
            timestamp=pygame.time.get_ticks(),
            window_id=0,
            data={}
        )
        
        # Call blur handlers directly
        for handler in self._event_handlers:
            if hasattr(handler, '__name__') and 'on_blur' in handler.__name__:
                try:
                    handler(fake_event)
                except Exception as e:
                    print(f"Error triggering blur event: {e}")
        
        self.engine.show_warning("Blur event triggered", 1)
    
    def trigger_resize_event(self):
        """Manually trigger a resize event."""
        # Get current size
        current_size = pygame.display.get_window_size()
        new_size = (current_size[0] - 50, current_size[1] - 30)
        
        # Resize the window
        pygame.display.set_mode(new_size, pygame.RESIZABLE)
        
        self.engine.show_info(f"Resized to {new_size}", 1)
    
    def trigger_move_event(self):
        """Manually trigger a move event (simulated)."""
        # Note: Pygame doesn't have a direct way to move windows,
        # so we'll just log a simulated event
        fake_event = WindowEventData(
            event_type=WindowEventType.MOVED,
            timestamp=pygame.time.get_ticks(),
            window_id=0,
            data={'position': (100, 100)}
        )
        
        # Call move handlers directly
        for handler in self._event_handlers:
            if hasattr(handler, '__name__') and 'on_move' in handler.__name__:
                try:
                    handler(fake_event)
                except Exception as e:
                    print(f"Error triggering move event: {e}")
        
        self.engine.show_info("Move event simulated", 1)
    
    def minimize_window(self):
        """Minimize the window."""
        # Note: Pygame doesn't have a direct minimize function
        # This would require platform-specific code
        # For now, we'll simulate it
        fake_event = WindowEventData(
            event_type=WindowEventType.MINIMIZED,
            timestamp=pygame.time.get_ticks(),
            window_id=0,
            data={}
        )
        
        # Call minimize handlers directly
        for handler in self._event_handlers:
            if hasattr(handler, '__name__') and 'on_minimize' in handler.__name__:
                try:
                    handler(fake_event)
                except Exception as e:
                    print(f"Error triggering minimize event: {e}")
        
        self.engine.show_warning("Minimize simulated (platform-dependent)", 2)
    
    def restore_window(self):
        """Restore the window."""
        fake_event = WindowEventData(
            event_type=WindowEventType.RESTORED,
            timestamp=pygame.time.get_ticks(),
            window_id=0,
            data={}
        )
        
        # Call restore handlers directly
        for handler in self._event_handlers:
            if hasattr(handler, '__name__') and 'on_restore' in handler.__name__:
                try:
                    handler(fake_event)
                except Exception as e:
                    print(f"Error triggering restore event: {e}")
        
        self.engine.show_success("Restore event triggered", 1)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        # Toggle fullscreen
        self.engine.fullscreen = not self.engine.fullscreen
        
        # Recreate window with new flags
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        if self.engine.fullscreen:
            flags |= pygame.FULLSCREEN
            flags |= pygame.SCALED
        
        pygame.display.set_mode((self.engine.width, self.engine.height), flags)
        
        status = "ON" if self.engine.fullscreen else "OFF"
        self.engine.show_info(f"Fullscreen toggled: {status}", 2)
        self.log_event("FULLSCREEN", f"Toggled fullscreen {status}")
    
    def clear_event_log(self):
        """Clear the event log."""
        self.event_log = []
        for label in self.event_log_labels:
            label.set_text("")
        
        self.engine.show_info("Event log cleared", 1)
    
    def update(self, dt):
        """Update scene logic."""
        # Update window state from engine
        if hasattr(self.engine, 'get_window_state'):
            engine_state = self.engine.get_window_state()
            if engine_state:
                self.window_state.update(engine_state)
        
        # Update displays
        self.update_window_state_display()
        
        # Update performance stats
        self.perf_stats = self.engine.get_fps_stats()
        self.perf_fps.set_text(f"FPS: {self.perf_stats.get('current_fps', 0):.1f}")
        self.perf_frame_time.set_text(f"Frame Time: {self.perf_stats.get('frame_time_ms', 0):.2f} ms")
        
        # Check for window state changes
        current_size = pygame.display.get_window_size()
        if current_size != self.window_state['size']:
            # Window was resized outside our event system
            self.window_state['size'] = current_size
            self.log_event("SIZE CHANGE", f"Detected size change to {current_size}")
    
    def render(self, renderer):
        """Render the scene."""
        # Draw gradient background
        renderer.fill_screen((20, 25, 40))
        
        # Draw header
        renderer.draw_rect(0, 0, self.engine.width, 80, (30, 35, 50, 200))
        
        # Draw section backgrounds
        renderer.draw_rect(10, 100, 420, 340, (40, 45, 60, 150))
        renderer.draw_rect(440, 100, 350, 240, (40, 45, 60, 150))
        renderer.draw_rect(10, 450, 400, 190, (40, 45, 60, 150))
        renderer.draw_rect(10, 650, 400, 80, (40, 45, 60, 150))
        renderer.draw_rect(650, 100, 340, 400, (40, 45, 60, 150))
        
        # Draw separator lines
        renderer.draw_rect(0, 440, self.engine.width, 2, (100, 100, 100, 100))
        renderer.draw_rect(0, 640, self.engine.width, 2, (100, 100, 100, 100))
        
        # Draw focus indicator
        if self.window_state['focused']:
            # x, y, w, h, color
            renderer.draw_rect(self.engine.width - 50, 10, 40, 40, (0, 255, 0, 100))
            
            # text, x, y, color, font
            renderer.draw_text("True", self.engine.width - 45, 20, (0, 255, 0), FontManager.get_font(None, 24))
        else:
            renderer.draw_rect(self.engine.width - 50, 10, 40, 40, (255, 0, 0, 100))
            
            renderer.draw_text("False", self.engine.width - 45, 20, (255, 0, 0), FontManager.get_font(None, 24))

def main():
    """Main function to run the demo."""
    
    print("=" * 60)
    print("WINDOW EVENTS DEMO")
    print("=" * 60)
    print("Testing new window event decorator system for LunaEngine")
    print("\nFeatures being tested:")
    print("- Window focus/blur events")
    print("- Window resize events")
    print("- Window move events")
    print("- Minimize/restore/maximize events")
    print("- Mouse enter/leave events")
    print("- Window close events")
    print("- Real-time state tracking")
    print("- Decorator-based event handling")
    print("\nThe demo will show events in real-time as they occur.")
    print("=" * 60)
    
    # Create engine with resizable window
    engine = LunaEngine(
        title="LunaEngine - Window Events Demo",
        width=1024,
        height=768,
        fullscreen=False
    )
    
    # Make window resizable for testing
    pygame.display.set_mode((1024, 768), pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF)
    
    # Set FPS
    engine.fps = 60
    
    # Add and set the scene
    engine.add_scene("main", WindowEventsDemo)
    engine.set_scene("main")
    
    # Show welcome notification
    engine.show_info("Window Events Demo Loaded!", 3)
    
    # Run the engine
    engine.run()

if __name__ == "__main__":
    main()