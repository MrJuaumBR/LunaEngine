"""
bones_demo.py - Interactive Skeletal Animation Demo for LunaEngine

ENGINE PATH:
lunaengine -> examples -> bones_demo.py

DESCRIPTION:
This demo showcases the bones system with interactive skeletons that can be
manipulated, animated, and customized. Features different animal skeletons
with bone manipulation controls.

CONTROLS:
- Use TAB to switch between skeletons
- Click and drag to move the skeleton
- Use sliders to adjust bone angles
- Click animation buttons to see different movements
- Use color pickers to customize bone colors
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
from lunaengine.ui.tween import Tween, EasingType, AnimationHandler
from lunaengine.misc.bones import Joint, Bone, Skeleton, HumanBones, DogBones, CatBones, HorseBones
import pygame as pg
import math
from typing import Dict, List, Tuple, Optional

class BonesDemo(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.skeletons = {}
        self.current_skeleton_type = "Human"
        self.current_skeleton: Optional[Skeleton] = None
        self.skeleton_position = [512, 384]  # Center of screen
        self.is_dragging = False
        self.drag_offset = [0, 0]
        
        # Animation states
        self.animation_handler = AnimationHandler(engine)
        self.active_animation = None
        self.animation_speed = 1.0
        
        # Demo state
        self.demo_state = {
            'bone_color': (255, 255, 255),
            'show_joints': True,
            'bone_width': 3,
            'current_bone': None,
        }
        
        # Setup skeletons
        self.setup_skeletons()
        self.setup_ui()
    
    def on_enter(self, previous_scene: str = None):
        print("=== LunaEngine Bones Demo ===")
        print("Explore the skeletal animation system!")
        print("Controls:")
        print("- TAB: Switch between skeletons (Human, Dog, Cat, Horse)")
        print("- Click and drag: Move the current skeleton")
        print("- Use sliders: Adjust bone angles")
        print("- Animation buttons: Play different movements")
        print("- Color pickers: Change bone colors")
        print("- Switch: Toggle joint visibility")
        print("- Bone width slider: Adjust bone thickness")
        print("- Hover over UI elements for tooltips")
        
    def on_exit(self, next_scene: str = None):
        print("Exiting Bones Demo scene")
        self.animation_handler.cancel_all()
    
    def setup_skeletons(self):
        """Initialize all skeleton types"""
        center_x, center_y = 512, 384
        
        # Human skeleton
        self.skeletons['Human'] = HumanBones(center_x, center_y, scale=1.0)
        
        # Dog skeleton
        self.skeletons['Dog'] = DogBones(center_x, center_y, scale=1.0)
        
        # Cat skeleton
        self.skeletons['Cat'] = CatBones(center_x, center_y, scale=1.0)
        
        # Horse skeleton
        self.skeletons['Horse'] = HorseBones(center_x, center_y, scale=0.8)  # Smaller scale for horse
        
        # Set initial skeleton
        self.current_skeleton = self.skeletons['Human']
    
    def setup_ui(self):
        """Set up all UI controls"""
        self.engine.set_global_theme(ThemeType.DEFAULT)
        
        # --- TITLE AND INFO ---
        title = TextLabel(512, 20, "LunaEngine - Bones System Demo", 32, (255, 220, 100), root_point=(0.5, 0))
        self.add_ui_element(title)
        
        info_text = "TAB: Switch skeletons | Drag: Move skeleton | Sliders: Adjust angles"
        info_label = TextLabel(512, 50, info_text, 16, (200, 200, 255), root_point=(0.5, 0))
        self.add_ui_element(info_label)
        
        # --- SKELETON INFO DISPLAY ---
        self.skeleton_info = TextLabel(20, 80, "Current: Human Skeleton", 20, (100, 255, 100))
        self.add_ui_element(self.skeleton_info)
        
        # --- MAIN CONTROL PANEL (Left side) ---
        control_panel = UiFrame(20, 110, 300, 620)
        control_panel.set_background_color((30, 30, 50, 200))
        control_panel.set_border((100, 150, 255), 2)
        self.add_ui_element(control_panel)
        
        # Panel title
        panel_title = TextLabel(5, 5, "Skeleton Controls", 22, (255, 200, 100))
        control_panel.add_child(panel_title)
        
        y_offset = 40
        
        # --- Skeleton Selection Buttons ---
        selection_label = TextLabel(10, y_offset, "Select Skeleton:", 16, (200, 200, 255))
        control_panel.add_child(selection_label)
        y_offset += 25
        
        # Create skeleton selection buttons in a grid
        skeleton_types = ['Human', 'Dog', 'Cat', 'Horse']
        for i, skeleton_type in enumerate(skeleton_types):
            btn_x = 10 + (i % 2) * 140
            btn_y = y_offset + (i // 2) * 35
            btn = Button(btn_x, btn_y, 130, 30, skeleton_type)
            btn.set_on_click(lambda st=skeleton_type: self.switch_skeleton(st))
            btn.set_simple_tooltip(f"Switch to {skeleton_type.lower()} skeleton")
            if skeleton_type == self.current_skeleton_type:
                btn.set_background_color((80, 120, 200))
            control_panel.add_child(btn)
        y_offset += 75
        
        # --- Bone Color Picker ---
        color_label = TextLabel(10, y_offset, "Bone Color:", 16, (200, 200, 255))
        control_panel.add_child(color_label)
        y_offset += 25
        
        # Color preset buttons
        color_presets = [
            ("White", (255, 255, 255)),
            ("Red", (255, 100, 100)),
            ("Green", (100, 255, 100)),
            ("Blue", (100, 150, 255)),
            ("Gold", (255, 215, 0)),
            ("Purple", (200, 100, 255)),
        ]
        
        for i, (name, color) in enumerate(color_presets):
            btn_x = 10 + (i % 3) * 95
            btn_y = y_offset + (i // 3) * 35
            btn = Button(btn_x, btn_y, 85, 30, name)
            btn.set_background_color(color)
            btn.set_on_click(lambda c=color: self.set_bone_color(c))
            btn.set_simple_tooltip(f"Set bone color to {name}")
            control_panel.add_child(btn)
        
        y_offset += 80
        
        # --- Visual Settings ---
        visual_label = TextLabel(10, y_offset, "Visual Settings:", 16, (200, 200, 255))
        control_panel.add_child(visual_label)
        y_offset += 25
        
        # Show joints switch
        switch_label = TextLabel(10, y_offset, "Show Joints:", 14)
        control_panel.add_child(switch_label)
        
        joint_switch = Switch(110, y_offset - 5, 50, 25)
        joint_switch.toggled = self.demo_state['show_joints']
        joint_switch.set_on_toggle(lambda s: self.toggle_joints(s))
        joint_switch.set_simple_tooltip("Toggle joint visibility (red dots)")
        control_panel.add_child(joint_switch)
        
        y_offset += 35
        
        # Bone width slider
        width_label = TextLabel(10, y_offset, "Bone Width:", 14)
        control_panel.add_child(width_label)
        
        width_slider = Slider(100, y_offset - 5, 150, 20, 1, 10, self.demo_state['bone_width'])
        width_slider.on_value_changed = lambda v: self.set_bone_width(v)
        width_slider.set_simple_tooltip("Adjust bone thickness")
        control_panel.add_child(width_slider)
        
        self.width_display = TextLabel(260, y_offset, f"{self.demo_state['bone_width']}", 14)
        control_panel.add_child(self.width_display)
        
        y_offset += 40
        
        # --- Animation Controls ---
        anim_label = TextLabel(10, y_offset, "Animations:", 16, (200, 200, 255))
        control_panel.add_child(anim_label)
        y_offset += 25
        
        # Animation buttons
        animations = [
            ("Idle", self.play_idle_animation),
            ("Walk", self.play_walk_animation),
            ("Jump", self.play_jump_animation),
            ("Attack", self.play_attack_animation),
            ("Dance", self.play_dance_animation),
        ]
        
        for i, (name, func) in enumerate(animations):
            btn_x = 10 + (i % 2) * 140
            btn_y = y_offset + (i // 2) * 35
            btn = Button(btn_x, btn_y, 130, 30, name)
            btn.set_on_click(func)
            btn.set_simple_tooltip(f"Play {name.lower()} animation")
            control_panel.add_child(btn)
        
        y_offset += 95
        
        # Animation speed control
        speed_label = TextLabel(10, y_offset, "Animation Speed:", 14)
        control_panel.add_child(speed_label)
        
        speed_slider = Slider(130, y_offset - 5, 120, 20, 0.1, 3.0, self.animation_speed)
        speed_slider.on_value_changed = lambda v: self.set_animation_speed(v)
        speed_slider.set_simple_tooltip("Adjust animation playback speed")
        control_panel.add_child(speed_slider)
        
        self.speed_display = TextLabel(260, y_offset, f"{self.animation_speed:.1f}x", 14)
        control_panel.add_child(self.speed_display)
        
        y_offset += 35
        
        # Stop animation button
        stop_btn = Button(10, y_offset, 280, 30, "Stop Animation")
        stop_btn.set_on_click(self.stop_animation)
        stop_btn.set_background_color((200, 100, 100))
        stop_btn.set_simple_tooltip("Stop current animation")
        control_panel.add_child(stop_btn)
        
        y_offset += 45
        
        # --- Bone Angle Controls (Right side panel) ---
        angle_panel = UiFrame(self.engine.width - 320, 110, 300, 400)
        angle_panel.set_background_color((30, 30, 50, 200))
        angle_panel.set_border((100, 150, 255), 2)
        self.add_ui_element(angle_panel)
        
        angle_title = TextLabel(5, 5, "Bone Angle Controls", 22, (255, 200, 100))
        angle_panel.add_child(angle_title)
        
        # Bone selection dropdown
        self.bone_dropdown = Dropdown(10, 40, 280, 30, ["Select a bone..."])
        self.bone_dropdown.set_on_selection_changed(self.on_bone_selected)
        self.bone_dropdown.set_simple_tooltip("Select a bone to adjust its angle")
        angle_panel.add_child(self.bone_dropdown)
        
        # Angle slider
        self.angle_label = TextLabel(10, 85, "Angle: 0°", 16, (200, 200, 255))
        angle_panel.add_child(self.angle_label)
        
        self.angle_slider = Slider(10, 110, 280, 30, -180, 180, 0)
        self.angle_slider.on_value_changed = self.on_angle_changed
        self.angle_slider.set_simple_tooltip("Adjust selected bone angle (-180° to 180°)")
        self.angle_slider.enabled = False
        angle_panel.add_child(self.angle_slider)
        
        # Reset bone button
        reset_btn = Button(10, 155, 280, 30, "Reset All Bones")
        reset_btn.set_on_click(self.reset_all_bones)
        reset_btn.set_simple_tooltip("Reset all bones to default angles")
        angle_panel.add_child(reset_btn)
        
        # Random pose button
        random_btn = Button(10, 195, 280, 30, "Random Pose")
        random_btn.set_on_click(self.random_pose)
        random_btn.set_simple_tooltip("Set random angles for all bones")
        angle_panel.add_child(random_btn)
        
        # --- Skeleton Stats Display ---
        stats_panel = UiFrame(self.engine.width - 320, 520, 300, 210)
        stats_panel.set_background_color((30, 30, 50, 200))
        stats_panel.set_border((100, 150, 255), 2)
        self.add_ui_element(stats_panel)
        
        stats_title = TextLabel(5, 5, "Skeleton Stats", 22, (255, 200, 100))
        stats_panel.add_child(stats_title)
        
        self.stats_bone_count = TextLabel(10, 40, "Bones: 0", 16)
        stats_panel.add_child(self.stats_bone_count)
        
        self.stats_position = TextLabel(10, 65, "Position: (0, 0)", 16)
        stats_panel.add_child(self.stats_position)
        
        self.stats_animation = TextLabel(10, 90, "Animation: None", 16)
        stats_panel.add_child(self.stats_animation)
        
        # Instructions
        instructions = [
            "Click and drag skeleton to move",
            "Use TAB to quickly switch skeletons",
            "Select bone from dropdown to adjust",
            "Use animation buttons for preset moves",
            "Try different bone colors!"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_label = TextLabel(10, 120 + i * 20, f"• {instruction}", 12, (150, 200, 255))
            stats_panel.add_child(inst_label)
        
        # --- FPS Display ---
        self.fps_display = TextLabel(self.engine.width - 5, 20, "FPS: --", 16, (100, 255, 100), root_point=(1, 0))
        self.add_ui_element(self.fps_display)
        
        # Update bone dropdown and stats
        self.update_bone_dropdown()
        self.update_stats()
    
    def switch_skeleton(self, skeleton_type: str):
        """Switch to a different skeleton type"""
        if skeleton_type in self.skeletons:
            self.current_skeleton_type = skeleton_type
            self.current_skeleton = self.skeletons[skeleton_type]
            
            # Reset position to center
            self.skeleton_position = [512, 384]
            
            # Stop any current animation
            self.stop_animation()
            
            # Update UI
            self.skeleton_info.set_text(f"Current: {skeleton_type} Skeleton")
            
            # Update bone dropdown
            self.update_bone_dropdown()
            
            # Update stats
            self.update_stats()
            
            print(f"Switched to {skeleton_type} skeleton")
    
    def update_bone_dropdown(self):
        """Update the bone dropdown with current skeleton's bones"""
        if self.current_skeleton:
            bone_names = list(self.current_skeleton.bones.keys())
            self.bone_dropdown.set_options(bone_names)
            if bone_names:
                self.bone_dropdown.set_selected_index(0)
                self.demo_state['current_bone'] = bone_names[0]
                self.update_angle_slider()
            else:
                self.demo_state['current_bone'] = None
    
    def on_bone_selected(self, index: int, bone_name: str):
        """Handle bone selection from dropdown"""
        self.demo_state['current_bone'] = bone_name
        self.update_angle_slider()
    
    def update_angle_slider(self):
        """Update angle slider based on selected bone"""
        if self.demo_state['current_bone'] and self.current_skeleton:
            bone = self.current_skeleton.get_bone(self.demo_state['current_bone'])
            current_angle = bone.joint.angle
            
            # Normalize angle to -180 to 180 range for slider
            normalized_angle = ((current_angle + 180) % 360) - 180
            
            self.angle_slider.set_value(normalized_angle)
            self.angle_label.set_text(f"Angle: {current_angle:.1f}°")
            self.angle_slider.enabled = True
        else:
            self.angle_slider.enabled = False
            self.angle_label.set_text("Angle: --")
    
    def on_angle_changed(self, angle: float):
        """Handle angle slider change"""
        if self.demo_state['current_bone'] and self.current_skeleton:
            # Convert slider angle back to 0-360 range
            normalized_angle = angle % 360
            
            self.current_skeleton.set_bone_angle(self.demo_state['current_bone'], normalized_angle)
            self.angle_label.set_text(f"Angle: {normalized_angle:.1f}°")
            
            # Update child positions
            self.current_skeleton._update_child_positions()
    
    def set_bone_color(self, color: Tuple[int, int, int]):
        """Set color for all bones in current skeleton"""
        self.demo_state['bone_color'] = color
        if self.current_skeleton:
            for bone_name, bone in self.current_skeleton.bones.items():
                bone.set_color(color)
    
    def toggle_joints(self, show: bool):
        """Toggle joint visibility"""
        self.demo_state['show_joints'] = show
        if self.current_skeleton:
            for bone_name, bone in self.current_skeleton.bones.items():
                bone.show_joint = show
    
    def set_bone_width(self, width: int):
        """Set bone width"""
        self.demo_state['bone_width'] = int(width)
        self.width_display.set_text(f"{width}")
        if self.current_skeleton:
            for bone_name, bone in self.current_skeleton.bones.items():
                bone.width = int(width)
    
    def set_animation_speed(self, speed: float):
        """Set animation speed"""
        self.animation_speed = speed
        self.speed_display.set_text(f"{speed:.1f}x")
        # Update active animation speed if any
        if self.active_animation:
            self.active_animation.set_duration(2.0 / speed)
    
    def stop_animation(self):
        """Stop current animation"""
        self.animation_handler.cancel_all()
        self.active_animation = None
        self.stats_animation.set_text("Animation: None")
    
    def play_idle_animation(self):
        """Play idle/breathing animation"""
        self.stop_animation()
        
        if self.current_skeleton_type == "Human":
            # Gentle breathing motion for human
            self.animate_bone_with_tween("torso", 0, 5, 2.0, EasingType.SINE_IN_OUT, loops=-1, yoyo=True)
            self.animate_bone_with_tween("neck", 0, 3, 2.5, EasingType.SINE_IN_OUT, loops=-1, yoyo=True)
        elif self.current_skeleton_type in ["Dog", "Cat"]:
            # Tail wag for animals
            self.animate_bone_with_tween("tail", 170, 190, 1.5, EasingType.SINE_IN_OUT, loops=-1, yoyo=True)
        
        self.stats_animation.set_text("Animation: Idle")
    
    def play_walk_animation(self):
        """Play walking animation"""
        self.stop_animation()
        
        if self.current_skeleton_type == "Human":
            # Human walk cycle
            self.animate_bone_with_tween("left_upper_leg", 280, 300, 0.5, EasingType.SINE_IN_OUT, loops=-1, yoyo=True)
            self.animate_bone_with_tween("right_upper_leg", 260, 280, 0.5, EasingType.SINE_IN_OUT, loops=-1, yoyo=True, delay=0.25)
            self.animate_bone_with_tween("left_upper_arm", 45, 65, 0.5, EasingType.SINE_IN_OUT, loops=-1, yoyo=True, delay=0.25)
            self.animate_bone_with_tween("right_upper_arm", 135, 155, 0.5, EasingType.SINE_IN_OUT, loops=-1, yoyo=True)
        elif self.current_skeleton_type in ["Dog", "Cat", "Horse"]:
            # Quadruped walk cycle
            legs = []
            if self.current_skeleton_type == "Dog" or self.current_skeleton_type == "Cat":
                legs = ["front_right_upper", "front_left_upper", "back_right_upper", "back_left_upper"]
            elif self.current_skeleton_type == "Horse":
                legs = ["front_right_upper", "front_left_upper", "back_right_upper", "back_left_upper"]
            
            for i, leg in enumerate(legs):
                if leg in self.current_skeleton.bones:
                    base_angle = 270  # Default angle for legs
                    self.animate_bone_with_tween(leg, base_angle - 15, base_angle + 15, 0.8, 
                                                EasingType.SINE_IN_OUT, loops=-1, yoyo=True, 
                                                delay=i * 0.2)
        
        self.stats_animation.set_text("Animation: Walking")
    
    def play_jump_animation(self):
        """Play jumping animation"""
        self.stop_animation()
        
        if self.current_skeleton_type == "Human":
            # Human jump
            self.animate_bone_with_tween("torso", 0, 15, 0.5, EasingType.BOUNCE_OUT, loops=1)
            self.animate_bone_with_tween("left_upper_leg", 280, 320, 0.5, EasingType.BOUNCE_OUT, loops=1)
            self.animate_bone_with_tween("right_upper_leg", 260, 300, 0.5, EasingType.BOUNCE_OUT, loops=1)
        elif self.current_skeleton_type in ["Dog", "Cat"]:
            # Animal pounce
            self.animate_bone_with_tween("spine", 5, 15, 0.5, EasingType.BOUNCE_OUT, loops=1)
            self.animate_bone_with_tween("front_right_upper", 270, 300, 0.5, EasingType.BOUNCE_OUT, loops=1)
            self.animate_bone_with_tween("front_left_upper", 270, 240, 0.5, EasingType.BOUNCE_OUT, loops=1)
        
        self.stats_animation.set_text("Animation: Jump")
    
    def play_attack_animation(self):
        """Play attack animation"""
        self.stop_animation()
        
        if self.current_skeleton_type == "Human":
            # Punch/kick animation
            self.animate_bone_with_tween("right_upper_arm", 135, 180, 0.2, EasingType.BACK_OUT, loops=1)
            self.animate_bone_with_tween("right_lower_arm", -20, -60, 0.2, EasingType.BACK_OUT, loops=1, delay=0.1)
        elif self.current_skeleton_type in ["Dog", "Cat"]:
            # Bite/pounce animation
            self.animate_bone_with_tween("head", 0, 15, 0.3, EasingType.BACK_OUT, loops=1)
            self.animate_bone_with_tween("neck", 355, 340, 0.3, EasingType.BACK_OUT, loops=1)
        
        self.stats_animation.set_text("Animation: Attack")
    
    def play_dance_animation(self):
        """Play fun dance animation"""
        self.stop_animation()
        
        if self.current_skeleton_type == "Human":
            # Funky dance moves
            self.animate_bone_with_tween("torso", 0, 10, 0.8, EasingType.SINE_IN_OUT, loops=-1, yoyo=True)
            self.animate_bone_with_tween("left_upper_arm", 45, 90, 0.6, EasingType.SINE_IN_OUT, loops=-1, yoyo=True)
            self.animate_bone_with_tween("right_upper_arm", 135, 180, 0.7, EasingType.SINE_IN_OUT, loops=-1, yoyo=True, delay=0.3)
            self.animate_bone_with_tween("left_upper_leg", 280, 310, 0.5, EasingType.SINE_IN_OUT, loops=-1, yoyo=True, delay=0.1)
            self.animate_bone_with_tween("right_upper_leg", 260, 290, 0.5, EasingType.SINE_IN_OUT, loops=-1, yoyo=True, delay=0.4)
        
        self.stats_animation.set_text("Animation: Dance Party!")
    
    def animate_bone_with_tween(self, bone_name: str, start_angle: float, end_angle: float, 
                               duration: float, easing: EasingType, loops: int = 0, 
                               yoyo: bool = False, delay: float = 0):
        """Create and play a tween animation for a bone"""
        if not self.current_skeleton or bone_name not in self.current_skeleton.bones:
            return
        
        bone = self.current_skeleton.get_bone(bone_name)
        
        # Save current angle
        original_angle = bone.joint.angle
        
        # Create tween
        tween = Tween.create(bone.joint)
        tween.to(
            angle=end_angle,
            duration=duration / self.animation_speed,
            easing=easing
        )
        
        if loops != 0:
            tween.set_loops(loops, yoyo=yoyo)
        
        tween.set_callbacks(
            on_update=lambda t, p: self.current_skeleton._update_child_positions() if self.current_skeleton else None,
            on_complete=lambda: self.on_animation_complete(bone_name, original_angle) if loops == 1 else None
        )
        
        # Add delay if specified
        if delay > 0:
            tween.set_delay(delay)
        
        self.animation_handler.add(f"bone_{bone_name}", tween, auto_play=True)
    
    def on_animation_complete(self, bone_name: str, original_angle: float):
        """Callback when single-loop animation completes"""
        # Reset to original angle for single-play animations
        if self.current_skeleton and bone_name in self.current_skeleton.bones:
            self.current_skeleton.set_bone_angle(bone_name, original_angle)
            self.current_skeleton._update_child_positions()
    
    def reset_all_bones(self):
        """Reset all bones to default angles"""
        self.stop_animation()
        
        # Recreate the skeleton to reset all angles
        if self.current_skeleton_type == "Human":
            self.skeletons['Human'] = HumanBones(512, 384, 1.0)
            self.current_skeleton = self.skeletons['Human']
        elif self.current_skeleton_type == "Dog":
            self.skeletons['Dog'] = DogBones(512, 384, 1.0)
            self.current_skeleton = self.skeletons['Dog']
        elif self.current_skeleton_type == "Cat":
            self.skeletons['Cat'] = CatBones(512, 384, 1.0)
            self.current_skeleton = self.skeletons['Cat']
        elif self.current_skeleton_type == "Horse":
            self.skeletons['Horse'] = HorseBones(512, 384, 0.8)
            self.current_skeleton = self.skeletons['Horse']
        
        # Update UI
        self.update_bone_dropdown()
        self.update_stats()
        
        print("All bones reset to default angles")
    
    def random_pose(self):
        """Set random angles for all bones"""
        self.stop_animation()
        
        if self.current_skeleton:
            for bone_name in self.current_skeleton.bones.keys():
                random_angle = (hash(bone_name + str(pg.time.get_ticks())) % 360)
                self.current_skeleton.set_bone_angle(bone_name, random_angle)
            
            self.current_skeleton._update_child_positions()
            self.update_angle_slider()
            
            print("Random pose applied")
    
    def update_stats(self):
        """Update skeleton statistics display"""
        if self.current_skeleton:
            self.stats_bone_count.set_text(f"Bones: {len(self.current_skeleton.bones)}")
            self.stats_position.set_text(f"Position: ({self.skeleton_position[0]}, {self.skeleton_position[1]})")
    
    def handle_events(self, events):
        """Handle input events"""
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_TAB:
                    # Cycle through skeletons
                    skeleton_types = list(self.skeletons.keys())
                    current_index = skeleton_types.index(self.current_skeleton_type)
                    next_index = (current_index + 1) % len(skeleton_types)
                    self.switch_skeleton(skeleton_types[next_index])
            
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = pg.mouse.get_pos()
                    
                    # Check if click is within skeleton bounds (rough estimate)
                    skeleton_radius = 150
                    dx = mouse_pos[0] - self.skeleton_position[0]
                    dy = mouse_pos[1] - self.skeleton_position[1]
                    
                    if dx*dx + dy*dy < skeleton_radius*skeleton_radius:
                        self.is_dragging = True
                        self.drag_offset = [dx, dy]
            
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    self.is_dragging = False
            
            elif event.type == pg.MOUSEMOTION:
                if self.is_dragging:
                    mouse_pos = pg.mouse.get_pos()
                    self.skeleton_position = [
                        mouse_pos[0] - self.drag_offset[0],
                        mouse_pos[1] - self.drag_offset[1]
                    ]
    
    def update(self, dt):
        """Update scene"""
        # Update animations
        self.animation_handler.update(dt)
        
        # Update FPS display
        fps_stats = self.engine.get_fps_stats()
        self.fps_display.set_text(f"FPS: {fps_stats['current_fps']:.1f}")
        
        # Update stats
        self.update_stats()
    
    def render(self, renderer):
        """Render scene"""
        renderer.fill_screen(ThemeManager.get_color('background'))
        
        # Draw grid background
        grid_size = 50
        grid_color = (40, 40, 60)
        for x in range(0, self.engine.width, grid_size):
            renderer.draw_line(x, 0, x, self.engine.height, grid_color, 2)
        for y in range(0, self.engine.height, grid_size):
            renderer.draw_line(0, y, self.engine.width, y, grid_color, 2)
        
        # Draw center marker
        renderer.draw_circle(512, 384, 5, (100, 100, 150, 150))
        
        # Draw skeleton at current position
        if self.current_skeleton:
            # Temporarily translate all bones
            original_positions = {}
            for bone_name, bone in self.current_skeleton.bones.items():
                original_positions[bone_name] = (bone.joint.x, bone.joint.y)
                
                # Adjust position for rendering
                bone.joint.x = self.skeleton_position[0] + (bone.joint.x - 512)
                bone.joint.y = self.skeleton_position[1] + (bone.joint.y - 384)
            
            # Apply bone color and joint visibility
            for bone_name, bone in self.current_skeleton.bones.items():
                bone.set_color(self.demo_state['bone_color'])
                bone.show_joint = self.demo_state['show_joints']
                bone.width = self.demo_state['bone_width']
            
            # Render skeleton
            self.current_skeleton.render(renderer)
            
            # Draw skeleton name at position
            renderer.draw_text(self.current_skeleton_type, self.skeleton_position[0], 
                             self.skeleton_position[1] - 180, (255, 200, 100),
                             FontManager.get_font(None, 24), anchor_point=(0.5, 0.5))
            
            # Draw drag indicator if dragging
            if self.is_dragging:
                renderer.draw_circle(self.skeleton_position[0], self.skeleton_position[1], 
                                   10, (255, 255, 255, 100))
            
            # Restore original positions
            for bone_name, bone in self.current_skeleton.bones.items():
                if bone_name in original_positions:
                    bone.joint.x, bone.joint.y = original_positions[bone_name]
        
        # Draw UI panels background
        renderer.draw_rect(15, 105, 310, 630, (20, 20, 40, 200))
        renderer.draw_rect(self.engine.width - 325, 105, 310, 630, (20, 20, 40, 200))


def main():
    # Create engine
    engine = LunaEngine("LunaEngine - Bones System Demo", 1024, 768, use_opengl=True, fullscreen=False)
    
    # Configure the max FPS
    engine.fps = 60
    
    # Add and set the main scene
    engine.add_scene("main", BonesDemo)
    engine.set_scene("main")
    
    # Run the engine
    engine.run()

if __name__ == "__main__":
    main()