"""Unified animation controller."""

class AnimationController:
    """Handles all animation types uniformly using frame-based timing."""

    def __init__(self, fps=None):
        self.animations = []
        self.fps = fps

    def add_animation(self, animation):
        """Add an animation to the controller."""
        self._add_debug_fields(animation)
        self.animations.append(animation)

    def _add_debug_fields(self, animation):
        """Initialize debugging fields for an animation."""
        animation['debug_frame_count'] = 0
        animation['debug_start_frame'] = None
        animation['debug_end_frame'] = None

    def update_sprites(self, sprites, current_frame):
        """Update all sprites based on current frame number."""
        for animation in self.animations:
            if self._is_active_frame(animation, current_frame):
                progress = self._calculate_progress_frame(animation, current_frame)
                self._apply_animation(animation, sprites, progress, current_frame)

    def _is_active_frame(self, animation, current_frame):
        """Check if animation is active based on frame bounds."""
        start_frame = animation['start_frame']
        duration_frames = animation['duration_frames']
        end_frame = start_frame + duration_frames
        return start_frame <= current_frame <= end_frame

    def duration_to_frames(self, duration_seconds):
        """Convert duration in seconds to exact frame count."""
        return round(duration_seconds * self.fps)

    def _calculate_progress_frame(self, animation, current_frame):
        """Calculate animation progress based on frame numbers."""
        start_frame = animation['start_frame']
        duration_frames = animation['duration_frames']

        if current_frame >= start_frame + duration_frames:
            return 1.0

        elapsed_frames = current_frame - start_frame
        return max(0.0, min(elapsed_frames / duration_frames, 1.0))

    def _apply_animation(self, animation, sprites, progress, current_frame):
        """Apply animation to sprite with debugging."""
        self._update_debug_info(animation, progress, current_frame)

        sprite_id = animation['sprite_id']
        anim_type = animation['type']
        is_complete = progress >= 1.0

        # Route to specific animation handler
        if anim_type == 'camera_move':
            self._handle_camera_animation(animation, is_complete, progress)
        else:
            sprite = sprites.get(sprite_id)
            if sprite:
                self._handle_sprite_animation(animation, sprite, is_complete, progress)

    def _update_debug_info(self, animation, progress, current_frame):
        """Update debugging information for an animation."""
        if animation['debug_start_frame'] is None:
            animation['debug_start_frame'] = animation['start_frame']
            sprite_id = animation['sprite_id']
            anim_type = animation['type']
            print(f"Animation {sprite_id}:{anim_type} started at frame {animation['debug_start_frame']}")

        animation['debug_frame_count'] += 1
        animation['debug_end_frame'] = current_frame

        if progress >= 1.0:
            self._print_completion_debug(animation, progress)

    def _print_completion_debug(self, animation, progress):
        """Print debug information when animation completes."""
        expected_frames = animation['duration_frames']
        actual_frames = animation['debug_frame_count']
        sprite_id = animation['sprite_id']
        anim_type = animation['type']

        print(f"Animation {sprite_id}:{anim_type} completed:")
        print(f"  Expected frames: {expected_frames}")
        print(f"  Actual frames: {actual_frames}")
        print(f"  Start frame: {animation['debug_start_frame']}")
        print(f"  End frame: {animation['debug_end_frame']}")
        print(f"  Final progress: {progress}")

    def _handle_camera_animation(self, animation, is_complete, progress):
        """Handle camera movement animations."""
        self._capture_camera_start_position(animation)

        start_x = animation['actual_start_x']
        start_y = animation['actual_start_y']
        target_x = animation['target_x']
        target_y = animation['target_y']

        if is_complete:
            current_x, current_y = target_x, target_y
        else:
            current_x = start_x + (target_x - start_x) * progress
            current_y = start_y + (target_y - start_y) * progress

        scene = animation.get('scene')
        if scene:
            scene.coords.set_camera_position(current_x, current_y)

    def _capture_camera_start_position(self, animation):
        """Capture camera start position on first frame."""
        if 'actual_start_x' not in animation:
            scene = animation.get('scene')
            if scene:
                animation['actual_start_x'] = scene.coords.camera_x
                animation['actual_start_y'] = scene.coords.camera_y

    def _handle_sprite_animation(self, animation, sprite, is_complete, progress):
        """Route sprite animation to specific handler based on type."""
        anim_type = animation['type']

        handlers = {
            'fade_in': self._handle_fade_in,
            'move_to': self._handle_move_to,
            'color_change': self._handle_color_change,
            'change_appearance': self._handle_change_appearance,
            'fade_to': self._handle_fade_to
        }

        handler = handlers.get(anim_type)
        if handler:
            handler(animation, sprite, is_complete, progress)

    def _handle_fade_in(self, animation, sprite, is_complete, progress):
        """Handle fade-in animations."""
        # Capture the starting alpha value on first frame
        if 'actual_start_alpha' not in animation:
            animation['actual_start_alpha'] = sprite.alpha
            print(f"Fade-in starting: sprite {animation['sprite_id']} alpha={sprite.alpha}")

        start_alpha = animation['actual_start_alpha']
        target_alpha = 255  # Always fade to full opacity

        if is_complete:
            print(f"Fade-in complete: setting {animation['sprite_id']} alpha to {target_alpha}")
            sprite.set_alpha(target_alpha)
        else:
            current_alpha = int(start_alpha + (target_alpha - start_alpha) * progress)
            sprite.set_alpha(current_alpha)
        sprite.set_visible(True)

    def _handle_move_to(self, animation, sprite, is_complete, progress):
        """Handle movement animations."""
        self._capture_sprite_start_position(animation, sprite)

        start_grid_x = animation['actual_start_grid_x']
        start_grid_y = animation['actual_start_grid_y']
        target_grid_x = animation['target_grid_x']
        target_grid_y = animation['target_grid_y']

        if is_complete:
            sprite.grid_x = target_grid_x
            sprite.grid_y = target_grid_y
        else:
            current_grid_x = start_grid_x + (target_grid_x - start_grid_x) * progress
            current_grid_y = start_grid_y + (target_grid_y - start_grid_y) * progress
            sprite.grid_x = current_grid_x
            sprite.grid_y = current_grid_y

    def _capture_sprite_start_position(self, animation, sprite):
        """Capture sprite start position on first frame."""
        if 'actual_start_grid_x' not in animation:
            animation['actual_start_grid_x'] = sprite.grid_x
            animation['actual_start_grid_y'] = sprite.grid_y

    def _handle_color_change(self, animation, sprite, is_complete, progress):
        """Handle color change animations."""
        self._capture_sprite_start_color(animation, sprite)

        start_color = animation['actual_start_color']
        target_color = animation['target_color']

        if is_complete:
            sprite.set_color(target_color)
        else:
            current_color = self._interpolate_color(start_color, target_color, progress)
            sprite.set_color(current_color)

    def _capture_sprite_start_color(self, animation, sprite):
        """Capture sprite start color on first frame."""
        if 'actual_start_color' not in animation:
            animation['actual_start_color'] = sprite.color

    def _handle_change_appearance(self, animation, sprite, is_complete, progress):
        """Handle combined color and alpha change animations."""
        self._capture_sprite_start_appearance(animation, sprite)

        start_alpha = animation['actual_start_alpha']
        start_color = animation['actual_start_color']
        target_alpha = animation['target_alpha']
        target_color = animation['target_color']

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

    def _capture_sprite_start_appearance(self, animation, sprite):
        """Capture sprite start appearance on first frame."""
        if 'actual_start_alpha' not in animation:
            animation['actual_start_alpha'] = sprite.alpha
            animation['actual_start_color'] = sprite.color

    def _handle_fade_to(self, animation, sprite, is_complete, progress):
        """Handle fade-to animations."""
        self._capture_sprite_start_alpha(animation, sprite)

        start_alpha = animation['actual_start_alpha']
        target_alpha = animation['target_alpha']

        if is_complete:
            sprite.set_alpha(target_alpha)
        else:
            current_alpha = int(start_alpha + (target_alpha - start_alpha) * progress)
            sprite.set_alpha(current_alpha)

    def _capture_sprite_start_alpha(self, animation, sprite):
        """Capture sprite start alpha on first frame."""
        if 'actual_start_alpha' not in animation:
            animation['actual_start_alpha'] = sprite.alpha

    def _interpolate_color(self, start_color, target_color, progress):
        """Interpolate between two colors based on progress."""
        return tuple(
            int(start_color[i] + (target_color[i] - start_color[i]) * progress)
            for i in range(3)
        )