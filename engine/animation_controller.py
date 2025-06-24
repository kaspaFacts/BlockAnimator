from typing import List, Dict, Any
from engine.animations import Animation, AnimationType

class AnimationController:
    def __init__(self, fps: int = 30):
        self.animations: List[Animation] = []
        self.fps = fps
        self.next_available_frame = 0

        # Handler registry using enum types
        self.handlers = {
            AnimationType.FADE_IN: self._handle_fade_in,
            AnimationType.MOVE_TO: self._handle_move_to,
            AnimationType.COLOR_CHANGE: self._handle_color_change,
            AnimationType.CAMERA_MOVE: self._handle_camera_move,
            AnimationType.FADE_TO: self._handle_fade_to,
            AnimationType.CHANGE_APPEARANCE: self._handle_change_appearance,
            AnimationType.WAIT: self._handle_wait,
        }

    def play_simultaneous(self, animations, start_frame=None):
        """Play multiple animations at the same time"""
        if start_frame is None:
            start_frame = self.next_available_frame

        if not isinstance(animations, list):
            animations = [animations]

        # Filter out None animations
        valid_animations = [anim for anim in animations if anim is not None]

        if not valid_animations:
            return self.next_available_frame

        max_duration = 0
        for animation in valid_animations:
            animation.start_frame = start_frame + self.duration_to_frames(animation.delay)
            animation.duration_frames = self.duration_to_frames(animation.duration)
            max_duration = max(max_duration, animation.duration_frames + self.duration_to_frames(animation.delay))
            self.add_animation(animation)

        end_frame = start_frame + max_duration
        self.next_available_frame = end_frame
        return end_frame

    def play_sequential(self, animation_groups):
        """Play animation groups one after another"""
        current_frame = self.next_available_frame

        for group in animation_groups:
            # Each group plays simultaneously, but groups are sequential
            end_frame = self.play_simultaneous(group, current_frame)
            current_frame = end_frame

        return current_frame

    def add_animation(self, animation: Animation) -> None:
        """Add a typed animation to the controller."""
        self.animations.append(animation)

    def duration_to_frames(self, duration_seconds):
        """Convert duration in seconds to exact frame count."""
        return round(duration_seconds * self.fps)

    def update_sprites(self, sprites: Dict[str, Any], current_frame: int) -> None:
        """Update all sprites based on current frame."""
        for animation in self.animations:
            if self._is_active_frame(animation, current_frame):
                progress = self._calculate_progress(animation, current_frame)
                self._apply_animation(animation, sprites, progress, current_frame)

    def _is_active_frame(self, animation: Animation, current_frame: int) -> bool:
        """Check if animation is active based on frame bounds."""
        start_frame = animation.start_frame
        duration_frames = animation.duration_frames
        end_frame = start_frame + duration_frames
        return start_frame <= current_frame <= end_frame

    def _calculate_progress(self, animation: Animation, current_frame: int) -> float:
        """Calculate animation progress based on frame numbers."""
        start_frame = animation.start_frame
        duration_frames = animation.duration_frames

        if current_frame >= start_frame + duration_frames:
            return 1.0

        elapsed_frames = current_frame - start_frame
        return max(0.0, min(elapsed_frames / duration_frames, 1.0))

    def _apply_animation(self, animation: Animation, sprites: Dict[str, Any],
                        progress: float, current_frame: int) -> None:
        """Apply animation using type-specific handler."""
        self._update_debug_info(animation, progress, current_frame)

        handler = self.handlers.get(animation.type)
        if handler:
            if animation.type == AnimationType.CAMERA_MOVE:
                handler(animation, progress >= 1.0, progress)
            else:
                sprite = sprites.get(animation.sprite_id)
                if sprite:
                    handler(animation, sprite, progress >= 1.0, progress)

    def _update_debug_info(self, animation: Animation, progress: float, current_frame: int):
        """Update debugging information for an animation."""
        if animation.state.debug_start_frame is None:
            animation.state.debug_start_frame = animation.start_frame
            print(f"Animation {animation.sprite_id}:{animation.type.value} started at frame {animation.state.debug_start_frame}")

        animation.state.debug_frame_count += 1
        animation.state.debug_end_frame = current_frame

        if progress >= 1.0:
            self._print_completion_debug(animation, progress)

    def _print_completion_debug(self, animation: Animation, progress: float):
        """Print debug information when animation completes."""
        expected_frames = animation.duration_frames
        actual_frames = animation.state.debug_frame_count
        sprite_id = animation.sprite_id
        anim_type = animation.type.value

        print(f"Animation {sprite_id}:{anim_type} completed:")
        print(f"  Expected frames: {expected_frames}")
        print(f"  Actual frames: {actual_frames}")
        print(f"  Start frame: {animation.state.debug_start_frame}")
        print(f"  End frame: {animation.state.debug_end_frame}")
        print(f"  Final progress: {progress}")

    # Animation Handler Methods
    def _handle_fade_in(self, animation: Animation, sprite: Any,
                       is_complete: bool, progress: float) -> None:
        """Handle fade-in with captured state."""
        if animation.state.actual_start_alpha is None:
            animation.state.actual_start_alpha = sprite.alpha
            if hasattr(sprite, '_visible') and sprite._visible == 0:
                sprite.set_visible(True)

        start_alpha = animation.state.actual_start_alpha
        target_alpha = animation.target_alpha

        if is_complete:
            sprite.set_alpha(target_alpha)
            if not hasattr(sprite, '_visible'):
                sprite.set_visible(True)
        else:
            current_alpha = int(start_alpha + (target_alpha - start_alpha) * progress)
            sprite.set_alpha(current_alpha)
            if not hasattr(sprite, '_visible'):
                sprite.set_visible(True)

    def _handle_move_to(self, animation: Animation, sprite: Any,
                       is_complete: bool, progress: float) -> None:
        """Handle movement with captured state."""
        if animation.state.actual_start_grid_x is None:
            animation.state.actual_start_grid_x = sprite.grid_x
            animation.state.actual_start_grid_y = sprite.grid_y

        if is_complete:
            sprite.grid_x = animation.target_grid_x
            sprite.grid_y = animation.target_grid_y
        else:
            sprite.grid_x = animation.state.actual_start_grid_x + \
                           (animation.target_grid_x - animation.state.actual_start_grid_x) * progress
            sprite.grid_y = animation.state.actual_start_grid_y + \
                           (animation.target_grid_y - animation.state.actual_start_grid_y) * progress

    def _handle_color_change(self, animation: Animation, sprite: Any,
                            is_complete: bool, progress: float) -> None:
        """Handle color change with captured state."""
        if animation.state.actual_start_color is None:
            animation.state.actual_start_color = sprite.color

        start_color = animation.state.actual_start_color
        target_color = animation.target_color

        if is_complete:
            sprite.set_color(target_color)
        else:
            current_color = self._interpolate_color(start_color, target_color, progress)
            sprite.set_color(current_color)

    def _handle_fade_to(self, animation: Animation, sprite: Any,
                       is_complete: bool, progress: float) -> None:
        """Handle fade-to with captured state."""
        if animation.state.actual_start_alpha is None:
            animation.state.actual_start_alpha = sprite.alpha

        start_alpha = animation.state.actual_start_alpha
        target_alpha = animation.target_alpha

        if is_complete:
            sprite.set_alpha(target_alpha)
        else:
            current_alpha = int(start_alpha + (target_alpha - start_alpha) * progress)
            sprite.set_alpha(current_alpha)

    def _handle_change_appearance(self, animation: Animation, sprite: Any,
                                 is_complete: bool, progress: float) -> None:
        """Handle combined color and alpha change with captured state."""
        if animation.state.actual_start_alpha is None:
            animation.state.actual_start_alpha = sprite.alpha
            animation.state.actual_start_color = sprite.color

        start_alpha = animation.state.actual_start_alpha
        start_color = animation.state.actual_start_color
        target_alpha = animation.target_alpha
        target_color = animation.target_color

        if is_complete:
            if target_alpha is not None:
                sprite.set_alpha(target_alpha)
            if target_color is not None:
                sprite.set_color(target_color)
        else:
            if target_alpha is not None:
                current_alpha = int(start_alpha + (target_alpha - start_alpha) * progress)
                sprite.set_alpha(current_alpha)
            if target_color is not None:
                current_color = self._interpolate_color(start_color, target_color, progress)
                sprite.set_color(current_color)

    def _handle_camera_move(self, animation: Animation, is_complete: bool, progress: float):
        """Handle camera movement animations."""
        if animation.state.actual_start_x is None:
            scene = animation.scene
            if scene:
                animation.state.actual_start_x = scene.coords.camera_x
                animation.state.actual_start_y = scene.coords.camera_y

        start_x = animation.state.actual_start_x
        start_y = animation.state.actual_start_y
        target_x = animation.target_x
        target_y = animation.target_y

        if is_complete:
            current_x, current_y = target_x, target_y
        else:
            current_x = start_x + (target_x - start_x) * progress
            current_y = start_y + (target_y - start_y) * progress

        scene = animation.scene
        if scene:
            scene.coords.set_camera_position(current_x, current_y)

    def _handle_wait(self, animation: Animation, sprite: Any, is_complete: bool, progress: float):
        """Handle wait animations - do nothing, just consume time"""
        pass  # Wait animations don't need to do anything

    def _interpolate_color(self, start_color, target_color, progress):
        """Interpolate between two colors based on progress."""
        return tuple(
            int(start_color[i] + (target_color[i] - start_color[i]) * progress)
            for i in range(3)
        )
