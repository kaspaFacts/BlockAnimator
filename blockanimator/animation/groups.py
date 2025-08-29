# BlockAnimator\blockanimator\animation\groups.py

class TimelineEvent:
    def __init__(self, trigger_frame, event_type, **kwargs):
        self.trigger_frame = trigger_frame
        self.event_type = event_type
        self.kwargs = kwargs
        self.executed = False


class AnimationGroup:
    """Wrapper for simultaneous animations"""

    def __init__(self, animations):
        self.animations = animations if isinstance(animations, list) else [animations]
        self.animation_type = 'simultaneous'


class SequentialAnimations:
    """Wrapper for sequential animation groups"""

    def __init__(self, *animation_groups):
        # Store groups as-is, don't flatten them
        self.animation_groups = list(animation_groups)
        self.animation_type = 'sequential'

    # Convenience functions


def simultaneous(*animations):
    """Create a group of simultaneous animations"""
    return AnimationGroup(list(animations))


def sequential(*groups):
    """Create sequential animation groups"""
    return SequentialAnimations(*groups)
