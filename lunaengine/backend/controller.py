"""
lunaengine/backend/controller.py

Advanced game controller support with hot‑plug, multiple controllers,
gyro, touchpad, mouse emulation, and input source detection.
"""

import pygame
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
from dataclasses import dataclass, field
import time
import math

# ----------------------------------------------------------------------
# Enums and constants
# ----------------------------------------------------------------------

class ControllerType(Enum):
    XBOX = auto()
    PLAYSTATION = auto()
    NINTENDO_SWITCH = auto()
    GENERIC = auto()

class ConnectionType(Enum):
    USB = auto()
    BLUETOOTH = auto()
    WIRELESS_DONGLE = auto()
    UNKNOWN = auto()

class JButton(Enum):
    A = auto()
    B = auto()
    X = auto()
    Y = auto()
    BACK = auto()
    GUIDE = auto()
    START = auto()
    LEFT_STICK = auto()
    RIGHT_STICK = auto()
    LEFT_BUMPER = auto()
    RIGHT_BUMPER = auto()
    DPAD_UP = auto()
    DPAD_DOWN = auto()
    DPAD_LEFT = auto()
    DPAD_RIGHT = auto()
    # PlayStation aliases
    CROSS = A
    CIRCLE = B
    SQUARE = X
    TRIANGLE = Y
    SHARE = BACK
    OPTIONS = START
    TOUCHPAD = auto()

class Axis(Enum):
    LEFT_X = auto()
    LEFT_Y = auto()
    RIGHT_X = auto()
    RIGHT_Y = auto()
    LEFT_TRIGGER = auto()
    RIGHT_TRIGGER = auto()
    GYRO_X = auto()
    GYRO_Y = auto()
    GYRO_Z = auto()
    ACCEL_X = auto()
    ACCEL_Y = auto()
    ACCEL_Z = auto()

# ----------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------

@dataclass
class TouchPoint:
    x: float          # normalized 0..1
    y: float
    pressure: float
    finger_id: int

@dataclass
class ControllerState:
    buttons: Dict[JButton, bool] = field(default_factory=dict)
    axes: Dict[Axis, float] = field(default_factory=dict)
    hat: Tuple[float, float] = (0.0, 0.0)
    touch_points: List[TouchPoint] = field(default_factory=list)
    gyro: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    accelerometer: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    last_button_time: Dict[JButton, float] = field(default_factory=dict)

# ----------------------------------------------------------------------
# Individual Controller
# ----------------------------------------------------------------------

class Controller:
    _XBOX_IDS = {"xbox", "x-box", "microsoft", "xinput"}
    _PS_IDS = {"playstation", "ps4", "ps5", "sony", "dualshock", "dualsense", "wireless controller"}
    _NINTENDO_IDS = {"nintendo", "switch", "pro controller"}

    def __init__(self, joystick_id: int, manager: "ControllerManager"):
        self.joystick_id = joystick_id
        self.manager = manager
        self._joystick = None
        self.name = ""
        self.guid = ""
        self.type = ControllerType.GENERIC
        self.connection = ConnectionType.UNKNOWN
        self.num_axes = 0
        self.num_buttons = 0
        self.num_hats = 0

        self._button_map: Dict[JButton, int] = {}
        self._axis_map: Dict[Axis, int] = {}
        self._hat_index = 0
        self._axis_invert: Dict[Axis, bool] = {}
        self.deadzone = 0.15

        self.state = ControllerState()

        self._touch_joystick: Optional[pygame.joystick.Joystick] = None
        self._has_rumble = False

        # Mouse emulation
        self.mouse_emulation_enabled = False
        self._mouse_speed = 5.0
        self._mouse_deadzone = 0.2
        self._mouse_button_map = {
            JButton.A: 1,      # left click
            JButton.B: 3,      # right click
            JButton.X: 2,      # middle click
            JButton.LEFT_BUMPER: 4,
            JButton.RIGHT_BUMPER: 5,
        }

        self._open()

    def _open(self):
        try:
            self._joystick = pygame.joystick.Joystick(self.joystick_id)
            self._joystick.init()
        except pygame.error as e:
            raise RuntimeError(f"Cannot open joystick {self.joystick_id}: {e}")

        self.name = self._joystick.get_name()
        self.guid = self._joystick.get_guid()
        self.num_axes = self._joystick.get_numaxes()
        self.num_buttons = self._joystick.get_numbuttons()
        self.num_hats = self._joystick.get_numhats()

        self._detect_type()
        self._build_default_maps()
        self._detect_touchpad()
        self._check_rumble()
        self._guess_connection_type()

    def _detect_type(self):
        name_lower = self.name.lower()
        if any(x in name_lower for x in self._XBOX_IDS):
            self.type = ControllerType.XBOX
        elif any(x in name_lower for x in self._PS_IDS):
            self.type = ControllerType.PLAYSTATION
        elif any(x in name_lower for x in self._NINTENDO_IDS):
            self.type = ControllerType.NINTENDO_SWITCH
        else:
            self.type = ControllerType.GENERIC

    def _guess_connection_type(self):
        name_lower = self.name.lower()
        
        # Bluetooth keywords
        if any(x in name_lower for x in ["bluetooth", "bt", "wireless"]):
            # Differentiate for known brands
            if "sony" in name_lower and "wireless" in name_lower:
                # PS4/PS5: short name "Wireless Controller" → Bluetooth
                if len(self.name.split()) <= 3:
                    self.connection = ConnectionType.BLUETOOTH
                    return
            if "xbox" in name_lower:
                if "bluetooth" in name_lower:
                    self.connection = ConnectionType.BLUETOOTH
                    return
                elif "wireless" in name_lower:
                    # Could be proprietary wireless dongle
                    self.connection = ConnectionType.WIRELESS_DONGLE
                    return
            # Default for "wireless" without other hints
            if "wireless" in name_lower:
                self.connection = ConnectionType.WIRELESS_DONGLE
                return
            self.connection = ConnectionType.BLUETOOTH
            return

        # USB keywords
        if any(x in name_lower for x in ["usb", "wired", "cable"]):
            self.connection = ConnectionType.USB
            return

        self.connection = ConnectionType.UNKNOWN

    def _build_default_maps(self):
        """Build button and axis maps based on detected controller type."""
        if self.type == ControllerType.PLAYSTATION:
            self._build_playstation_map()
        elif self.type == ControllerType.XBOX:
            self._build_xbox_map()
        elif self.type == ControllerType.NINTENDO_SWITCH:
            self._build_switch_map()
        else:
            self._build_generic_map()

    def _build_xbox_map(self):
        # Xbox 360/One common layout (SDL mapping)
        self._button_map = {
            JButton.A: 0,
            JButton.B: 1,
            JButton.X: 2,
            JButton.Y: 3,
            JButton.LEFT_BUMPER: 4,
            JButton.RIGHT_BUMPER: 5,
            JButton.BACK: 6,
            JButton.START: 7,
            JButton.GUIDE: 8,
            JButton.LEFT_STICK: 9,
            JButton.RIGHT_STICK: 10,
        }
        self._axis_map = {
            Axis.LEFT_X: 0,
            Axis.LEFT_Y: 1,
            Axis.RIGHT_X: 2,
            Axis.RIGHT_Y: 3,
            Axis.LEFT_TRIGGER: 4,
            Axis.RIGHT_TRIGGER: 5,
        }
        self._axis_invert = {Axis.LEFT_Y: True, Axis.RIGHT_Y: True}

    def _build_playstation_map(self):
        # DualShock 4 / DualSense – exact mapping from ps4_keys.json
        self._button_map = {
            JButton.A: 0,          # Cross
            JButton.B: 1,          # Circle
            JButton.X: 2,          # Square
            JButton.Y: 3,          # Triangle
            JButton.BACK: 4,       # Share
            JButton.GUIDE: 5,      # PS button
            JButton.START: 6,      # Options
            JButton.LEFT_STICK: 7, # L3
            JButton.RIGHT_STICK: 8,# R3
            JButton.LEFT_BUMPER: 9,# L1
            JButton.RIGHT_BUMPER: 10,# R1
            JButton.DPAD_UP: 11,
            JButton.DPAD_DOWN: 12,
            JButton.DPAD_LEFT: 13,
            JButton.DPAD_RIGHT: 14,
            JButton.TOUCHPAD: 15,   # Touchpad click (if present)
        }
        # Axis mapping (raw values, no inversion)
        self._axis_map = {
            Axis.LEFT_X: 0,
            Axis.LEFT_Y: 1,
            Axis.RIGHT_X: 2,
            Axis.RIGHT_Y: 3,
            Axis.LEFT_TRIGGER: 4,   # L2 analog: -1 = released, 1 = fully pressed
            Axis.RIGHT_TRIGGER: 5,  # R2 analog
            # Gyro/accelerometer axes – often start at 6
            Axis.GYRO_X: 6,
            Axis.GYRO_Y: 7,
            Axis.GYRO_Z: 8,
        }
        self._axis_invert = {Axis.LEFT_Y: True, Axis.RIGHT_Y: True}  # Keep empty, or explicitly set False for clarity

    def _build_switch_map(self):
        # Nintendo Switch Pro Controller (SDL mapping)
        self._button_map = {
            JButton.A: 0,
            JButton.B: 1,
            JButton.X: 2,
            JButton.Y: 3,
            JButton.LEFT_BUMPER: 4,    # L
            JButton.RIGHT_BUMPER: 5,   # R
            JButton.BACK: 6,            # Minus
            JButton.START: 7,           # Plus
            JButton.LEFT_STICK: 8,      # L3
            JButton.RIGHT_STICK: 9,     # R3
            JButton.GUIDE: 10,          # Home
            # ZL and ZR are analog triggers, no digital button mapping here
        }
        self._axis_map = {
            Axis.LEFT_X: 0,
            Axis.LEFT_Y: 1,
            Axis.RIGHT_X: 2,
            Axis.RIGHT_Y: 3,
            Axis.LEFT_TRIGGER: 4,       # ZL analog
            Axis.RIGHT_TRIGGER: 5,      # ZR analog
        }
        self._axis_invert = {Axis.LEFT_Y: True, Axis.RIGHT_Y: True}

    def _build_generic_map(self):
        # Fallback: assume Xbox-like ordering
        self._button_map = {}
        if self.num_buttons >= 4:
            self._button_map[JButton.A] = 0
            self._button_map[JButton.B] = 1
            self._button_map[JButton.X] = 2
            self._button_map[JButton.Y] = 3
        if self.num_buttons >= 6:
            self._button_map[JButton.LEFT_BUMPER] = 4
            self._button_map[JButton.RIGHT_BUMPER] = 5
        if self.num_buttons >= 8:
            self._button_map[JButton.BACK] = 6
            self._button_map[JButton.START] = 7
        if self.num_buttons >= 9:
            self._button_map[JButton.GUIDE] = 8
        if self.num_buttons >= 11:
            self._button_map[JButton.LEFT_STICK] = 9
            self._button_map[JButton.RIGHT_STICK] = 10

        self._axis_map = {}
        if self.num_axes >= 2:
            self._axis_map[Axis.LEFT_X] = 0
            self._axis_map[Axis.LEFT_Y] = 1
            self._axis_invert[Axis.LEFT_Y] = True
        if self.num_axes >= 4:
            self._axis_map[Axis.RIGHT_X] = 2
            self._axis_map[Axis.RIGHT_Y] = 3
            self._axis_invert[Axis.RIGHT_Y] = True
        if self.num_axes >= 6:
            self._axis_map[Axis.LEFT_TRIGGER] = 4
            self._axis_map[Axis.RIGHT_TRIGGER] = 5
        if self.num_axes >= 9:
            self._axis_map[Axis.GYRO_X] = 6
            self._axis_map[Axis.GYRO_Y] = 7
            self._axis_map[Axis.GYRO_Z] = 8

    def _detect_touchpad(self):
        """For PlayStation controllers, try to find a second joystick that handles touchpad."""
        if self.type != ControllerType.PLAYSTATION:
            return
        # Look for another joystick with "touchpad" in name
        for i in range(pygame.joystick.get_count()):
            if i == self.joystick_id:
                continue
            joy = pygame.joystick.Joystick(i)
            if "touchpad" in joy.get_name().lower():
                try:
                    joy.init()
                    self._touch_joystick = joy
                except pygame.error:
                    pass
                break

    def _check_rumble(self):
        try:
            self._has_rumble = self._joystick.rumble(0, 0, 0) is not None
        except AttributeError:
            self._has_rumble = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, events: List[pygame.event.Event]):
        for event in events:
            if event.type == pygame.JOYAXISMOTION and event.joy == self.joystick_id:
                self._handle_axis_event(event)
            elif event.type == pygame.JOYBUTTONDOWN and event.joy == self.joystick_id:
                self._handle_button_event(event, True)
            elif event.type == pygame.JOYBUTTONUP and event.joy == self.joystick_id:
                self._handle_button_event(event, False)
            elif event.type == pygame.JOYHATMOTION and event.joy == self.joystick_id:
                self._handle_hat_event(event)

        self._poll_axes()
        self._apply_deadzone()

        if self.mouse_emulation_enabled:
            self._update_mouse_emulation()

    def _handle_axis_event(self, event):
        axis_idx = event.axis
        value = event.value
        for logical, idx in self._axis_map.items():
            if idx == axis_idx:
                if self._axis_invert.get(logical, False):
                    value = -value
                self.state.axes[logical] = value
                break

    def _handle_button_event(self, event, pressed):
        button_idx = event.button
        for logical, idx in self._button_map.items():
            if idx == button_idx:
                self.state.buttons[logical] = pressed
                if pressed:
                    self.state.last_button_time[logical] = time.time()
                break

    def _handle_hat_event(self, event):
        self.state.hat = event.value

    def _poll_axes(self):
        if not self._joystick:
            return
        for logical, idx in self._axis_map.items():
            try:
                raw = self._joystick.get_axis(idx)
            except pygame.error:
                continue
            if self._axis_invert.get(logical, False):
                raw = -raw
            self.state.axes[logical] = raw

    def _apply_deadzone(self):
        for axis in [Axis.LEFT_X, Axis.LEFT_Y, Axis.RIGHT_X, Axis.RIGHT_Y,
                     Axis.LEFT_TRIGGER, Axis.RIGHT_TRIGGER]:
            if axis in self.state.axes:
                val = self.state.axes[axis]
                if abs(val) < self.deadzone:
                    self.state.axes[axis] = 0.0

    def _update_mouse_emulation(self):
        if not self.manager or not self.manager.engine:
            return
        lx = self.state.axes.get(Axis.LEFT_X, 0.0)
        ly = self.state.axes.get(Axis.LEFT_Y, 0.0)

        if abs(lx) < self._mouse_deadzone:
            lx = 0.0
        if abs(ly) < self._mouse_deadzone:
            ly = 0.0

        if lx != 0.0 or ly != 0.0:
            dx = int(lx * self._mouse_speed)
            dy = int(ly * self._mouse_speed)
            pygame.mouse.set_pos(pygame.mouse.get_pos()[0] + dx,
                                 pygame.mouse.get_pos()[1] + dy)

        # Mouse click simulation is handled by the engine via manager's input detection

    def remap_button(self, logical: JButton, raw_index: int):
        self._button_map[logical] = raw_index

    def remap_axis(self, logical: Axis, raw_index: int, invert: bool = False):
        self._axis_map[logical] = raw_index
        self._axis_invert[logical] = invert

    def set_deadzone(self, value: float):
        self.deadzone = max(0.0, min(1.0, value))

    def rumble(self, low: float, high: float, duration_ms: int) -> bool:
        if not self._has_rumble:
            return False
        try:
            return self._joystick.rumble(low, high, duration_ms)
        except pygame.error:
            return False

    def stop_rumble(self):
        if self._has_rumble:
            try:
                self._joystick.stop_rumble()
            except (AttributeError, pygame.error):
                pass

    def get_guid(self) -> str:
        return self.guid

    def get_name(self) -> str:
        return self.name

    def is_connected(self) -> bool:
        return self._joystick is not None and self._joystick.get_init()

    def close(self):
        if self._joystick:
            self._joystick.quit()
            self._joystick = None
        if self._touch_joystick:
            self._touch_joystick.quit()
            self._touch_joystick = None

    def get_button_pressed(self, button: JButton) -> bool:
        return self.state.buttons.get(button, False)

    def get_axis(self, axis: Axis) -> float:
        return self.state.axes.get(axis, 0.0)

    def get_hat(self) -> Tuple[float, float]:
        return self.state.hat

    def get_touch_points(self) -> List[TouchPoint]:
        """Read touch points from the touchpad joystick (if any)."""
        if not self._touch_joystick:
            return []
        points = []
        # This is a placeholder; actual touchpad reading depends on OS and driver.
        # Some systems report touch as multiple axes or buttons.
        # For now, return empty list.
        return points

    def __repr__(self):
        return f"<Controller id={self.joystick_id} name='{self.name}' type={self.type.name}>"


# ----------------------------------------------------------------------
# ControllerManager (manages all controllers and input source detection)
# ----------------------------------------------------------------------

class ControllerManager:
    """
    Manages multiple controllers, detects hot‑plug events, and tracks
    which input device (keyboard/mouse vs. controller) was last used.
    """

    def __init__(self, engine: Optional["LunaEngine"] = None):
        self.engine = engine
        self.controllers: Dict[int, Controller] = {}  # key: device index
        self._last_joystick_count = 0

        # Callbacks
        self.on_connect: List[Callable[[Controller], None]] = []
        self.on_disconnect: List[Callable[[Controller], None]] = []

        # Mouse emulation can be toggled globally
        self.global_mouse_emulation = False

        # Input source detection
        self.last_input_time = {
            "keyboard": 0.0,
            "mouse": 0.0,
            "controller": 0.0,
        }
        self.active_source = "keyboard"  # 'keyboard', 'mouse', 'controller'

        # Initial scan
        self.scan_controllers()

    def scan_controllers(self):
        count = pygame.joystick.get_count()
        for i in range(count):
            if i not in self.controllers:
                try:
                    ctrl = Controller(i, self)
                    self.controllers[i] = ctrl
                    for cb in self.on_connect:
                        cb(ctrl)
                except Exception as e:
                    print(f"Failed to init controller {i}: {e}")

    def handle_events(self, events: List[pygame.event.Event]):
        """
        Process device events and update controllers.
        Also tracks last input time for source detection.
        """
        now = time.time()

        for event in events:
            # Update last input time based on event type
            if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                self.last_input_time["keyboard"] = now
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN,
                                pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
                self.last_input_time["mouse"] = now
            elif event.type in (pygame.JOYAXISMOTION, pygame.JOYBUTTONDOWN,
                                pygame.JOYBUTTONUP, pygame.JOYHATMOTION):
                self.last_input_time["controller"] = now

            # Handle device connection/disconnection
            if event.type == pygame.JOYDEVICEADDED:
                idx = event.device_index
                if idx not in self.controllers:
                    try:
                        ctrl = Controller(idx, self)
                        self.controllers[idx] = ctrl
                        for cb in self.on_connect:
                            cb(ctrl)
                    except Exception as e:
                        print(f"Failed to init new controller {idx}: {e}")
            elif event.type == pygame.JOYDEVICEREMOVED:
                inst_id = event.instance_id
                to_remove = None
                for idx, ctrl in self.controllers.items():
                    if ctrl._joystick and ctrl._joystick.get_instance_id() == inst_id:
                        to_remove = idx
                        break
                if to_remove is not None:
                    ctrl = self.controllers.pop(to_remove)
                    for cb in self.on_disconnect:
                        cb(ctrl)
                    ctrl.close()

        # Update each controller
        for ctrl in self.controllers.values():
            ctrl.update(events)

        # Determine active source based on which had the most recent input
        # (with a small timeout to avoid flickering)
        latest = max(self.last_input_time.items(), key=lambda x: x[1])
        if latest[1] > 0 and (now - latest[1]) < 0.5:  # within last 0.5 seconds
            self.active_source = latest[0]

    def get_active_source(self) -> str:
        """Return 'keyboard', 'mouse', or 'controller'."""
        return self.active_source

    def is_using_controller(self) -> bool:
        """Convenience: whether a controller was used recently."""
        return self.active_source == "controller"

    def get_controller(self, index: int) -> Optional[Controller]:
        return self.controllers.get(index)

    def get_controllers_by_type(self, ctype: ControllerType) -> List[Controller]:
        return [c for c in self.controllers.values() if c.type == ctype]

    def get_all_controllers(self) -> List[Controller]:
        return list(self.controllers.values())

    def get_first_connected(self) -> Optional[Controller]:
        """Return the first (lowest index) connected controller."""
        if self.controllers:
            return next(iter(self.controllers.values()))
        return None

    def set_mouse_emulation(self, enabled: bool, controller_index: Optional[int] = None):
        if controller_index is None:
            self.global_mouse_emulation = enabled
            for ctrl in self.controllers.values():
                ctrl.mouse_emulation_enabled = enabled
        else:
            ctrl = self.controllers.get(controller_index)
            if ctrl:
                ctrl.mouse_emulation_enabled = enabled

    def shutdown(self):
        for ctrl in list(self.controllers.values()):
            ctrl.close()
        self.controllers.clear()

    def __len__(self) -> int:
        return len(self.controllers)