# engine/scene.py
import pygame
from engine.coordinate_system import CoordinateSystem
from engine.animation_controller import AnimationController
from engine.renderer import VideoRenderer
from engine.sprites.block import Block
from engine.sprites.line import Connection


class TimelineEvent:
    def __init__(self, trigger_frame, event_type, **kwargs):
        self.trigger_frame = trigger_frame
        self.event_type = event_type
        self.kwargs = kwargs
        self.executed = False

class Scene:
    def __init__(self, resolution='720p', fps=30, field_height=50):

        resolutions = {
            '240p': (426, 240),
            '480p': (854, 480),
            '720p': (1280, 720),
            '1080p': (1920, 1080)
        }

        self.width, self.height = resolutions[resolution]
        self.fps = fps

        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.HIDDEN)

        # Proportional coordinate system
        self.coords = CoordinateSystem(
            self.width, self.height,
            field_height=field_height
        )

        # Animation system
        self.animation_controller = AnimationController()

        # Use LayeredUpdates instead of regular Group for z-ordering
        self.sprites = pygame.sprite.LayeredUpdates()
        self.sprite_registry = {}

        # Define layer constants for proper z-ordering
        self.CONNECTION_LAYER = 0  # Behind everything
        self.BLOCK_LAYER = 1       # On top of connections

        # Timing
        self.current_time = 0.0
        self.scene_duration = 0.0

        self.timeline_events = []  # Add this new attribute
        self.scene_duration_frames = 0  # Add this new attribute

    def schedule_at_frame(self, frame, event_type, **kwargs):
        """Schedule an event to happen at a specific frame during rendering."""
        event = TimelineEvent(frame, event_type, **kwargs)
        self.timeline_events.append(event)
        # Update scene duration to include this event
        duration_frames = kwargs.get('duration_frames', 0)
        self.scene_duration_frames = max(self.scene_duration_frames, frame + duration_frames)
        # Convert to time for compatibility
        self.scene_duration = self.scene_duration_frames / self.fps

    def construct(self):
        """Override this method to define your scene animations."""
        raise NotImplementedError("Subclasses must implement construct()")

    def add_sprite(self, sprite_id, grid_x, grid_y, **kwargs):
        """Add a sprite at grid coordinates."""
        pixel_x, pixel_y = self.coords.grid_to_pixel(grid_x, grid_y)

        text = kwargs.pop('text', sprite_id)

        sprite = Block(
            pixel_x, pixel_y,
            sprite_id=sprite_id,
            grid_size=self.coords.grid_size,  # Automatically pass grid_size
            text=text,
            **kwargs
        )

        # Store grid coordinates in the sprite
        sprite.grid_x = grid_x
        sprite.grid_y = grid_y

        self.sprite_registry[sprite_id] = sprite
        # Add sprite to BLOCK_LAYER so it appears on top of connections
        self.sprites.add(sprite, layer=self.BLOCK_LAYER)
        return sprite

    def add_connection(self, connection_id, start_block_id, end_block_id, **kwargs):
        """Add a connection line between two blocks."""
        start_block = self.sprite_registry.get(start_block_id)
        end_block = self.sprite_registry.get(end_block_id)

        if not start_block or not end_block:
            return None

        connection = Connection(
            start_block, end_block,
            sprite_id=connection_id,
            color=kwargs.get('color', (255, 255, 255)),
            width=kwargs.get('width', 2)
        )

        self.sprite_registry[connection_id] = connection
        # Add connection to CONNECTION_LAYER so it appears behind blocks
        self.sprites.add(connection, layer=self.CONNECTION_LAYER)

        # Register connection as an alpha observer for both blocks
        start_block.alpha_observers.append(connection)
        end_block.alpha_observers.append(connection)

        # Initialize connection alpha to match start block's alpha
        connection.set_alpha(start_block.alpha)

        return connection

    def update_connections(self):
        """Update all connection lines to follow their blocks."""
        for sprite in self.sprites:
            if isinstance(sprite, Connection):
                sprite.update_line()

    def play(self, *animations, duration=1.0):
        """Convert time-based play to frame-based scheduling."""
        current_frame = int(self.current_time * self.fps)

        # Flatten any nested lists of animations first
        flattened_animations = []
        for anim in animations:
            if isinstance(anim, list):
                flattened_animations.extend(anim)
            elif anim is not None:  # Handle None animations
                flattened_animations.append(anim)

        for animation in flattened_animations:
            if animation:  # Double-check it's not None
                duration_frames = int(duration * self.fps)
                animation['duration_frames'] = duration_frames
                self.schedule_at_frame(current_frame, 'start_animation', animation=animation)

                # Update current time and frame tracking
        self.current_time += duration
        self.scene_duration_frames = max(self.scene_duration_frames, int(self.current_time * self.fps))
        self.scene_duration = max(self.scene_duration, self.current_time)

    def wait(self, duration):
        """Add a pause in frames."""
        self.current_time += duration
        wait_frames = int(duration * self.fps)
        self.scene_duration_frames = max(self.scene_duration_frames, int(self.current_time * self.fps))
        self.scene_duration = max(self.scene_duration, self.current_time)

    def render(self, filename=None):
        """Render the scene to video."""
        if filename is None:
            filename = f"{self.__class__.__name__}.mp4"

        # Ensure minimum duration
        if self.scene_duration <= 0:
            self.scene_duration = 1.0

        renderer = VideoRenderer(self, filename)
        renderer.generate_video()

    def move_to(self, sprite_id, target_pos, duration=1.0):
        """Create movement animation using current sprite positions."""
        if sprite_id not in self.sprite_registry:
            return None

        sprite = self.sprite_registry[sprite_id]
        start_x, start_y = sprite.grid_x, sprite.grid_y
        target_x, target_y = target_pos

        return {
            'type': 'move_to',
            'sprite_id': sprite_id,
            'start_grid_x': start_x,
            'start_grid_y': start_y,
            'target_grid_x': target_x,
            'target_grid_y': target_y,
            'duration': duration
        }

    def animate_camera_to_sprite(self, sprite_id, duration=1.0):
        """Create an animation to move camera to sprite."""
        if sprite_id in self.sprite_registry:
            sprite = self.sprite_registry[sprite_id]

            # Calculate field dimensions
            aspect_ratio = self.width / self.height
            horizontal_field = 50 * aspect_ratio  # 50 is your field_height

            # Center camera on sprite by offsetting by half the visible field
            target_x = sprite.grid_x - (horizontal_field / 2)
            target_y = sprite.grid_y - (25)  # 25 is half of field_height (50)

            return {
                'type': 'camera_move',
                'sprite_id': 'camera',
                'target_x': target_x,
                'target_y': target_y,
                'duration': duration,
                'scene': self
            }
        return None

    def animate_camera_move(self, delta_x, delta_y, duration=1.0):
        """Create an animation to move camera by offset."""
        return {
            'type': 'camera_move',
            'sprite_id': 'camera',
            'delta_x': delta_x,
            'delta_y': delta_y,
            'duration': duration,
            'scene': self
        }