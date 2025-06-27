# BlockAnimator\blockanimator\core\scene.py

from blockanimator.animation.controller import AnimationController
from blockanimator.animation import Timeline
from blockanimator.animation import AnimationOrchestrator
from ..consensus.manager import ConsensusManager
from ..utils.config import DisplayConfig
from .render_manager import RenderManager
from .coordinate_system import CoordinateSystem
from .camera import CameraController

class Scene:
    def __init__(self, resolution='720p', fps=30, field_height=50):
        # Core setup using display config
        self.width, self.height, self.screen = DisplayConfig.setup(resolution)
        self.fps = fps

        # Initialize subsystems
        self.coords = CoordinateSystem(self.width, self.height, field_height=field_height)
        self.animation_controller = AnimationController(fps=self.fps)
        self.timeline = Timeline(fps)
        self.camera = CameraController(self)
        self.animation_orchestrator = AnimationOrchestrator(self.animation_controller, self.timeline)
        self.dag_manager = ConsensusManager()
        self.render_manager = RenderManager()

    def register_dag(self, dag_instance):
        """Delegate DAG registration to the DAG manager."""
        return self.dag_manager.register_dag(dag_instance, self)

    def get_all_sprites(self):
        """Delegate sprite access to the DAG manager."""
        return self.dag_manager.get_all_sprites()

    def get_sprite_by_id(self, sprite_id):
        """Delegate sprite lookup to the DAG manager."""
        return self.dag_manager.get_sprite_by_id(sprite_id)

    def construct(self):
        """Override this method to define your scene animations."""
        raise NotImplementedError("Subclasses must implement construct()")

    def play(self, *args, **kwargs):
        """Delegate animation orchestration to the orchestrator."""
        return self.animation_orchestrator.play(*args, **kwargs)

    def wait(self, duration):
        """Delegate wait functionality to the orchestrator."""
        return self.animation_orchestrator.wait(duration)

    def render(self, filename=None):
        """Delegate rendering to the render manager."""
        return self.render_manager.render(self, filename)

        # Properties to maintain compatibility with existing code

    @property
    def current_frame(self):
        return self.timeline.current_frame

    @current_frame.setter
    def current_frame(self, value):
        self.timeline.current_frame = value

    @property
    def scene_duration_frames(self):
        return self.timeline.scene_duration_frames

    @scene_duration_frames.setter
    def scene_duration_frames(self, value):
        self.timeline.scene_duration_frames = value

    @property
    def timeline_events(self):
        return self.timeline.timeline_events