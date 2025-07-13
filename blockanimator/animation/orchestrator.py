# BlockAnimator\blockanimator\animation\orchestrator.py

from .anim_types import WaitAnimation


class AnimationOrchestrator:
    def __init__(self, animation_controller, timeline):
        self.animation_controller = animation_controller
        self.timeline = timeline

    def play(self, *args, **kwargs):
        """Universal play method that handles animation proxies and different animation types"""
        if not args:
            return

        def extract_animations_from_item(item):
            """Extract animations from various item types"""
            if hasattr(item, 'pending_animations'):  # Animation proxy
                animations = list(item.pending_animations)
                item.pending_animations.clear()
                return animations
            elif isinstance(item, list):
                extracted = []
                for sub_item in item:
                    extracted.extend(extract_animations_from_item(sub_item))
                return extracted
            elif item is not None:
                return [item]
            return []

            # Extract animations from all arguments

        all_animations = []
        for arg in args:
            all_animations.extend(extract_animations_from_item(arg))

            # Play all collected animations simultaneously
        end_frame = self.animation_controller.play_simultaneous(all_animations)
        self.timeline.update_timing(end_frame)
        return end_frame

    def wait(self, duration):
        """Add a wait/pause to the animation timeline"""
        wait_animation = WaitAnimation(
            sprite_id='wait',
            duration=duration
        )

        # Use the animation controller's timing system
        end_frame = self.animation_controller.play_simultaneous([wait_animation])
        self.timeline.update_timing(end_frame)
        return end_frame