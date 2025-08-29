# BlockAnimator\blockanimator\core\camera.py

from blockanimator.animation import CameraMoveAnimation

class CameraController:
    def __init__(self, scene, field_height):
        self.scene = scene
        self.field_height = field_height

    # TODO standardize grid format across engine
    def animate_camera_to_sprite(self, sprite_id, duration=1.0):
        """Create an animation to move camera to sprite."""
        sprite = self.scene.get_sprite_by_id(sprite_id)
        if sprite:
            # Calculate field dimensions
            aspect_ratio = self.scene.width / self.scene.height
            horizontal_field = self.field_height * aspect_ratio

            # Center camera on sprite by offsetting by half the visible field
            target_x = sprite.grid_x - (horizontal_field / 2)
            target_y = sprite.grid_y - (self.field_height / 2)

            return CameraMoveAnimation(
                sprite_id='camera',
                target_x=target_x,
                target_y=target_y,
                duration=duration,
                scene=self.scene
            )
        return None

    def animate_camera_move(self, delta_x, delta_y, duration=1.0):
        """Create an animation to move camera by offset."""
        return CameraMoveAnimation(
            sprite_id='camera',
            target_x=self.scene.coords.camera_x + delta_x,
            target_y=self.scene.coords.camera_y + delta_y,
            duration=duration,
            scene=self.scene
        )