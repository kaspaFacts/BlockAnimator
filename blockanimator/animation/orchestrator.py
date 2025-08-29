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

            # First check for direct SequentialAnimations
        if len(args) == 1 and hasattr(args[0], 'animation_groups'):
            print(f"[ORCHESTRATOR] Direct sequential detected with {len(args[0].animation_groups)} groups")
            animation_groups = []
            for i, group in enumerate(args[0].animation_groups):
                print(f"[ORCHESTRATOR] Processing group {i}: {type(group)}")
                group_animations = self._extract_animations_from_item(group)
                print(f"[ORCHESTRATOR] Group {i} extracted {len(group_animations)} animations")
                animation_groups.append(group_animations)

            print(f"[ORCHESTRATOR] Calling play_sequential with {len(animation_groups)} groups")
            end_frame = self.animation_controller.play_sequential(animation_groups)
            self.timeline.update_timing(end_frame)
            return end_frame

            # Extract all animations
        all_extracted = []
        for arg in args:
            extracted = self._extract_animations_from_item(arg)
            all_extracted.append(extracted)

            # Debug extraction for non-sequential path
        print(f"[ORCHESTRATOR] Debug extraction:")
        print(f"  args length: {len(args)}")
        print(f"  all_extracted length: {len(all_extracted)}")
        for i, extracted in enumerate(all_extracted):
            print(f"  extracted[{i}] length: {len(extracted)}")
            for j, item in enumerate(extracted):
                print(f"    item[{j}]: {type(item)} - has animation_groups: {hasattr(item, 'animation_groups')}")

                # Check if any extracted item is a SequentialAnimations object
        if len(all_extracted) == 1 and len(all_extracted[0]) == 1:
            item = all_extracted[0][0]
            if hasattr(item, 'animation_groups'):
                animation_groups = []
                for group in item.animation_groups:
                    group_animations = self._extract_animations_from_item(group)
                    animation_groups.append(group_animations)

                end_frame = self.animation_controller.play_sequential(animation_groups)
                self.timeline.update_timing(end_frame)
                return end_frame

                # Flatten for simultaneous execution
        all_animations = []
        for extracted in all_extracted:
            all_animations.extend(extracted)

        end_frame = self.animation_controller.play_simultaneous(all_animations)
        self.timeline.update_timing(end_frame)
        return end_frame

    def _extract_animations_from_item(self, item):
        """Extract animations from various item types"""
        if hasattr(item, 'pending_animations'):  # Animation proxy
            animations = list(item.pending_animations)
            item.pending_animations.clear()
            return animations
        elif hasattr(item, 'animations'):  # AnimationGroup
            extracted = []
            for sub_item in item.animations:
                extracted.extend(self._extract_animations_from_item(sub_item))
            return extracted
        elif hasattr(item, 'animation_groups'):  # SequentialAnimations
            # Return the SequentialAnimations object itself, don't flatten
            return [item]
        elif isinstance(item, list):
            extracted = []
            for sub_item in item:
                extracted.extend(self._extract_animations_from_item(sub_item))
            return extracted
        elif item is not None:
            return [item]
        return []

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