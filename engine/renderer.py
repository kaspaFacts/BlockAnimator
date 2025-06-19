"""Video renderer."""

import cv2
import numpy as np
import pygame

class VideoRenderer:
    """Renders scene to video."""

    def __init__(self, scene, filename):
        self.scene = scene
        self.filename = filename
        self.fps = scene.fps
        self.total_frames = int(scene.scene_duration * self.fps)

        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            filename, fourcc, self.fps,
            (scene.width, scene.height)
        )

    def generate_video(self):
        """Generate the video."""
        print(f"Generating {self.total_frames} frames...")

        for frame_num in range(max(1, self.total_frames)):
            current_time = frame_num / self.fps

            # Update animations
            self.scene.animation_controller.update_sprites(
                self.scene.sprite_registry, current_time
            )

            # Update sprite positions based on current camera
            for sprite in self.scene.sprites:
                if hasattr(sprite, 'grid_x') and hasattr(sprite, 'grid_y'):
                    pixel_x, pixel_y = self.scene.coords.grid_to_pixel(sprite.grid_x, sprite.grid_y)
                    sprite.set_position(pixel_x, pixel_y)

            # In VideoRenderer.generate_video(), add after updating sprite positions:
            # Update connections to follow blocks
            self.scene.update_connections()

            # Render frame
            self.scene.screen.fill((0, 0, 0))
            self.scene.sprites.draw(self.scene.screen)

            # Convert to video format
            frame_array = pygame.surfarray.array3d(self.scene.screen)
            frame_array = np.rot90(frame_array)
            frame_array = np.flipud(frame_array)
            frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)

            self.video_writer.write(frame_bgr)

            if frame_num % 30 == 0:
                print(f"Progress: {frame_num}/{self.total_frames}")

        self.video_writer.release()
        print("Video generation complete!")