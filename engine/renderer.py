"""Video renderer."""

import cv2
import numpy as np
import pygame
import time

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

        # Check if video writer was initialized successfully
        if not self.video_writer.isOpened():
            raise RuntimeError(f"Failed to open video writer for {filename}. "  
                             f"File may be in use by another application.")

    def generate_video(self):
        """Generate the video."""
        total_frames = max(self.scene.scene_duration_frames, int(self.scene.scene_duration * self.fps))
        print(f"Generating {total_frames} frames...")
        start_time = time.time()

        try:
            for frame_num in range(max(1, total_frames)):
                current_time = frame_num / self.fps

                # Process timeline events that should trigger at this frame
                for event in self.scene.timeline_events:
                    if not event.executed and frame_num >= event.trigger_frame:
                        self._execute_timeline_event(event, current_time, frame_num)
                        event.executed = True

                        # Update animations
                self.scene.animation_controller.update_sprites(
                    self.scene.sprite_registry, current_time
                )

                # Update sprite positions based on current camera
                for sprite in self.scene.sprites:
                    if hasattr(sprite, 'grid_x') and hasattr(sprite, 'grid_y'):
                        pixel_x, pixel_y = self.scene.coords.grid_to_pixel(sprite.grid_x, sprite.grid_y)
                        sprite.set_position(pixel_x, pixel_y)

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

                # Write frame and check for success
                success = self.video_writer.write(frame_bgr)
                if success is False:  # Some OpenCV versions return False on failure
                    raise RuntimeError(f"Failed to write frame {frame_num} to {self.filename}. "
                                       f"File may be locked by another application.")

                if frame_num % 30 == 0:
                    elapsed = time.time() - start_time
                    print(f"Progress: {frame_num}/{self.total_frames} - Elapsed: {elapsed:.2f}s")

            self.video_writer.release()
            # Calculate and display total rendering time
            total_time = time.time() - start_time
            print(f"Video generation complete! Total rendering time: {total_time:.2f} seconds")

        except Exception as e:
            # Clean up on any error
            total_time = time.time() - start_time
            self.video_writer.release()
            print(f"ERROR: Video generation failed after {total_time:.2f} seconds - {str(e)}")
            raise

    def _execute_timeline_event(self, event, current_time, current_frame):
        """Execute a timeline event during rendering."""
        if event.event_type == 'create_sprite':
            sprite_id = event.kwargs['sprite_id']
            grid_x = event.kwargs['grid_x']
            grid_y = event.kwargs['grid_y']
            self.scene.add_sprite(sprite_id, grid_x, grid_y, **event.kwargs)

        elif event.event_type == 'start_animation':
            animation = event.kwargs['animation']
            animation['start_time'] = current_time
            # Convert frame duration to time duration
            if 'duration_frames' in animation:
                animation['duration'] = animation['duration_frames'] / self.scene.fps
            self.scene.animation_controller.add_animation(animation)