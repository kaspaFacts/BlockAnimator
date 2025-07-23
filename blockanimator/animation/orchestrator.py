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
            elif hasattr(item, 'animations'):  # AnimationGroup
                extracted = []
                for sub_item in item.animations:
                    extracted.extend(extract_animations_from_item(sub_item))
                return extracted
            elif hasattr(item, 'animation_groups'):  # SequentialAnimations
                extracted = []
                for sub_item in item.animation_groups:
                    extracted.extend(extract_animations_from_item(sub_item))
                return extracted
            elif isinstance(item, list):
                extracted = []
                for sub_item in item:
                    extracted.extend(extract_animations_from_item(sub_item))
                return extracted
            elif item is not None:
                return [item]
            return []

            # Check if we have a SequentialAnimations object

        if len(args) == 1 and hasattr(args[0], 'animation_groups'):
            # Handle sequential animations
            animation_groups = []
            for group in args[0].animation_groups:
                group_animations = extract_animations_from_item(group)
                animation_groups.append(group_animations)

            end_frame = self.animation_controller.play_sequential(animation_groups)
            self.timeline.update_timing(end_frame)
            return end_frame

            # Handle simultaneous animations (existing logic)
        all_animations = []
        for arg in args:
            all_animations.extend(extract_animations_from_item(arg))

        end_frame = self.animation_controller.play_simultaneous(all_animations)
        self.timeline.update_timing(end_frame)
        return end_frame

    def _play_sequential(self, sequential_animations):
        """Handle sequential animation groups"""
        animation_groups = []
        for group in sequential_animations.animation_groups:
            group_animations = self.extract_animations_from_item(group)
            animation_groups.append(group_animations)

        end_frame = self.animation_controller.play_sequential(animation_groups)
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