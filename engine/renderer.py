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
        # Fix: Use scene_duration_frames directly instead of scene_duration  
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
        # Fix: Use scene_duration_frames directly  
        total_frames = max(1, self.scene.scene_duration_frames)  
        print(f"Generating {total_frames} frames...")  
        start_time = time.time()  
  
        try:  
            for frame_num in range(total_frames):  
                # Fix: Pass frame_num instead of current_time to update_sprites  
                # since AnimationController.update_sprites expects frame numbers  
                self.scene.animation_controller.update_sprites(  
                    self.scene.sprite_registry, frame_num  
                )  
  
                # Update sprite positions based on current camera  
                for sprite in self.scene.sprites:  
                    if hasattr(sprite, 'grid_x') and hasattr(sprite, 'grid_y'):  
                        pixel_x, pixel_y = self.scene.coords.grid_to_pixel(sprite.grid_x, sprite.grid_y)  
                        sprite.set_position(pixel_x, pixel_y)  
  
                # Update connections to follow blocks  
                self.scene.update_connections()  
  
                # Process timeline events that should trigger at this frame  
                for event in self.scene.timeline_events:  
                    if not event.executed and frame_num >= event.trigger_frame:  
                        self._execute_timeline_event(event, frame_num / self.fps, frame_num)  
                        event.executed = True  
  
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

    def _execute_timeline_event(self, event, current_time, current_frame):
        """Execute a timeline event during rendering."""
        if event.event_type == 'create_sprite':
            sprite_id = event.kwargs['sprite_id']
            grid_x = event.kwargs['grid_x']
            grid_y = event.kwargs['grid_y']
            self.scene.add_sprite(sprite_id, grid_x, grid_y, **event.kwargs)

        elif event.event_type == 'start_animation':
            animation = event.kwargs['animation']
            # The animation already has start_frame set by Scene.play()
            # Just add it to the animation controller
            self.scene.animation_controller.add_animation(animation)