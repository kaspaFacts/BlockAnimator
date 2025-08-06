# BlockAnimator\blockanimator\animation\__init__.py

from .anim_types import *
from .groups import *
from .controller import AnimationController
from .proxy import BlockAnimationProxy
from .orchestrator import AnimationOrchestrator
from .timeline import Timeline

__all__ = [
    # Core classes
    'AnimationController',
    'BlockAnimationProxy',
    'AnimationOrchestrator',
    'Timeline',

    # Animation types
    'Animation',
    'AnimationType',
    'AnimationState',
    'MoveToAnimation',
    'ColorChangeAnimation',
    'CameraMoveAnimation',
    'FadeToAnimation',
    'WaitAnimation',
    'RelativeMoveAnimation',
    'LabelChangeAnimation',

    # Group classes and functions
    'TimelineEvent',
    'AnimationGroup',
    'SequentialAnimations',
    'simultaneous',
    'sequential'
]