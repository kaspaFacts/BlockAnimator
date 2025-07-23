# BlockAnimator\blockanimator\animation\anim_types.py

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum


class AnimationType(Enum):
    FADE_TO = "fade_to"
    MOVE_TO = "move_to"
    COLOR_CHANGE = "color_change"
    CAMERA_MOVE = "camera_move"
    WAIT = "wait"
    RELATIVE_MOVE = "relative_move"


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
class MoveToAnimation(Animation):
    type: AnimationType = field(default=AnimationType.MOVE_TO, init=False)
    target_grid_x: float = 0.0
    target_grid_y: float = 0.0

@dataclass
class ColorChangeAnimation(Animation):
    type: AnimationType = field(default=AnimationType.COLOR_CHANGE, init=False)
    target_color: tuple = (255, 255, 255)

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
class WaitAnimation(Animation):
    type: AnimationType = field(default=AnimationType.WAIT, init=False)

@dataclass
class RelativeMoveAnimation(Animation):
    type: AnimationType = field(default=AnimationType.RELATIVE_MOVE, init=False)
    offset: tuple = (0.0, 0.0)  # Store offset instead of absolute position
    target_grid_x: Optional[float] = None  # Will be calculated at execution time
    target_grid_y: Optional[float] = None