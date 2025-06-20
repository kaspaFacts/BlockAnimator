"""Unified animation controller."""

class AnimationController:
    """Handles all animation types uniformly."""

    def __init__(self):
        self.animations = []

    def add_animation(self, animation):
        """Add an animation to the controller."""
        self.animations.append(animation)

    def update_sprites(self, sprites, current_time):
        """Update all sprites based on current time."""
        for animation in self.animations:
            if self._is_active(animation, current_time):
                progress = self._calculate_progress(animation, current_time)
                self._apply_animation(animation, sprites, progress)

    def _is_active(self, animation, current_time):
        """Check if animation is active at current time."""
        start = animation['start_time']
        end = start + animation['duration']
        return start <= current_time <= end

    def _calculate_progress(self, animation, current_time):
        """Calculate animation progress (0.0 to 1.0)."""
        elapsed = current_time - animation['start_time']
        return min(elapsed / animation['duration'], 1.0)

    def _apply_animation(self, animation, sprites, progress):
        """Apply animation to sprite."""
        sprite_id = animation['sprite_id']
        anim_type = animation['type']

        # Handle camera animations separately since they don't target sprites
        if anim_type == 'camera_move':
            # Capture start position on first frame if not already captured
            if 'actual_start_x' not in animation:
                scene = animation.get('scene')
                if scene:
                    animation['actual_start_x'] = scene.coords.camera_x
                    animation['actual_start_y'] = scene.coords.camera_y

                    # Use the captured actual start positions
            start_x = animation['actual_start_x']
            start_y = animation['actual_start_y']
            target_x = animation['target_x']
            target_y = animation['target_y']

            current_x = start_x + (target_x - start_x) * progress
            current_y = start_y + (target_y - start_y) * progress

            # Access the scene's coordinate system
            scene = animation.get('scene')
            if scene:
                scene.coords.set_camera_position(current_x, current_y)
            return

            # For sprite animations, get the sprite
        sprite = sprites.get(sprite_id)
        if not sprite:
            return

        if anim_type == 'fade_in':
            sprite.set_alpha(int(255 * progress))
            sprite.set_visible(True)

        elif anim_type == 'move_to':
            # Capture start position on first frame if not already captured
            if 'actual_start_grid_x' not in animation:
                animation['actual_start_grid_x'] = sprite.grid_x
                animation['actual_start_grid_y'] = sprite.grid_y

                # Use the captured actual start positions
            start_grid_x = animation['actual_start_grid_x']
            start_grid_y = animation['actual_start_grid_y']
            target_grid_x = animation['target_grid_x']
            target_grid_y = animation['target_grid_y']

            current_grid_x = start_grid_x + (target_grid_x - start_grid_x) * progress
            current_grid_y = start_grid_y + (target_grid_y - start_grid_y) * progress

            # Update sprite's grid coordinates
            sprite.grid_x = current_grid_x
            sprite.grid_y = current_grid_y

        elif anim_type == 'color_change':
            from_color = animation['from_color']
            to_color = animation['to_color']

            current_color = tuple(
                int(from_color[i] + (to_color[i] - from_color[i]) * progress)
                for i in range(3)
            )
            sprite.set_color(current_color)