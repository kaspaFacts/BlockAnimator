import pygame
from engine.coordinate_system import CoordinateSystem
from engine.animation_controller import AnimationController
from engine.renderer import VideoRenderer
from engine.sprites.block import *
from engine.sprites.line import Connection

from engine.animations import (
    MoveToAnimation, FadeToAnimation, AlphaChangeAnimation, ColorChangeAnimation,
    ChangeAppearanceAnimation, CameraMoveAnimation, WaitAnimation
)

class TimelineEvent:
    def __init__(self, trigger_frame, event_type, **kwargs):
        self.trigger_frame = trigger_frame
        self.event_type = event_type
        self.kwargs = kwargs
        self.executed = False


class AnimationGroup:
    """Wrapper for simultaneous animations"""

    def __init__(self, animations):
        self.animations = animations if isinstance(animations, list) else [animations]
        self.animation_type = 'simultaneous'


class SequentialAnimations:
    """Wrapper for sequential animation groups"""

    def __init__(self, *animation_groups):
        self.animation_groups = list(animation_groups)
        self.animation_type = 'sequential'

# Convenience functions
def simultaneous(*animations):
    """Create a group of simultaneous animations"""
    return AnimationGroup(list(animations))

def sequential(*groups):
    """Create sequential animation groups"""
    return SequentialAnimations(*groups)

class Scene:
    def __init__(self, resolution='720p', fps=30, field_height=50):

        resolutions = {
            '240p': (432, 240),  # Changed from (426, 240)
            '480p': (848, 480),  # Changed from (854, 480)
            '720p': (1280, 720),  # Already correct
            '1080p': (1920, 1080)  # Already correct
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
        self.animation_controller = AnimationController(fps=self.fps)

        # Use LayeredUpdates instead of regular Group for z-ordering
        self.sprites = pygame.sprite.LayeredUpdates()
        self.sprite_registry = {}

        # Define layer constants for proper z-ordering
        self.CONNECTION_LAYER = 0  # Behind everything
        self.SELECTED_CONNECTION_LAYER = 1  # Selected parent connections
        self.BLOCK_LAYER = 2  # Always on top

        # Frame-based timing only
        self.current_frame = 0
        self.timeline_events = []
        self.scene_duration_frames = 0

    def duration_to_frames(self, duration_seconds):
        """Convert duration in seconds to exact frame count."""
        return round(duration_seconds * self.fps)

    def schedule_at_frame(self, frame, event_type, **kwargs):
        """Schedule an event to happen at a specific frame during rendering."""
        event = TimelineEvent(frame, event_type, **kwargs)
        self.timeline_events.append(event)
        # Update scene duration to include this event
        duration_frames = kwargs.get('duration_frames', 0)
        self.scene_duration_frames = max(self.scene_duration_frames, frame + duration_frames)

    def construct(self):
        """Override this method to define your scene animations."""
        raise NotImplementedError("Subclasses must implement construct()")

    def add_sprite(self, sprite_id, grid_x, grid_y, consensus_type="basic", **kwargs):
        """Add a sprite at grid coordinates with specified consensus type."""
        pixel_x, pixel_y = self.coords.grid_to_pixel(grid_x, grid_y)
        text = kwargs.pop('text', sprite_id)
        parents = kwargs.pop('parents', None)

        # Block type factory
        block_types = {
            "basic": lambda: Block(pixel_x, pixel_y, sprite_id, self.coords.grid_size, text, **kwargs),
            "ghostdag": lambda: GhostdagBlock(pixel_x, pixel_y, sprite_id, self.coords.grid_size, text, parents=parents,
                                              **kwargs),
            "bitcoin": lambda: BitcoinBlock(pixel_x, pixel_y, sprite_id, self.coords.grid_size, text,
                                            parent=parents[0] if parents else None, **kwargs)
        }

        if consensus_type not in block_types:
            raise ValueError(f"Unknown consensus type: {consensus_type}")

        sprite = block_types[consensus_type]()

        # Store grid coordinates in the sprite
        sprite.grid_x = grid_x
        sprite.grid_y = grid_y

        self.sprite_registry[sprite_id] = sprite
        self.sprites.add(sprite, layer=self.BLOCK_LAYER)
        return sprite

    def add_connection(self, connection_id, start_block_id, end_block_id, **kwargs):
        """Enhanced connection creation with GHOSTDAG awareness."""
        start_block = self.sprite_registry.get(start_block_id)
        end_block = self.sprite_registry.get(end_block_id)

        if not start_block or not end_block:
            return None

            # Auto-determine connection properties for GHOSTDAG blocks
        if isinstance(end_block, GhostdagBlock):
            is_selected_parent = (start_block.sprite_id == end_block.ghostdag_data.selected_parent)

            # NEW: Check if connection is blue using the unified mergeset
            is_blue_connection = self._is_blue_connection(start_block.sprite_id, end_block)

            # Auto-determine color based on GHOSTDAG classification
            if 'color' not in kwargs:
                if is_selected_parent:
                    kwargs['color'] = (0, 255, 0)  # Green for selected parent
                elif is_blue_connection:
                    kwargs['color'] = (0, 0, 255)  # Blue for blue blocks
                else:
                    kwargs['color'] = (255, 0, 0)  # Red for red blocks

            kwargs['selected_parent'] = is_selected_parent

            # Create connection with existing logic
        connection = Connection(
            start_block, end_block,
            sprite_id=connection_id,
            grid_size=self.coords.grid_size,
            **kwargs
        )

        self.sprite_registry[connection_id] = connection

        if kwargs.get('selected_parent', False):
            layer = self.SELECTED_CONNECTION_LAYER  # Layer 1
        else:
            layer = self.CONNECTION_LAYER  # Layer 0

        self.sprites.add(connection, layer=layer)
        return connection

    def _is_blue_connection(self, parent_id, child_block):
        """Helper method to determine if a connection represents a blue relationship"""
        if not hasattr(child_block, 'ghostdag_data') or not child_block.ghostdag_data.mergeset:
            return False

            # In the unified mergeset, blues come first (after selected parent)
        # You'll need to implement the logic to determine the blue/red boundary
        # This depends on how you implement the k-cluster validation in your GhostdagData

        # For now, simple approach: check if parent is in first k+1 positions
        # (selected parent + k blues)
        k = getattr(child_block, 'ghostdag_k', 3)
        blue_boundary = min(k + 1, len(child_block.ghostdag_data.mergeset))

        return parent_id in child_block.ghostdag_data.mergeset[:blue_boundary]

    def update_connections(self):
        """Update all connection lines to follow their blocks."""
        for sprite in self.sprites:
            if isinstance(sprite, Connection):
                sprite.update_line()

    def play(self, *args, **kwargs):
        """Universal play method that handles different animation types automatically"""
        if not args:
            return

        def flatten_animations(animations):
            """Recursively flatten nested lists of animations"""
            flattened = []
            for item in animations:
                if isinstance(item, list):
                    flattened.extend(flatten_animations(item))
                elif item is not None:
                    flattened.append(item)
            return flattened

            # Handle different input types

        if len(args) == 1:
            animation_input = args[0]

            # Check if it's a special animation group/sequence object
            if hasattr(animation_input, 'animation_type'):
                if animation_input.animation_type == 'simultaneous':
                    # Flatten the animations in the group
                    flattened_animations = flatten_animations(animation_input.animations)
                    end_frame = self.animation_controller.play_simultaneous(flattened_animations)
                elif animation_input.animation_type == 'sequential':
                    # Flatten each group in the sequence
                    flattened_groups = []
                    for group in animation_input.animation_groups:
                        flattened_groups.append(flatten_animations(group))
                    end_frame = self.animation_controller.play_sequential(flattened_groups)
                else:
                    # Single animation
                    end_frame = self.animation_controller.play_simultaneous([animation_input])
            elif isinstance(animation_input, list):
                # List of animations - flatten and play simultaneously
                flattened_animations = flatten_animations(animation_input)
                end_frame = self.animation_controller.play_simultaneous(flattened_animations)
            else:
                # Single animation
                end_frame = self.animation_controller.play_simultaneous([animation_input])
        else:
            # Multiple arguments - flatten all and play simultaneously
            all_animations = []
            for anim in args:
                if isinstance(anim, list):
                    all_animations.extend(flatten_animations(anim))
                elif anim is not None:
                    all_animations.append(anim)

            end_frame = self.animation_controller.play_simultaneous(all_animations)

            # Update scene timing
        self.current_frame = end_frame
        self.scene_duration_frames = max(self.scene_duration_frames, end_frame)

    def wait(self, duration):
        """Add a wait/pause to the animation timeline"""
        wait_animation = WaitAnimation(
            sprite_id='wait',
            duration=duration
        )

        # Use the animation controller's timing system
        end_frame = self.animation_controller.play_simultaneous([wait_animation])
        self.current_frame = end_frame
        self.scene_duration_frames = max(self.scene_duration_frames, end_frame)

    def render(self, filename=None):
        """Render the scene to video."""
        if filename is None:
            filename = f"{self.__class__.__name__}.mp4"

            # Ensure minimum duration
        if self.scene_duration_frames <= 0:
            self.scene_duration_frames = self.fps  # 1 second minimum

        renderer = VideoRenderer(self, filename)
        renderer.generate_video()

    #####################
    # Block/Line Methods
    #####################

    def move_to(self, sprite_id, target_pos, duration=1.0):
        """Create movement animation using current sprite positions."""
        if sprite_id not in self.sprite_registry:
            return None

        sprite = self.sprite_registry[sprite_id]
        target_x, target_y = target_pos

        return MoveToAnimation(
            sprite_id=sprite_id,
            target_grid_x=target_x,
            target_grid_y=target_y,
            duration=duration
        )

    def fade_to(self, sprite_id, target_alpha, duration=1.0):
        """Create opacity animation for a sprite."""
        if sprite_id not in self.sprite_registry:
            return None

        return FadeToAnimation(
            sprite_id=sprite_id,
            target_alpha=target_alpha,
            duration=duration
        )

    def change_color(self, sprite_id, target_color, duration=1.0):
        """Create color change animation for a sprite."""
        if sprite_id not in self.sprite_registry:
            return None

        return ColorChangeAnimation(
            sprite_id=sprite_id,
            target_color=target_color,
            duration=duration
        )

    def change_alpha(self, sprite_id, target_alpha, duration=1.0):
        """Create color change animation for a sprite."""
        if sprite_id not in self.sprite_registry:
            return None

        return AlphaChangeAnimation(
            sprite_id=sprite_id,
            target_alpha=target_alpha,
            duration=duration
        )

    def change_appearance(self, sprite_id, target_color=None, target_alpha=None, duration=1.0):
        """Create combined color and alpha animation for a sprite."""
        if sprite_id not in self.sprite_registry:
            return None

        return ChangeAppearanceAnimation(
            sprite_id=sprite_id,
            target_color=target_color,
            target_alpha=target_alpha,
            duration=duration
        )

    #####################
    # Camera Movement
    #####################

    def animate_camera_to_sprite(self, sprite_id, duration=1.0):
        """Create an animation to move camera to sprite."""
        if sprite_id in self.sprite_registry:
            sprite = self.sprite_registry[sprite_id]

            # Calculate field dimensions
            aspect_ratio = self.width / self.height
            horizontal_field = 50 * aspect_ratio

            # Center camera on sprite by offsetting by half the visible field
            target_x = sprite.grid_x - (horizontal_field / 2)
            target_y = sprite.grid_y - (25)

            return CameraMoveAnimation(
                sprite_id='camera',
                target_x=target_x,
                target_y=target_y,
                duration=duration,
                scene=self
            )
        return None

    def animate_camera_move(self, delta_x, delta_y, duration=1.0):
        """Create an animation to move camera by offset."""
        return CameraMoveAnimation(
            sprite_id='camera',
            target_x=self.coords.camera_x + delta_x,
            target_y=self.coords.camera_y + delta_y,
            duration=duration,
            scene=self
        )