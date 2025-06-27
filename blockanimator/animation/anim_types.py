# BlockAnimator\blockanimator\animation\anim_types.py

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum


class AnimationType(Enum):
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    FADE_TO = "fade_to"
    MOVE_TO = "move_to"
    COLOR_CHANGE = "color_change"
    ALPHA_CHANGE = "alpha_change"
    CAMERA_MOVE = "camera_move"
    CHANGE_APPEARANCE = "change_appearance"
    WAIT = "wait"


@dataclass
class AnimationState:
    """Runtime state for animations"""
    actual_start_alpha: Optional[int] = None
    actual_start_color: Optional[tuple] = None
    actual_start_grid_x: Optional[float] = None
    actual_start_grid_y: Optional[float] = None
    actual_start_x: Optional[float] = None
    actual_start_y: Optional[float] = None
    debug_frame_count: int = 0
    debug_start_frame: Optional[int] = None
    debug_end_frame: Optional[int] = None


@dataclass
class Animation:
    """Base animation with common properties"""
    sprite_id: str
    duration: float = 1.0
    delay: float = 0.0

    # Runtime fields
    start_frame: int = 0
    duration_frames: int = 0
    state: AnimationState = field(default_factory=AnimationState)


@dataclass
class FadeInAnimation(Animation):
    type: AnimationType = field(default=AnimationType.FADE_IN, init=False)
    target_alpha: int = 255

@dataclass
class FadeOutAnimation(Animation):
    type: AnimationType = field(default=AnimationType.FADE_OUT, init=False)
    target_alpha: int = 0

@dataclass
class MoveToAnimation(Animation):
    type: AnimationType = field(default=AnimationType.MOVE_TO, init=False)
    target_grid_x: float = 0.0
    target_grid_y: float = 0.0

@dataclass
class ColorChangeAnimation(Animation):
    type: AnimationType = field(default=AnimationType.COLOR_CHANGE, init=False)
    target_color: tuple = (255, 255, 255)

@dataclass
class AlphaChangeAnimation(Animation):
    type: AnimationType = field(default=AnimationType.ALPHA_CHANGE, init=False)
    target_alpha: int = (255)

@dataclass
class CameraMoveAnimation(Animation):
    type: AnimationType = field(default=AnimationType.CAMERA_MOVE, init=False)
    target_x: float = 0.0
    target_y: float = 0.0
    scene: Optional[Any] = None

@dataclass
class FadeToAnimation(Animation):
    type: AnimationType = field(default=AnimationType.FADE_TO, init=False)
    target_alpha: int = 255

@dataclass
class ChangeAppearanceAnimation(Animation):
    type: AnimationType = field(default=AnimationType.CHANGE_APPEARANCE, init=False)
    target_color: Optional[tuple] = None
    target_alpha: Optional[int] = None

@dataclass
class WaitAnimation(Animation):
    type: AnimationType = field(default=AnimationType.WAIT, init=False)