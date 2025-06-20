# engine/scene.py
import pygame
from engine.coordinate_system import CoordinateSystem
from engine.animation_controller import AnimationController
from engine.renderer import VideoRenderer
from engine.sprites.block import Block
from engine.sprites.line import Connection


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
            field_height=field_height,
            base_resolution=resolution  # Reference resolution
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

        # Camera position tracking for animation chaining
        self.expected_camera_x = 0.0
        self.expected_camera_y = 0.0

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
        """Play animations sequentially."""
        start_time = self.current_time

        # Flatten any nested lists of animations
        flattened_animations = []
        for anim in animations:
            if isinstance(anim, list):
                flattened_animations.extend(anim)
            else:
                flattened_animations.append(anim)

        for animation in flattened_animations:
            # For camera animations, use tracking variables instead of actual camera position
            if animation.get('type') == 'camera_move':
                animation['start_x'] = self.expected_camera_x
                animation['start_y'] = self.expected_camera_y

                # Update our tracking of where camera will be after this animation
                if 'target_x' in animation:
                    self.expected_camera_x = animation['target_x']
                    self.expected_camera_y = animation['target_y']
                elif 'delta_x' in animation:
                    animation['target_x'] = self.expected_camera_x + animation['delta_x']
                    animation['target_y'] = self.expected_camera_y + animation['delta_y']
                    self.expected_camera_x = animation['target_x']
                    self.expected_camera_y = animation['target_y']

            anim_duration = animation.get('duration', duration)
            animation['start_time'] = start_time
            animation['duration'] = anim_duration
            self.animation_controller.add_animation(animation)

        self.current_time += duration
        self.scene_duration = max(self.scene_duration, self.current_time)

    def wait(self, duration):
        """Add a pause."""
        self.current_time += duration
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

    def move_sprite_to(self, sprite_id, target_grid_pos, run_time=1.0):
        """Move any sprite to absolute grid position."""
        if sprite_id not in self.sprite_registry:
            return None

        sprite = self.sprite_registry[sprite_id]
        current_x, current_y = sprite.grid_x, sprite.grid_y
        target_x, target_y = target_grid_pos

        return {
            'type': 'move_to',
            'sprite_id': sprite_id,
            'start_grid_x': current_x,
            'start_grid_y': current_y,
            'target_grid_x': target_x,
            'target_grid_y': target_y
        }

    def center_camera_on_sprite(self, sprite_id):
        """Center camera on a specific sprite."""
        if sprite_id in self.sprite_registry:
            # Find the sprite's grid position
            for block_id, block_data in getattr(self, '_block_positions', {}).items():
                if block_id == sprite_id:
                    grid_pos = block_data['grid_pos']
                    self.coords.set_camera_position(grid_pos[0], grid_pos[1])
                    return

            # If not found in block positions, calculate from pixel position
            sprite = self.sprite_registry[sprite_id]
            grid_x, grid_y = self.coords.pixel_to_grid(sprite.x, sprite.y)
            self.coords.set_camera_position(grid_x, grid_y)

    def move_camera(self, delta_x, delta_y):
        """Move camera by grid steps."""
        self.coords.move_camera(delta_x, delta_y)

    def set_camera_position(self, grid_x, grid_y):
        """Set absolute camera position."""
        self.coords.set_camera_position(grid_x, grid_y)

    def animate_camera_to_sprite(self, sprite_id, duration=1.0):
        """Create an animation to move camera to sprite."""
        if sprite_id in self._block_positions:
            grid_pos = self._block_positions[sprite_id]['grid_pos']
            return {
                'type': 'camera_move',
                'sprite_id': 'camera',
                'target_x': grid_pos[0],
                'target_y': grid_pos[1],
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