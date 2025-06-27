from animation.types import WaitAnimation


class AnimationOrchestrator:
    def __init__(self, animation_controller, timeline):
        self.animation_controller = animation_controller
        self.timeline = timeline

    def play(self, *args, **kwargs):
        """Universal play method that handles different animation types automatically"""
        if not args:
            return

        def flatten_animations(animations):
            """Recursively flatten nested lists of animations"""
            flattened = []
            for item in animations:
                if isinstance(item, list):
                    flattened.extend(flatten_animations(item))
                elif item is not None:
                    flattened.append(item)
            return flattened

            # Handle different input types

        if len(args) == 1:
            animation_input = args[0]

            # Check if it's a special animation group/sequence object
            if hasattr(animation_input, 'animation_type'):
                if animation_input.animation_type == 'simultaneous':
                    # Flatten the animations in the group
                    flattened_animations = flatten_animations(animation_input.animations)
                    end_frame = self.animation_controller.play_simultaneous(flattened_animations)
                elif animation_input.animation_type == 'sequential':
                    # Flatten each group in the sequence
                    flattened_groups = []
                    for group in animation_input.animation_groups:
                        flattened_groups.append(flatten_animations(group))
                    end_frame = self.animation_controller.play_sequential(flattened_groups)
                else:
                    # Single animation
                    end_frame = self.animation_controller.play_simultaneous([animation_input])
            elif isinstance(animation_input, list):
                # List of animations - flatten and play simultaneously
                flattened_animations = flatten_animations(animation_input)
                end_frame = self.animation_controller.play_simultaneous(flattened_animations)
            else:
                # Single animation
                end_frame = self.animation_controller.play_simultaneous([animation_input])
        else:
            # Multiple arguments - flatten all and play simultaneously
            all_animations = []
            for anim in args:
                if isinstance(anim, list):
                    all_animations.extend(flatten_animations(anim))
                elif anim is not None:
                    all_animations.append(anim)

            end_frame = self.animation_controller.play_simultaneous(all_animations)

            # Update timeline timing
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