"""
timer_demo.py - Timer System Demo for LunaEngine

This demo demonstrates the integrated timer system accessible via the engine.
It shows:
- Adding one-shot and repeating timers
- Pausing/resuming timers
- Resetting timers
- Removing/destroying timers
- Anonymous timers
- Live display of timer status (elapsed, remaining, done)
- Global timer controls (pause all, resume all, clear all)
- Notifications on timer completion
"""

import sys
import os
import time
# sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))

from lunaengine.ui import *
from lunaengine.core import LunaEngine, Scene
from lunaengine.misc.icons import Icons
from lunaengine.backend import *


class TimerDemoScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        # Store references to timer UI entries: name -> dict of UI elements
        self.timer_ui_entries = {}
        self.timer_ui_frames = []  # list of frames for scrolling

        # Global controls
        self.paused_all = False
        self.timer_list_updated = True  # flag to rebuild list

        # Setup the UI
        self.setup_ui()

        # Add a convenience function to LiveInspector
        self.engine.add_function_to_live_inspector(
            'List Timers',
            lambda: print(f"Active timers: {self.engine.get_all_timers()}"),
            [],
            'Prints all active timer names to console.'
        )

    def on_enter(self, previous_scene: str | None = None):
        print("=== Timer Demo ===")
        print("Use the controls to add, manage, and monitor timers.")
        print("Timers fire notifications upon completion.")

    def on_exit(self, next_scene: str | None = None):
        # Clean up all timers
        self.engine.clear_timers()
        print("All timers cleared.")

    def setup_ui(self):
        """Build the UI for the timer demo."""
        self.engine.set_global_theme(ThemeType.DEFAULT)

        # --- Title ---
        title = TextLabel(512, 30, "LunaEngine - Timer Demo", 36, pivot=(0.5, 0))
        self.add_ui_element(title)

        # --- Main Frame ---
        main_frame = UiFrame(20, 70, 984, 680)
        main_frame.set_background_color((30, 30, 40, 200))
        main_frame.set_border((80, 80, 100), 1)
        main_frame.set_corner_radius(8)
        self.add_ui_element(main_frame)

        # --- Add Timer Controls ---
        controls_y = 20

        # Duration label + input
        duration_label = TextLabel(20, controls_y + 5, "Duration (s):", 16, (200, 200, 255))
        main_frame.add_child(duration_label)
        self.duration_selector = NumberSelector(105, controls_y, 80, 30, 1, 60, 5, step=1)
        self.duration_selector.set_simple_tooltip("Timer duration in seconds")
        main_frame.add_child(self.duration_selector)

        # Repeating checkbox
        self.repeating_checkbox = Checkbox(195, controls_y + 2, 120, 30, False, label="Repeating")
        self.repeating_checkbox.set_simple_tooltip("If checked, timer will repeat indefinitely")
        main_frame.add_child(self.repeating_checkbox)

        # Add Timer button
        add_btn = Button(325, controls_y, 125, 30, "Add Timer", icon=Icons.PLUS)
        add_btn.set_on_click(self.add_timer)
        add_btn.set_simple_tooltip("Add a timer with the specified duration")
        main_frame.add_child(add_btn)

        # Add Anonymous Timer button
        anon_btn = Button(460, controls_y, 140, 30, "Add Anonymous")
        anon_btn.set_on_click(self.add_anonymous_timer)
        anon_btn.set_simple_tooltip("Add a timer with an auto-generated name")
        main_frame.add_child(anon_btn)

        # Global controls
        pause_all_btn = Button(620, controls_y, 100, 30, "Pause All")
        pause_all_btn.set_on_click(self.pause_all_timers)
        main_frame.add_child(pause_all_btn)

        resume_all_btn = Button(730, controls_y, 100, 30, "Resume All")
        resume_all_btn.set_on_click(self.resume_all_timers)
        main_frame.add_child(resume_all_btn)

        clear_all_btn = Button(840, controls_y, 80, 30, "Clear", icon=Icons.TRASH)
        clear_all_btn.set_on_click(self.clear_all_timers)
        clear_all_btn.set_simple_tooltip("Remove all timers")
        main_frame.add_child(clear_all_btn)

        # --- Scrolling Frame for Timer List ---
        self.timer_scroll = ScrollingFrame(20, 70, 944, 580, 920, 1200)
        self.timer_scroll.set_simple_tooltip("List of active timers - scroll to see all")
        main_frame.add_child(self.timer_scroll)

        # Initial placeholder
        self.placeholder = TextLabel(10, 10, "No timers active. Use the 'Add Timer' button above.", 18, (150, 150, 150))
        self.timer_scroll.add_child(self.placeholder)

        # --- Bottom status ---
        self.status_label = TextLabel(20, 660, "Ready", 14, (200, 200, 200))
        main_frame.add_child(self.status_label)

        # --- FPS and other info (optional) ---
        self.fps_display = TextLabel(self.engine.width - 10, 20, "FPS: --", 14, (100, 255, 100), pivot=(1, 0))
        self.add_ui_element(self.fps_display)

    def add_timer(self):
        """Add a timer with the specified duration and repeating option."""
        duration = self.duration_selector.value
        repeats = self.repeating_checkbox.value
        name = f"timer_{int(time.time() * 1000)}_{len(self.engine.get_all_timers())}"

        # Define a callback that shows a notification
        def on_timer_done(timer_name):
            self.engine.show_success(f"Timer '{timer_name}' completed!", duration=2.0)
            # The UI will refresh automatically in update()

        success = self.engine.add_timer(name, duration, on_timer_done, callback_args=(name,), repeats=repeats)
        if success:
            self.engine.show_info(f"Timer '{name}' added ({duration}s, repeats={repeats})")
            self.status_label.set_text(f"Added timer: {name}")
            self.timer_list_updated = True
        else:
            self.engine.show_error(f"Could not add timer '{name}'. It may already exist.")

    def add_anonymous_timer(self):
        """Add a timer with an auto-generated name."""
        duration = self.duration_selector.value
        repeats = self.repeating_checkbox.value

        def on_timer_done():
            self.engine.show_success("An anonymous timer completed!", duration=2.0)

        name = self.engine.add_anonymous_timer(duration, on_timer_done, repeats=repeats)
        self.engine.show_info(f"Anonymous timer '{name}' added ({duration}s, repeats={repeats})")
        self.status_label.set_text(f"Added anonymous timer: {name}")
        self.timer_list_updated = True

    def pause_all_timers(self):
        """Pause all timers."""
        # We need to get all timer names and pause each
        for name in self.engine.get_all_timers():
            self.engine.pause_timer(name)
        self.engine.show_info("All timers paused")
        self.status_label.set_text("All timers paused")
        self.timer_list_updated = True

    def resume_all_timers(self):
        """Resume all timers."""
        for name in self.engine.get_all_timers():
            self.engine.resume_timer(name)
        self.engine.show_info("All timers resumed")
        self.status_label.set_text("All timers resumed")
        self.timer_list_updated = True

    def clear_all_timers(self):
        """Remove all timers."""
        self.engine.clear_timers()
        self.engine.show_info("All timers cleared")
        self.status_label.set_text("All timers cleared")
        self.timer_list_updated = True

    def rebuild_timer_list(self):
        """Rebuild the UI list of timers based on current engine timers."""
        # Clear existing UI entries
        for frame in self.timer_ui_frames:
            self.timer_scroll.remove_child(frame)
        self.timer_ui_frames.clear()
        self.timer_ui_entries.clear()

        # Remove placeholder if exists
        if self.placeholder in self.timer_scroll.children:
            self.timer_scroll.remove_child(self.placeholder)

        # Get all timers
        timer_names = self.engine.get_all_timers()
        if not timer_names:
            # Re-add placeholder
            self.timer_scroll.add_child(self.placeholder)
            return

        # Sort by name for consistency
        timer_names.sort()

        y_offset = 10
        for idx, name in enumerate(timer_names):
            # Create a frame for each timer
            frame = UiFrame(10, y_offset, 900, 50)
            frame.set_background_color((50, 50, 70, 200))
            frame.set_border((80, 80, 120), 1)
            frame.set_corner_radius(5)
            self.timer_scroll.add_child(frame)
            self.timer_ui_frames.append(frame)

            # Timer name
            name_label = TextLabel(10, 10, name, 16, (255, 255, 255))
            frame.add_child(name_label)

            # Duration
            dur_label = TextLabel(175, 10, "Duration: --", 14, (200, 200, 200))
            frame.add_child(dur_label)

            # Elapsed / Remaining
            elapsed_label = TextLabel(270, 10, "Elapsed: --", 14, (100, 255, 100))
            frame.add_child(elapsed_label)

            remaining_label = TextLabel(370, 10, "Remaining: --", 14, (255, 200, 100))
            frame.add_child(remaining_label)

            # Status
            status_label = TextLabel(470, 10, "Status: --", 14, (200, 200, 200))
            frame.add_child(status_label)

            # Buttons
            pause_btn = Button(570, 8, 60, 28, "Pause")
            pause_btn.set_on_click(lambda n=name: self.pause_timer(n))
            pause_btn.set_simple_tooltip(f"Pause timer '{name}'")
            frame.add_child(pause_btn)

            resume_btn = Button(645, 8, 60, 28, "Resume")
            resume_btn.set_on_click(lambda n=name: self.resume_timer(n))
            resume_btn.set_simple_tooltip(f"Resume timer '{name}'")
            frame.add_child(resume_btn)

            reset_btn = Button(720, 8, 60, 28, "Reset")
            reset_btn.set_on_click(lambda n=name: self.reset_timer(n))
            reset_btn.set_simple_tooltip(f"Reset timer '{name}'")
            frame.add_child(reset_btn)

            destroy_btn = Button(795, 8, 75, 32, "Destroy", icon=Icons.TRASH)
            destroy_btn.set_on_click(lambda n=name: self.destroy_timer(n))
            destroy_btn.set_simple_tooltip(f"Destroy timer '{name}'")
            frame.add_child(destroy_btn)

            # Store references for updating
            self.timer_ui_entries[name] = {
                'frame': frame,
                'duration_label': dur_label,
                'elapsed_label': elapsed_label,
                'remaining_label': remaining_label,
                'status_label': status_label,
                'pause_btn': pause_btn,
                'resume_btn': resume_btn,
                'reset_btn': reset_btn,
                'destroy_btn': destroy_btn,
            }

            y_offset += 60

        # Update scroll area content height
        self.timer_scroll.content_height = y_offset + 20
        self.timer_list_updated = False

    def pause_timer(self, name: str):
        if self.engine.pause_timer(name):
            self.engine.show_info(f"Timer '{name}' paused")
            self.status_label.set_text(f"Paused: {name}")
        else:
            self.engine.show_warning(f"Could not pause '{name}'. Check if it exists or is already paused.")

    def resume_timer(self, name: str):
        if self.engine.resume_timer(name):
            self.engine.show_info(f"Timer '{name}' resumed")
            self.status_label.set_text(f"Resumed: {name}")
        else:
            self.engine.show_warning(f"Could not resume '{name}'. Check if it exists or is not paused.")

    def reset_timer(self, name: str):
        if self.engine.reset_timer(name):
            self.engine.show_info(f"Timer '{name}' reset")
            self.status_label.set_text(f"Reset: {name}")
        else:
            self.engine.show_warning(f"Could not reset '{name}'. Timer may not exist.")

    def destroy_timer(self, name: str):
        if self.engine.destroy_timer(name):
            self.engine.show_info(f"Timer '{name}' marked for destruction")
            self.status_label.set_text(f"Destroying: {name}")
            self.timer_list_updated = True
        else:
            self.engine.show_warning(f"Could not destroy '{name}'. Timer may not exist.")

    def update_timer_list(self):
        """Update the labels of all timer entries with current data."""
        for name, entry in self.timer_ui_entries.items():
            # Check if timer still exists
            if not self.engine.timer_exists(name):
                # Timer was removed/destroyed, flag for rebuild
                self.timer_list_updated = True
                continue
            elapsed = self.engine.timer_elapsed(name)
            remaining = self.engine.timer_remaining(name)
            done = self.engine.timer_done(name)
            paused = self.engine.timer_paused(name)

            if elapsed is not None:
                entry['elapsed_label'].set_text(f"Elapsed: {elapsed:.1f}s")
            if remaining is not None:
                entry['remaining_label'].set_text(f"Remaining: {remaining:.1f}s")

            # Status
            if done:
                entry['status_label'].set_text("Status: Done")
                entry['status_label'].set_color((255, 100, 100))
            elif paused:
                entry['status_label'].set_text("Status: Paused")
                entry['status_label'].set_color((255, 200, 50))
            else:
                entry['status_label'].set_text("Status: Running")
                entry['status_label'].set_color((100, 255, 100))

            # Update button states
            if paused:
                entry['pause_btn'].enabled = False
                entry['resume_btn'].enabled = True
            else:
                entry['pause_btn'].enabled = True
                entry['resume_btn'].enabled = False

    def update(self, dt):
        # Update FPS
        stats = self.engine.get_fps_stats()
        self.fps_display.set_text(f"FPS: {stats.get('current_fps', 0):.1f}")

        # Rebuild timer list if needed
        if self.timer_list_updated:
            self.rebuild_timer_list()
        else:
            # Update existing entries
            self.update_timer_list()

        # Also check for new timers added via other means? We'll just check count.
        current_count = self.engine.get_timer_count()
        if current_count != len(self.timer_ui_entries):
            self.timer_list_updated = True

    def render(self, renderer):
        renderer.clear()
        renderer.fill_screen(ThemeManager.get_color('background'))


def main():
    # Create engine with debug enabled
    engine = LunaEngine("LunaEngine - Timer Demo", 1024, 768, icon=Icons.TIMER, debug=True)
    engine.fps = 60

    # Add the scene
    engine.add_scene("timer_demo", TimerDemoScene)
    engine.set_scene("timer_demo")

    engine.run()


if __name__ == "__main__":
    main()