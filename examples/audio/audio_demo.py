"""
Audio Demo for LunaEngine 0.2.5+
Showcases the new AudioManager with named channels, curves, balance, and device selection.
"""

import sys
import os
import time
import math
import random
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import Scene, LunaEngine
from lunaengine.core.audio import AudioManager, AudioChannel, AudioCurve, AudioEvent
from lunaengine.ui import *
from lunaengine.ui.tween import Tween, EasingType, AnimationHandler
import pygame
import numpy as np


class AudioDemoScene(Scene):
    def on_enter(self, previous_scene=None):
        self.engine.set_global_theme(ThemeType.GRUVBOX)

    def __init__(self, engine: LunaEngine):
        super().__init__(engine)

        # Sound names
        self.sfx_name = "explosion"
        self.music_name = "bg_music"

        # UI state
        self.sfx_volume = 0.8
        self.music_volume = 0.7
        self.sfx_pitch = 1.0
        self.music_pitch = 1.0
        self.sfx_balance = 0.0
        self.music_balance = 0.0
        self.curve_duration = 2.0

        # Active channel references for status
        self.active_sfx_channels = {}  # key -> channel name
        self.music_channel = None

        # Event log
        self.event_log = []

        # Load audio files (or create placeholders)
        self.load_audio()

        # Setup UI tabs
        self.setup_ui()

        # Register audio events for logging
        self.audio_manager.on_event(AudioEvent.PLAYBACK_STARTED, self.on_audio_event)
        self.audio_manager.on_event(AudioEvent.PLAYBACK_COMPLETED, self.on_audio_event)
        self.audio_manager.on_event(AudioEvent.CURVE_FINISHED, self.on_audio_event)

        # Keyboard shortcuts
        @engine.on_event(pygame.KEYDOWN)
        def on_key(event):
            self.handle_key(event.key)

    # ---------- Audio Loading ----------
    def load_audio(self):
        """Load sound files; if missing, create placeholder tones."""
        try:
            # Try loading real files
            path = os.path.dirname(os.path.abspath(__file__))
            sfx_path = f"{path}/../examples/explosion.wav"
            music_path = f"{path}/../examples/music.mp3"

            if os.path.exists(sfx_path):
                self.audio_manager.load_sound(self.sfx_name, sfx_path)
                print("Loaded explosion.wav")
            else:
                self.create_placeholder_sound(self.sfx_name, duration=1.0, freq=440)

            if os.path.exists(music_path):
                self.audio_manager.load_sound(self.music_name, music_path)
                print("Loaded music.mp3")
            else:
                self.create_placeholder_sound(self.music_name, duration=5.0, freq=523)

        except Exception as e:
            print(f"Audio loading error: {e}")
            self.create_placeholder_sound(self.sfx_name, duration=1.0, freq=440)
            self.create_placeholder_sound(self.music_name, duration=5.0, freq=523)

    def create_placeholder_sound(self, name: str, duration: float = 1.0, freq: float = 440.0):
        """Generate a simple sine wave tone and load it as a sound."""
        try:
            import tempfile
            import wave
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = np.sin(2 * np.pi * freq * t)
            tone = (tone * 32767).astype(np.int16)
            stereo = np.column_stack((tone, tone))
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                with wave.open(tmp.name, 'wb') as wf:
                    wf.setnchannels(2)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(stereo.tobytes())
                self.audio_manager.load_sound(name, tmp.name)
                os.unlink(tmp.name)
            print(f"Created placeholder tone '{name}' ({freq}Hz, {duration}s)")
        except Exception as e:
            print(f"Failed to create placeholder: {e}")

    # ---------- UI Setup ----------
    def setup_ui(self):
        self.engine.set_global_theme(ThemeType.DEFAULT)

        # Title
        title = TextLabel(512, 30, "Audio Demo - LunaEngine 0.2.5", 36, pivot=(0.5, 0))
        self.add_ui_element(title)

        # Create main tabs container – adjust height to fit the window (720 - 90 for header = 630)
        self.main_tabs = Tabination(25, 80, 980, 610, 20)
        self.main_tabs.set_corner_radius((8, 8, 8, 8))

        # --- ADD TABS FIRST ---
        self.main_tabs.add_tab('Sound Effects')
        self.main_tabs.add_tab('Music')
        self.main_tabs.add_tab('Transitions & Curves')
        self.main_tabs.add_tab('Visualizer')
        self.main_tabs.add_tab('Monitor')
        self.main_tabs.add_tab('Settings')

        # Now fill each tab with content
        self.setup_sfx_tab()
        self.setup_music_tab()
        self.setup_curves_tab()
        self.setup_visualizer_tab()
        self.setup_monitor_tab()
        self.setup_settings_tab()

        self.add_ui_element(self.main_tabs)

        # FPS display
        self.fps_label = TextLabel(self.engine.width - 10, 10, "FPS: --", 14, (100, 255, 100), pivot=(1, 0))
        self.add_ui_element(self.fps_label)

    # ---------- SFX Tab ----------
    def setup_sfx_tab(self):
        tab = 'Sound Effects'
        # Create three named channels for SFX
        self.audio_manager.create_channel('sfx1', volume=0.8, balance=0.0)
        self.audio_manager.create_channel('sfx2', volume=0.8, balance=0.0)
        self.audio_manager.create_channel('sfx3', volume=0.8, balance=0.0)

        # Header
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Sound Effects", 24, (255, 255, 0)))

        y = 50
        # Channel 1 controls
        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Channel 1 (sfx1):", 18))
        b1 = Button(200, y, 100, 30, "Play")
        b1.set_on_click(lambda: self.play_sfx('sfx1', volume=0.8, pitch=1.0, balance=0.0))
        self.main_tabs.add_to_tab(tab, b1)

        b1_slow = Button(310, y, 100, 30, "Slow (0.5x)")
        b1_slow.set_on_click(lambda: self.play_sfx('sfx1', volume=0.8, pitch=0.5, balance=0.0))
        self.main_tabs.add_to_tab(tab, b1_slow)

        b1_fast = Button(420, y, 100, 30, "Fast (2.0x)")
        b1_fast.set_on_click(lambda: self.play_sfx('sfx1', volume=0.8, pitch=2.0, balance=0.0))
        self.main_tabs.add_to_tab(tab, b1_fast)

        y += 50
        # Channel 2 controls
        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Channel 2 (sfx2):", 18))
        b2 = Button(200, y, 100, 30, "Play")
        b2.set_on_click(lambda: self.play_sfx('sfx2', volume=0.6, pitch=1.0, balance=0.0))
        self.main_tabs.add_to_tab(tab, b2)

        b2_loop = Button(310, y, 100, 30, "Loop")
        b2_loop.set_on_click(lambda: self.play_sfx('sfx2', volume=0.6, pitch=1.0, balance=0.0, loop=True))
        self.main_tabs.add_to_tab(tab, b2_loop)

        y += 50
        # Balance controls for channel 3
        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Channel 3 (sfx3) - Balance:", 18))
        b_left = Button(200, y, 80, 30, "Left")
        b_left.set_on_click(lambda: self.play_sfx('sfx3', volume=0.8, pitch=1.0, balance=-0.8))
        self.main_tabs.add_to_tab(tab, b_left)

        b_center = Button(290, y, 80, 30, "Center")
        b_center.set_on_click(lambda: self.play_sfx('sfx3', volume=0.8, pitch=1.0, balance=0.0))
        self.main_tabs.add_to_tab(tab, b_center)

        b_right = Button(380, y, 80, 30, "Right")
        b_right.set_on_click(lambda: self.play_sfx('sfx3', volume=0.8, pitch=1.0, balance=0.8))
        self.main_tabs.add_to_tab(tab, b_right)

        y += 50
        # Stop all SFX
        stop_btn = Button(10, y, 120, 30, "Stop All SFX")
        stop_btn.set_on_click(lambda: self.stop_sfx_channels())
        self.main_tabs.add_to_tab(tab, stop_btn)

        y += 50
        self.sfx_status = TextLabel(10, y, "No SFX playing", 16, (200, 200, 200))
        self.main_tabs.add_to_tab(tab, self.sfx_status)

    # ---------- Music Tab ----------
    def setup_music_tab(self):
        tab = 'Music'
        # Header
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Music Controls", 24, (255, 255, 0)))

        # Get the existing music channel (already created by AudioManager)
        music_channel = self.audio_manager.get_channel('music')
        if music_channel is None:
            # Fallback: create it (should not happen)
            music_channel = self.audio_manager.create_channel('music', volume=0.7, balance=0.0, loop=True)
        else:
            # Ensure it's configured correctly
            music_channel.volume = 0.7
            music_channel.balance = 0.0
            music_channel.loop = True

        self.music_channel = music_channel
        self.music_volume = music_channel.volume
        self.music_pitch = music_channel.pitch
        self.music_balance = music_channel.balance

        y = 50
        # Play / Pause / Stop
        play_btn = Button(10, y, 100, 30, "Play")
        play_btn.set_on_click(lambda: self.play_music())
        self.main_tabs.add_to_tab(tab, play_btn)

        pause_btn = Button(120, y, 100, 30, "Pause")
        pause_btn.set_on_click(lambda: self.pause_music())
        self.main_tabs.add_to_tab(tab, pause_btn)

        resume_btn = Button(230, y, 100, 30, "Resume")
        resume_btn.set_on_click(lambda: self.resume_music())
        self.main_tabs.add_to_tab(tab, resume_btn)

        stop_btn = Button(340, y, 100, 30, "Stop")
        stop_btn.set_on_click(lambda: self.stop_music())
        self.main_tabs.add_to_tab(tab, stop_btn)

        y += 50
        # Volume slider
        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Volume:", 16))
        vol_slider = Slider(100, y, 200, 20, 0.0, 1.0, self.music_volume)
        vol_slider.on_value_changed = lambda v: self.set_music_volume(v)
        self.main_tabs.add_to_tab(tab, vol_slider)
        self.music_vol_label = TextLabel(310, y, f"{self.music_volume:.2f}", 14)
        self.main_tabs.add_to_tab(tab, self.music_vol_label)

        y += 40
        # Pitch slider
        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Pitch:", 16))
        pitch_slider = Slider(100, y, 200, 20, 0.5, 2.0, self.music_pitch)
        pitch_slider.on_value_changed = lambda v: self.set_music_pitch(v)
        self.main_tabs.add_to_tab(tab, pitch_slider)
        self.music_pitch_label = TextLabel(310, y, f"{self.music_pitch:.2f}x", 14)
        self.main_tabs.add_to_tab(tab, self.music_pitch_label)

        y += 40
        # Balance slider
        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Balance:", 16))
        bal_slider = Slider(100, y, 200, 20, -1.0, 1.0, self.music_balance)
        bal_slider.on_value_changed = lambda v: self.set_music_balance(v)
        self.main_tabs.add_to_tab(tab, bal_slider)
        self.music_bal_label = TextLabel(310, y, f"{self.music_balance:.2f}", 14)
        self.main_tabs.add_to_tab(tab, self.music_bal_label)

        y += 50
        self.music_status = TextLabel(10, y, "Stopped", 16, (255, 100, 100))
        self.main_tabs.add_to_tab(tab, self.music_status)

        y += 30
        self.music_pos = TextLabel(10, y, "Position: 0.00s", 14, (200, 200, 200))
        self.main_tabs.add_to_tab(tab, self.music_pos)

    # ---------- Curves / Transitions Tab ----------
    def setup_curves_tab(self):
        tab = 'Transitions & Curves'
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Audio Curves & Transitions", 24, (255, 255, 0)))

        y = 50
        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Volume Curve (0→1→0.5 over 3s):", 16))
        btn_vol_curve = Button(300, y, 150, 30, "Apply to SFX1")
        btn_vol_curve.set_on_click(lambda: self.apply_volume_curve())
        self.main_tabs.add_to_tab(tab, btn_vol_curve)

        y += 40
        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Pitch Curve (0.5→2.0→1.0 over 2s):", 16))
        btn_pitch_curve = Button(320, y, 150, 30, "Apply to SFX2")
        btn_pitch_curve.set_on_click(lambda: self.apply_pitch_curve())
        self.main_tabs.add_to_tab(tab, btn_pitch_curve)

        y += 40
        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Balance Curve (L→R→Center over 2s):", 16))
        btn_bal_curve = Button(330, y, 150, 30, "Apply to SFX3")
        btn_bal_curve.set_on_click(lambda: self.apply_balance_curve())
        self.main_tabs.add_to_tab(tab, btn_bal_curve)

        y += 50
        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Combined: volume ↑ + pitch ↑ (2s)", 16))
        btn_combined = Button(280, y, 150, 30, "Apply to Music")
        btn_combined.set_on_click(lambda: self.apply_combined_curve())
        self.main_tabs.add_to_tab(tab, btn_combined)

        y += 50
        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Curve Duration:", 16))
        dur_slider = Slider(150, y, 200, 20, 0.5, 5.0, self.curve_duration)
        dur_slider.on_value_changed = lambda v: self.set_curve_duration(v)
        self.main_tabs.add_to_tab(tab, dur_slider)
        self.curve_dur_label = TextLabel(360, y, f"{self.curve_duration:.1f}s", 14)
        self.main_tabs.add_to_tab(tab, self.curve_dur_label)

    # ---------- Visualizer Tab ----------
    def setup_visualizer_tab(self):
        tab = 'Visualizer'
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Audio Visualizer", 24, (255, 255, 0)))

        from lunaengine.ui.elements import AudioVisualizer

        self.audio_visualizer = AudioVisualizer(
            x=20, y=50, width=600, height=200,
            style='bars',
            source=None,
            color_gradient=[(100, 0, 200), (0, 150, 255), (0, 255, 200), (100, 255, 100)]
        )
        self.main_tabs.add_to_tab(tab, self.audio_visualizer)

        controls_y = 270
        self.main_tabs.add_to_tab(tab, TextLabel(20, controls_y, "Style:", 16))
        style_dd = Dropdown(100, controls_y-10, 120, 30, ['Bars', 'Waveform', 'Circle', 'Spectrum'])
        style_dd.set_on_selection_changed(lambda i, v: self.audio_visualizer.set_style(v.lower()))
        self.main_tabs.add_to_tab(tab, style_dd)

        self.main_tabs.add_to_tab(tab, TextLabel(250, controls_y, "Source:", 16))
        src_dd = Dropdown(310, controls_y-10, 120, 30, ['Music', 'SFX1', 'SFX2', 'SFX3'])
        src_dd.set_on_selection_changed(lambda i, v: self.set_visualizer_source(v.lower()))
        self.main_tabs.add_to_tab(tab, src_dd)

        controls_y += 40
        self.main_tabs.add_to_tab(tab, TextLabel(20, controls_y, "Sensitivity:", 16))
        sens_slider = Slider(120, controls_y, 150, 20, 0.5, 3.0, 1.5)
        sens_slider.on_value_changed = lambda v: self.audio_visualizer.set_sensitivity(v)
        self.main_tabs.add_to_tab(tab, sens_slider)

        self.main_tabs.add_to_tab(tab, TextLabel(300, controls_y, "Smoothing:", 16))
        smooth_slider = Slider(390, controls_y, 150, 20, 0.1, 0.9, 0.7)
        smooth_slider.on_value_changed = lambda v: self.audio_visualizer.set_smoothing(v)
        self.main_tabs.add_to_tab(tab, smooth_slider)

    # ---------- Monitor Tab ----------
    def setup_monitor_tab(self):
        tab = 'Monitor'
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Audio Monitor", 24, (255, 255, 0)))

        self.main_tabs.add_to_tab(tab, TextLabel(10, 50, "Active Channels:", 16, (200, 200, 255)))
        self.channel_list_label = TextLabel(10, 75, "None", 14, (200, 200, 200))
        self.main_tabs.add_to_tab(tab, self.channel_list_label)

        self.main_tabs.add_to_tab(tab, TextLabel(10, 120, "Event Log:", 16, (200, 200, 255)))
        self.event_log_labels = []
        for i in range(8):
            lbl = TextLabel(10, 140 + i*22, "", 12, (200, 200, 200))
            self.event_log_labels.append(lbl)
            self.main_tabs.add_to_tab(tab, lbl)

        clear_btn = Button(10, 320, 100, 25, "Clear Log")
        clear_btn.set_on_click(lambda: self.clear_event_log())
        self.main_tabs.add_to_tab(tab, clear_btn)

    # ---------- Settings Tab ----------
    def setup_settings_tab(self):
        tab = 'Settings'
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Audio Settings", 24, (255, 255, 0)))

        self.main_tabs.add_to_tab(tab, TextLabel(10, 50, "Audio Output Device:", 16, (200, 200, 255)))
        devices = self.audio_manager.list_devices()
        if not devices:
            devices = ["default"]
        self.device_dropdown = Dropdown(10, 75, 300, 30, devices)
        self.device_dropdown.set_on_selection_changed(lambda i, v: self.change_device(v))
        self.main_tabs.add_to_tab(tab, self.device_dropdown)

        self.device_status = TextLabel(10, 120, f"Current: {devices[0] if devices else 'default'}", 14, (200, 200, 200))
        self.main_tabs.add_to_tab(tab, self.device_status)

        self.main_tabs.add_to_tab(tab, TextLabel(10, 170, "Master Volume:", 16, (200, 200, 255)))
        master_slider = Slider(150, 165, 200, 20, 0.0, 1.0, 1.0)
        master_slider.on_value_changed = lambda v: self.set_master_volume(v)
        self.main_tabs.add_to_tab(tab, master_slider)

        reload_btn = Button(10, 210, 150, 30, "Reload Sounds")
        reload_btn.set_on_click(lambda: self.reload_sounds())
        self.main_tabs.add_to_tab(tab, reload_btn)

    # ---------- Audio Control Methods ----------
    def play_sfx(self, channel_name, volume=1.0, pitch=1.0, balance=0.0, loop=False):
        ch = self.audio_manager.get_channel(channel_name)
        if not ch:
            self.add_event(f"Channel {channel_name} not found")
            return
        ch.volume = volume
        ch.pitch = pitch
        ch.balance = balance
        if ch.play(self.sfx_name, loop=loop):
            self.add_event(f"SFX on {channel_name}: vol={volume:.2f}, pitch={pitch:.2f}, bal={balance:.2f}")
            self.update_sfx_status()
        else:
            self.add_event(f"Failed to play on {channel_name}")

    def stop_sfx_channels(self):
        for name in ['sfx1', 'sfx2', 'sfx3']:
            ch = self.audio_manager.get_channel(name)
            if ch:
                ch.stop()
        self.add_event("All SFX stopped")
        self.update_sfx_status()

    def update_sfx_status(self):
        active = []
        for name in ['sfx1', 'sfx2', 'sfx3']:
            ch = self.audio_manager.get_channel(name)
            if ch and ch.is_playing():
                active.append(name)
        if active:
            self.sfx_status.set_text(f"Playing: {', '.join(active)}")
        else:
            self.sfx_status.set_text("No SFX playing")

    def play_music(self):
        ch = self.music_channel
        if ch is None:
            ch = self.audio_manager.get_channel('music')
            if ch is None:
                ch = self.audio_manager.create_channel('music', volume=self.music_volume, balance=self.music_balance, loop=True)
                self.music_channel = ch
        if ch.play(self.music_name, loop=True):
            self.music_status.set_text("Playing")
            self.music_status.color = (100, 255, 100)
            self.add_event("Music started")
        else:
            self.add_event("Failed to start music")

    def pause_music(self):
        ch = self.music_channel
        if ch and ch.is_playing():
            ch.pause()
            self.music_status.set_text("Paused")
            self.music_status.color = (255, 255, 100)
            self.add_event("Music paused")

    def resume_music(self):
        ch = self.music_channel
        if ch and ch.is_paused():
            ch.resume()
            self.music_status.set_text("Playing")
            self.music_status.color = (100, 255, 100)
            self.add_event("Music resumed")

    def stop_music(self):
        ch = self.music_channel
        if ch:
            ch.stop()
            self.music_status.set_text("Stopped")
            self.music_status.color = (255, 100, 100)
            self.add_event("Music stopped")

    def set_music_volume(self, vol):
        self.music_volume = vol
        self.music_vol_label.set_text(f"{vol:.2f}")
        ch = self.music_channel
        if ch:
            ch.set_volume(vol)

    def set_music_pitch(self, pitch):
        self.music_pitch = pitch
        self.music_pitch_label.set_text(f"{pitch:.2f}x")
        ch = self.music_channel
        if ch:
            ch.set_pitch(pitch)

    def set_music_balance(self, bal):
        self.music_balance = bal
        self.music_bal_label.set_text(f"{bal:.2f}")
        ch = self.music_channel
        if ch:
            ch.set_balance(bal)

    def set_curve_duration(self, dur):
        self.curve_duration = dur
        self.curve_dur_label.set_text(f"{dur:.1f}s")

    # Curve applications
    def apply_volume_curve(self):
        ch = self.audio_manager.get_channel('sfx1')
        if not ch or not ch.is_playing():
            self.add_event("SFX1 not playing, cannot apply curve")
            return
        dur = self.curve_duration
        keyframes = [(0.0, 0.0), (dur*0.5, 1.0), (dur, 0.5)]
        curve = AudioCurve('volume', keyframes, interpolation='smoothstep')
        ch.apply_curve(curve)
        self.add_event(f"Volume curve applied to sfx1 ({dur}s)")

    def apply_pitch_curve(self):
        ch = self.audio_manager.get_channel('sfx2')
        if not ch or not ch.is_playing():
            self.add_event("SFX2 not playing, cannot apply curve")
            return
        dur = self.curve_duration
        keyframes = [(0.0, 0.5), (dur*0.5, 2.0), (dur, 1.0)]
        curve = AudioCurve('pitch', keyframes, interpolation='smoothstep')
        ch.apply_curve(curve)
        self.add_event(f"Pitch curve applied to sfx2 ({dur}s)")

    def apply_balance_curve(self):
        ch = self.audio_manager.get_channel('sfx3')
        if not ch or not ch.is_playing():
            self.add_event("SFX3 not playing, cannot apply curve")
            return
        dur = self.curve_duration
        keyframes = [(0.0, -0.8), (dur*0.5, 0.8), (dur, 0.0)]
        curve = AudioCurve('balance', keyframes, interpolation='smoothstep')
        ch.apply_curve(curve)
        self.add_event(f"Balance curve applied to sfx3 ({dur}s)")

    def apply_combined_curve(self):
        ch = self.music_channel
        if not ch or not ch.is_playing():
            self.add_event("Music not playing, cannot apply combined curve")
            return
        dur = self.curve_duration
        vol_curve = AudioCurve('volume', [(0.0, 0.5), (dur, 1.0)], 'smoothstep')
        pitch_curve = AudioCurve('pitch', [(0.0, 1.0), (dur, 1.5)], 'smoothstep')
        ch.apply_curve(vol_curve)
        ch.apply_curve(pitch_curve)
        self.add_event(f"Combined volume+pitch curve on music ({dur}s)")

    def set_visualizer_source(self, source_name):
        if source_name == 'music':
            ch = self.music_channel
        else:
            ch = self.audio_manager.get_channel(source_name)
        if ch and ch.is_playing():
            self.audio_visualizer.set_source(ch)
        else:
            self.audio_visualizer.set_source(None)

    # ---------- Settings ----------
    def change_device(self, device_name):
        if self.audio_manager.set_device(device_name):
            self.device_status.set_text(f"Current: {device_name}")
            self.add_event(f"Device changed to {device_name}")
        else:
            self.add_event(f"Failed to switch to {device_name}")

    def set_master_volume(self, vol):
        for ch in self.audio_manager.channels.values():
            ch.set_volume(ch.volume * vol)
        self.add_event(f"Master volume set to {vol:.2f}")

    def reload_sounds(self):
        self.add_event("Reloading sounds...")
        self.load_audio()
        self.add_event("Sounds reloaded")

    # ---------- Event Logging ----------
    def on_audio_event(self, manager, **kwargs):
        event = kwargs.get('event', None)
        if event:
            self.add_event(f"AudioEvent: {event}")
        else:
            self.add_event("Audio event occurred")

    def add_event(self, text):
        self.event_log.append(text)
        if len(self.event_log) > 8:
            self.event_log.pop(0)
        self.update_event_log()

    def update_event_log(self):
        for i, lbl in enumerate(self.event_log_labels):
            if i < len(self.event_log):
                lbl.set_text(self.event_log[i])
            else:
                lbl.set_text("")

    def clear_event_log(self):
        self.event_log.clear()
        for lbl in self.event_log_labels:
            lbl.set_text("")

    # ---------- Update ----------
    def update(self, dt):
        self.audio_manager.update(dt)

        # Update music position
        ch = self.music_channel
        if ch and ch.is_playing():
            pos = ch.get_position()
            self.music_pos.set_text(f"Position: {pos:.2f}s")
        else:
            self.music_pos.set_text("Position: 0.00s")

        fps_stats = self.engine.get_fps_stats()
        self.fps_label.set_text(f"FPS: {fps_stats['current_fps']:.1f}")

        active = [name for name, ch in self.audio_manager.channels.items() if ch.is_playing()]
        if active:
            self.channel_list_label.set_text(", ".join(active))
        else:
            self.channel_list_label.set_text("None")

    # ---------- Keyboard ----------
    def handle_key(self, key):
        if key == pygame.K_1:
            self.play_sfx('sfx1', volume=0.8, pitch=1.0)
        elif key == pygame.K_2:
            self.play_sfx('sfx2', volume=0.7, pitch=1.0)
        elif key == pygame.K_3:
            self.play_sfx('sfx3', volume=0.8, pitch=1.0, balance=-0.5)
        elif key == pygame.K_4:
            self.play_music()
        elif key == pygame.K_5:
            self.pause_music()
        elif key == pygame.K_6:
            self.resume_music()
        elif key == pygame.K_7:
            self.stop_music()
        elif key == pygame.K_ESCAPE:
            self.engine.set_scene("MainMenu")

    # ---------- Render ----------
    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        renderer.draw_rect(0, 0, self.engine.width, 80, ThemeManager.get_color('background2'))
        # UI elements rendered automatically


# ---------- Main ----------
def main():
    engine = LunaEngine("Audio Demo - LunaEngine", 1024, 720, debug=True)
    engine.fps = 60

    engine.add_scene("AudioDemo", AudioDemoScene)
    engine.set_scene("AudioDemo")

    print("\n=== Audio Demo Controls ===")
    print("1-3: Play SFX on channels 1-3")
    print("4: Play music")
    print("5: Pause music")
    print("6: Resume music")
    print("7: Stop music")
    print("ESC: Exit demo")
    print("Use UI tabs for full control\n")

    engine.run()


if __name__ == "__main__":
    main()