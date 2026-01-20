"""
Miscellaneous things for LunaEngine

This module provides classes for creating and manipulating bone-based skeletal structures.

LOCATION: lunaengine/misc/bones.py
"""

import pygame as pg
import math
from typing import Tuple, Dict, Optional, List
from ..backend import OpenGLRenderer


class Joint:
    """Represents a joint in a skeletal system that can rotate."""
    
    def __init__(self, x: int, y: int, angle: float = 0, show_joint: bool = True):
        self.x = x
        self.y = y
        self.angle = angle  # Angle in degrees, 0 = right, 90 = down, 180 = left, 270 = up
        self.show_joint = show_joint
        self.parent: Optional['Joint'] = None
        
    def set_position(self, x: int, y: int) -> None:
        """Set the position of the joint."""
        self.x = x
        self.y = y
        
    def set_angle(self, angle: float) -> None:
        """Set the rotation angle of the joint."""
        self.angle = angle
        
    def get_end_position(self, length: int) -> Tuple[int, int]:
        """Calculate the endpoint position given a length and angle."""
        # Convert angle to radians
        rad = math.radians(self.angle)
        
        # Calculate endpoint
        end_x = self.x + length * math.cos(rad)
        end_y = self.y + length * math.sin(rad)
        
        return int(end_x), int(end_y)
        
    def render(self, renderer: OpenGLRenderer, color: Tuple[int, int, int] = (255, 100, 100), radius: int = 5) -> None:
        """Render the joint."""
        if self.show_joint:
            renderer.draw_circle(self.x, self.y, radius, color)


class Bone:
    """Represents a bone segment that connects a joint to an endpoint."""
    
    def __init__(self, joint: Joint, length: int, width: int = 3, 
                 color: Tuple[int, int, int] = (255, 255, 255)):
        self.joint = joint
        self.length = length
        self.width = width
        self.color = color
        self.end_x = 0
        self.end_y = 0
        self._calculate_end_position()
        
    def _calculate_end_position(self) -> None:
        """Calculate the end position based on joint angle and length."""
        self.end_x, self.end_y = self.joint.get_end_position(self.length)
        
    def set_color(self, color: Tuple[int, int, int]) -> None:
        """Set the color of the bone."""
        self.color = color
        
    def set_width(self, width: int) -> None:
        """Set the width of the bone."""
        self.width = width
        
    def set_angle(self, angle: float) -> None:
        """Set the angle of the bone's joint."""
        self.joint.set_angle(angle)
        self._calculate_end_position()
        
    def get_end_position(self) -> Tuple[int, int]:
        """Get the end position of the bone."""
        return self.end_x, self.end_y
        
    def render(self, renderer: OpenGLRenderer) -> None:
        """Render the bone."""
        self._calculate_end_position()
        renderer.draw_line(
            self.joint.x, self.joint.y,
            self.end_x, self.end_y,
            width=self.width, color=self.color
        )


class Skeleton:
    """A hierarchical skeleton system with joints and bones."""
    
    def __init__(self):
        self.bones: Dict[str, Bone] = {}
        self.joints: Dict[str, Joint] = {}
        self.hierarchy: Dict[str, str] = {}  # bone_name: parent_bone_name
        
    def add_joint(self, name: str, joint: Joint, parent_joint: Optional[str] = None) -> None:
        """Add a joint to the skeleton."""
        self.joints[name] = joint
        if parent_joint:
            # Store that this joint is attached to parent bone's end
            pass
            
    def add_bone(self, name: str, bone: Bone, parent_bone: Optional[str] = None) -> None:
        """Add a bone to the skeleton."""
        self.bones[name] = bone
        if parent_bone:
            self.hierarchy[name] = parent_bone
            
    def set_bone_angle(self, name: str, angle: float) -> None:
        """Set the angle of a bone."""
        if name in self.bones:
            self.bones[name].set_angle(angle)
            
            # Update child bones positions
            for child_name, parent_name in self.hierarchy.items():
                if parent_name == name:
                    child_bone = self.bones[child_name]
                    # Position child bone's joint at parent bone's end
                    parent_end = self.bones[name].get_end_position()
                    child_bone.joint.set_position(parent_end[0], parent_end[1])
                    
    def set_bone_color(self, name: str, color: Tuple[int, int, int]) -> None:
        """Set the color of a bone."""
        if name in self.bones:
            self.bones[name].set_color(color)
            
    def set_all_bones_color(self, color: Tuple[int, int, int]) -> None:
        """Set the color of all bones."""
        for bone in self.bones.values():
            bone.set_color(color)
            
    def set_bone_width(self, name: str, width: int) -> None:
        """Set the width of a bone."""
        if name in self.bones:
            self.bones[name].set_width(width)
            
    def set_all_bones_width(self, width: int) -> None:
        """Set the width of all bones."""
        for bone in self.bones.values():
            bone.set_width(width)
            
    def set_joints_visible(self, visible: bool) -> None:
        """Set visibility of all joints."""
        for joint in self.joints.values():
            joint.show_joint = visible
            
    def render(self, renderer: OpenGLRenderer) -> None:
        """Render the entire skeleton."""
        # Render all bones
        for bone in self.bones.values():
            bone.render(renderer)
            
        # Render all joints on top
        for joint in self.joints.values():
            joint.render(renderer)


class HumanBones(Skeleton):
    """Human skeleton with proper rotation."""
    
    def __init__(self, x: int = 400, y: int = 300, scale: float = 1.0):
        super().__init__()
        
        self.base_x = x
        self.base_y = y
        self.scale = scale
        
        self._create_skeleton()
        
    def _create_skeleton(self):
        """Create the human skeleton with proper hierarchy."""
        x, y = self.base_x, self.base_y
        scale = self.scale
        
        # Torso (root bone)
        torso_joint = Joint(x, y, angle=-90, show_joint=True)  # Pointing up
        torso = Bone(torso_joint, length=int(80 * scale), width=int(4 * scale))
        self.add_joint("torso_joint", torso_joint)
        self.add_bone("torso", torso)
        
        # Neck and head
        neck_joint = Joint(0, 0, angle=-90, show_joint=True)
        neck = Bone(neck_joint, length=int(20 * scale), width=int(3 * scale))
        self.add_joint("neck_joint", neck_joint)
        self.add_bone("neck", neck, "torso")
        
        head_joint = Joint(0, 0, angle=-90, show_joint=True)
        head = Bone(head_joint, length=int(20 * scale), width=int(3 * scale))
        self.add_joint("head_joint", head_joint)
        self.add_bone("head", head, "neck")
        
        # Left arm
        left_shoulder_joint = Joint(x, y - 20 * scale, angle=45, show_joint=True)
        left_upper_arm = Bone(left_shoulder_joint, length=int(40 * scale), width=int(3 * scale))
        self.add_joint("left_shoulder_joint", left_shoulder_joint)
        self.add_bone("left_upper_arm", left_upper_arm, "torso")
        
        left_elbow_joint = Joint(0, 0, angle=20, show_joint=True)
        left_lower_arm = Bone(left_elbow_joint, length=int(35 * scale), width=int(2 * scale))
        self.add_joint("left_elbow_joint", left_elbow_joint)
        self.add_bone("left_lower_arm", left_lower_arm, "left_upper_arm")
        
        # Right arm
        right_shoulder_joint = Joint(x, y - 20 * scale, angle=135, show_joint=True)
        right_upper_arm = Bone(right_shoulder_joint, length=int(40 * scale), width=int(3 * scale))
        self.add_joint("right_shoulder_joint", right_shoulder_joint)
        self.add_bone("right_upper_arm", right_upper_arm, "torso")
        
        right_elbow_joint = Joint(0, 0, angle=160, show_joint=True)
        right_lower_arm = Bone(right_elbow_joint, length=int(35 * scale), width=int(2 * scale))
        self.add_joint("right_elbow_joint", right_elbow_joint)
        self.add_bone("right_lower_arm", right_lower_arm, "right_upper_arm")
        
        # Left leg
        left_hip_joint = Joint(x - 15 * scale, y, angle=280, show_joint=True)
        left_upper_leg = Bone(left_hip_joint, length=int(50 * scale), width=int(3 * scale))
        self.add_joint("left_hip_joint", left_hip_joint)
        self.add_bone("left_upper_leg", left_upper_leg, "torso")
        
        left_knee_joint = Joint(0, 0, angle=340, show_joint=True)
        left_lower_leg = Bone(left_knee_joint, length=int(45 * scale), width=int(2 * scale))
        self.add_joint("left_knee_joint", left_knee_joint)
        self.add_bone("left_lower_leg", left_lower_leg, "left_upper_leg")
        
        # Right leg
        right_hip_joint = Joint(x + 15 * scale, y, angle=260, show_joint=True)
        right_upper_leg = Bone(right_hip_joint, length=int(50 * scale), width=int(3 * scale))
        self.add_joint("right_hip_joint", right_hip_joint)
        self.add_bone("right_upper_leg", right_upper_leg, "torso")
        
        right_knee_joint = Joint(0, 0, angle=340, show_joint=True)
        right_lower_leg = Bone(right_knee_joint, length=int(45 * scale), width=int(2 * scale))
        self.add_joint("right_knee_joint", right_knee_joint)
        self.add_bone("right_lower_leg", right_lower_leg, "right_upper_leg")
        
        # Update all positions based on hierarchy
        self._update_positions()
        
    def _update_positions(self):
        """Update positions of all bones based on hierarchy."""
        # Position child bones based on parent bones
        for bone_name, parent_name in self.hierarchy.items():
            if parent_name in self.bones:
                parent_bone = self.bones[parent_name]
                child_bone = self.bones[bone_name]
                
                # Get parent's end position
                parent_end = parent_bone.get_end_position()
                child_bone.joint.set_position(parent_end[0], parent_end[1])


class DogBones(Skeleton):
    """Dog skeleton with proper rotation."""
    
    def __init__(self, x: int = 400, y: int = 300, scale: float = 1.0):
        super().__init__()
        
        self.base_x = x
        self.base_y = y
        self.scale = scale
        
        self._create_skeleton()
        
    def _create_skeleton(self):
        """Create a simple dog skeleton with hierarchy."""
        x, y = self.base_x, self.base_y
        scale = self.scale
        
        # Spine (root)
        spine_joint = Joint(x, y, angle=0, show_joint=True)
        spine = Bone(spine_joint, length=int(100 * scale), width=int(5 * scale))
        self.add_joint("spine_joint", spine_joint)
        self.add_bone("spine", spine)
        
        # Neck and head
        neck_joint = Joint(0, 0, angle=340, show_joint=True)
        neck = Bone(neck_joint, length=int(40 * scale), width=int(4 * scale))
        self.add_joint("neck_joint", neck_joint)
        self.add_bone("neck", neck, "spine")
        
        head_joint = Joint(0, 0, angle=350, show_joint=True)
        head = Bone(head_joint, length=int(30 * scale), width=int(4 * scale))
        self.add_joint("head_joint", head_joint)
        self.add_bone("head", head, "neck")
        
        # Tail
        tail_joint = Joint(0, 0, angle=160, show_joint=True)
        tail = Bone(tail_joint, length=int(60 * scale), width=int(3 * scale))
        self.add_joint("tail_joint", tail_joint)
        self.add_bone("tail", tail, "spine")
        
        # Front legs
        fr_shoulder_joint = Joint(0, 0, angle=270, show_joint=True)
        fr_upper = Bone(fr_shoulder_joint, length=int(45 * scale), width=int(4 * scale))
        self.add_joint("fr_shoulder_joint", fr_shoulder_joint)
        self.add_bone("fr_upper", fr_upper, "spine")
        
        fl_shoulder_joint = Joint(0, 0, angle=270, show_joint=True)
        fl_upper = Bone(fl_shoulder_joint, length=int(45 * scale), width=int(4 * scale))
        self.add_joint("fl_shoulder_joint", fl_shoulder_joint)
        self.add_bone("fl_upper", fl_upper, "spine")
        
        # Back legs
        br_hip_joint = Joint(0, 0, angle=250, show_joint=True)
        br_upper = Bone(br_hip_joint, length=int(45 * scale), width=int(4 * scale))
        self.add_joint("br_hip_joint", br_hip_joint)
        self.add_bone("br_upper", br_upper, "spine")
        
        bl_hip_joint = Joint(0, 0, angle=290, show_joint=True)
        bl_upper = Bone(bl_hip_joint, length=int(45 * scale), width=int(4 * scale))
        self.add_joint("bl_hip_joint", bl_hip_joint)
        self.add_bone("bl_upper", bl_upper, "spine")
        
        # Update positions
        self._update_positions()
        
    def _update_positions(self):
        """Update positions of all bones based on hierarchy."""
        for bone_name, parent_name in self.hierarchy.items():
            if parent_name in self.bones:
                parent_bone = self.bones[parent_name]
                child_bone = self.bones[bone_name]
                
                parent_end = parent_bone.get_end_position()
                child_bone.joint.set_position(parent_end[0], parent_end[1])


class CatBones(Skeleton):
    """Cat skeleton with proper rotation."""
    
    def __init__(self, x: int = 400, y: int = 300, scale: float = 1.0):
        super().__init__()
        
        self.base_x = x
        self.base_y = y
        self.scale = scale
        
        self._create_skeleton()
        
    def _create_skeleton(self):
        """Create a simple cat skeleton with hierarchy."""
        x, y = self.base_x, self.base_y
        scale = self.scale
        
        # Similar to dog but with cat proportions
        spine_joint = Joint(x, y, angle=5, show_joint=True)
        spine = Bone(spine_joint, length=int(80 * scale), width=int(4 * scale))
        self.add_joint("spine_joint", spine_joint)
        self.add_bone("spine", spine)
        
        neck_joint = Joint(0, 0, angle=355, show_joint=True)
        neck = Bone(neck_joint, length=int(20 * scale), width=int(3 * scale))
        self.add_joint("neck_joint", neck_joint)
        self.add_bone("neck", neck, "spine")
        
        head_joint = Joint(0, 0, angle=0, show_joint=True)
        head = Bone(head_joint, length=int(25 * scale), width=int(3 * scale))
        self.add_joint("head_joint", head_joint)
        self.add_bone("head", head, "neck")
        
        tail_joint = Joint(0, 0, angle=170, show_joint=True)
        tail = Bone(tail_joint, length=int(70 * scale), width=int(2 * scale))
        self.add_joint("tail_joint", tail_joint)
        self.add_bone("tail", tail, "spine")
        
        # Front legs (more angled for cat crouch)
        fr_shoulder_joint = Joint(0, 0, angle=280, show_joint=True)
        fr_upper = Bone(fr_shoulder_joint, length=int(30 * scale), width=int(3 * scale))
        self.add_joint("fr_shoulder_joint", fr_shoulder_joint)
        self.add_bone("fr_upper", fr_upper, "spine")
        
        fl_shoulder_joint = Joint(0, 0, angle=260, show_joint=True)
        fl_upper = Bone(fl_shoulder_joint, length=int(30 * scale), width=int(3 * scale))
        self.add_joint("fl_shoulder_joint", fl_shoulder_joint)
        self.add_bone("fl_upper", fl_upper, "spine")
        
        # Back legs
        br_hip_joint = Joint(0, 0, angle=240, show_joint=True)
        br_upper = Bone(br_hip_joint, length=int(30 * scale), width=int(3 * scale))
        self.add_joint("br_hip_joint", br_hip_joint)
        self.add_bone("br_upper", br_upper, "spine")
        
        bl_hip_joint = Joint(0, 0, angle=300, show_joint=True)
        bl_upper = Bone(bl_hip_joint, length=int(30 * scale), width=int(3 * scale))
        self.add_joint("bl_hip_joint", bl_hip_joint)
        self.add_bone("bl_upper", bl_upper, "spine")
        
        # Update positions
        self._update_positions()
        
    def _update_positions(self):
        """Update positions of all bones based on hierarchy."""
        for bone_name, parent_name in self.hierarchy.items():
            if parent_name in self.bones:
                parent_bone = self.bones[parent_name]
                child_bone = self.bones[bone_name]
                
                parent_end = parent_bone.get_end_position()
                child_bone.joint.set_position(parent_end[0], parent_end[1])


class HorseBones(Skeleton):
    """Horse skeleton with proper rotation."""
    
    def __init__(self, x: int = 400, y: int = 300, scale: float = 1.0):
        super().__init__()
        
        self.base_x = x
        self.base_y = y
        self.scale = scale * 0.8  # Scale down horse a bit
        
        self._create_skeleton()
        
    def _create_skeleton(self):
        """Create a simple horse skeleton with hierarchy."""
        x, y = self.base_x, self.base_y
        scale = self.scale
        
        # Long spine
        spine_joint = Joint(x, y, angle=0, show_joint=True)
        spine = Bone(spine_joint, length=int(150 * scale), width=int(8 * scale))
        self.add_joint("spine_joint", spine_joint)
        self.add_bone("spine", spine)
        
        # Long neck and head
        neck_joint = Joint(0, 0, angle=340, show_joint=True)
        neck = Bone(neck_joint, length=int(80 * scale), width=int(6 * scale))
        self.add_joint("neck_joint", neck_joint)
        self.add_bone("neck", neck, "spine")
        
        head_joint = Joint(0, 0, angle=350, show_joint=True)
        head = Bone(head_joint, length=int(50 * scale), width=int(5 * scale))
        self.add_joint("head_joint", head_joint)
        self.add_bone("head", head, "neck")
        
        # Tail
        tail_joint = Joint(0, 0, angle=200, show_joint=True)
        tail = Bone(tail_joint, length=int(80 * scale), width=int(4 * scale))
        self.add_joint("tail_joint", tail_joint)
        self.add_bone("tail", tail, "spine")
        
        # Front legs (long)
        fr_shoulder_joint = Joint(0, 0, angle=270, show_joint=True)
        fr_upper = Bone(fr_shoulder_joint, length=int(70 * scale), width=int(6 * scale))
        self.add_joint("fr_shoulder_joint", fr_shoulder_joint)
        self.add_bone("fr_upper", fr_upper, "spine")
        
        fr_knee_joint = Joint(0, 0, angle=270, show_joint=True)
        fr_lower = Bone(fr_knee_joint, length=int(60 * scale), width=int(5 * scale))
        self.add_joint("fr_knee_joint", fr_knee_joint)
        self.add_bone("fr_lower", fr_lower, "fr_upper")
        
        # Other front leg
        fl_shoulder_joint = Joint(0, 0, angle=270, show_joint=True)
        fl_upper = Bone(fl_shoulder_joint, length=int(70 * scale), width=int(6 * scale))
        self.add_joint("fl_shoulder_joint", fl_shoulder_joint)
        self.add_bone("fl_upper", fl_upper, "spine")
        
        # Back legs
        br_hip_joint = Joint(0, 0, angle=250, show_joint=True)
        br_upper = Bone(br_hip_joint, length=int(70 * scale), width=int(6 * scale))
        self.add_joint("br_hip_joint", br_hip_joint)
        self.add_bone("br_upper", br_upper, "spine")
        
        br_knee_joint = Joint(0, 0, angle=290, show_joint=True)
        br_lower = Bone(br_knee_joint, length=int(60 * scale), width=int(5 * scale))
        self.add_joint("br_knee_joint", br_knee_joint)
        self.add_bone("br_lower", br_lower, "br_upper")
        
        bl_hip_joint = Joint(0, 0, angle=290, show_joint=True)
        bl_upper = Bone(bl_hip_joint, length=int(70 * scale), width=int(6 * scale))
        self.add_joint("bl_hip_joint", bl_hip_joint)
        self.add_bone("bl_upper", bl_upper, "spine")
        
        # Update positions
        self._update_positions()
        
    def _update_positions(self):
        """Update positions of all bones based on hierarchy."""
        for bone_name, parent_name in self.hierarchy.items():
            if parent_name in self.bones:
                parent_bone = self.bones[parent_name]
                child_bone = self.bones[bone_name]
                
                parent_end = parent_bone.get_end_position()
                child_bone.joint.set_position(parent_end[0], parent_end[1])