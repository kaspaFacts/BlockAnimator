import time
import cv2
import numpy as np
import pygame


class VideoRenderer:
    """Renders scene to video."""

    def __init__(self, scene, filename):
        self.scene = scene
        self.filename = filename
        self.fps = scene.fps
        self.total_frames = scene.scene_duration_frames

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
        total_frames = max(1, self.scene.scene_duration_frames)
        print(f"Generating {total_frames} frames...")
        start_time = time.time()

        try:
            for frame_num in range(total_frames):
                sprite_registry = self.scene.dag_manager.get_sprite_registry()
                self.scene.animation_controller.update_sprites(
                    sprite_registry, frame_num
                )

                all_sprites = self.scene.get_all_sprites()

                # Update sprite positions based on current camera
                for sprite in all_sprites:
                    if hasattr(sprite, 'grid_x') and hasattr(sprite, 'grid_y'):
                        pixel_x, pixel_y = self.scene.coords.grid_to_pixel(sprite.grid_x, sprite.grid_y)
                        sprite.set_position(pixel_x, pixel_y)

                # Update connections to follow blocks (now handled by DAG)
                if self.scene.dag_manager.has_dag():
                    self._update_dag_connections()

                # Process timeline events that should trigger at this frame
                for event in self.scene.timeline_events:
                    if not event.executed and frame_num >= event.trigger_frame:
                        self._execute_timeline_event(event, frame_num / self.fps, frame_num)
                        event.executed = True

                        # Render frame
                self.scene.screen.fill((0, 0, 0))
                all_sprites.draw(self.scene.screen)

                # Convert to video format
                frame_array = pygame.surfarray.array3d(self.scene.screen)
                frame_array = np.rot90(frame_array)
                frame_array = np.flipud(frame_array)
                frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)

                # Write frame and check for success
                success = self.video_writer.write(frame_bgr)
                if success is False:
                    raise RuntimeError(f"Failed to write frame {frame_num} to {self.filename}. "
                                       f"File may be locked by another application.")

                if frame_num % 30 == 0:
                    elapsed = time.time() - start_time
                    print(f"Progress: {frame_num}/{total_frames} - Elapsed: {elapsed:.2f}s")

            self.video_writer.release()
            total_time = time.time() - start_time
            print(f"Video generation complete! Total rendering time: {total_time:.2f} seconds")

        except Exception as e:
            total_time = time.time() - start_time
            self.video_writer.release()
            print(f"ERROR: Video generation failed after {total_time:.2f} seconds - {str(e)}")
            raise

    def _update_dag_connections(self):
        """Update all connection lines to follow their blocks using DAG's sprite registry."""
        if not self.scene.dag_manager.has_dag():
            return

        all_sprites = self.scene.dag_manager.get_all_sprites()
        for sprite in all_sprites:
            if hasattr(sprite, 'update_line'):
                sprite.update_line()

    def _execute_timeline_event(self, event, current_time, current_frame):
        """Execute a timeline event during rendering."""
        if event.event_type == 'create_sprite':
            # Timeline events for sprite creation now need to go through DAG
            if self.scene.dag_manager.has_dag():
                sprite_id = event.kwargs['sprite_id']
                grid_x = event.kwargs['grid_x']
                grid_y = event.kwargs['grid_y']
                self.scene.dag_manager.dag_instance.add_sprite(sprite_id, grid_x, grid_y, **event.kwargs)

        elif event.event_type == 'start_animation':
            animation = event.kwargs['animation']
            # The animation already has start_frame set by Scene.play()
            # Just add it to the animation controller
            self.scene.animation_controller.add_animation(animation)