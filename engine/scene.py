import pygame
from engine.coordinate_system import CoordinateSystem
from engine.animation_controller import AnimationController
from engine.renderer import VideoRenderer

from engine.animations.animations import (
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
            '240p': (432, 240),
            '480p': (848, 480),
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
        self.animation_controller = AnimationController(fps=self.fps)

        # Frame-based timing only
        self.current_frame = 0
        self.timeline_events = []
        self.scene_duration_frames = 0

        # Single DAG reference instead of list
        self.dag_instance = None

    def register_dag(self, dag_instance):
        """Register the single DAG instance for rendering access to its sprites."""
        self.dag_instance = dag_instance
        # When a DAG is registered, ensure its sprites' animation proxies know about the scene
        for sprite_id, sprite in dag_instance.sprite_registry.items():
            if hasattr(sprite, 'animate'):
                sprite.animate.scene = self

    def get_all_sprites(self):
        """Get all sprites from the registered DAG instance for rendering."""
        if self.dag_instance:
            return self.dag_instance.sprites
        else:
            return pygame.sprite.LayeredUpdates()

    def get_sprite_by_id(self, sprite_id):
        """Find a sprite by ID in the DAG instance."""
        if self.dag_instance and sprite_id in self.dag_instance.sprite_registry:
            return self.dag_instance.sprite_registry[sprite_id]
        return None

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

    # Camera Movement (Scene-level functionality)
    #####################

    def animate_camera_to_sprite(self, sprite_id, duration=1.0):
        """Create an animation to move camera to sprite."""
        sprite = self.get_sprite_by_id(sprite_id)
        if sprite:
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