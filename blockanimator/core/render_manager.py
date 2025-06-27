# BlockAnimator\blockanimator\core\render_manager.py

from .renderer import VideoRenderer


class RenderManager:
    def __init__(self):
        pass

    def render(self, scene, filename=None):
        """Handle video rendering coordination."""
        if filename is None:
            filename = f"{scene.__class__.__name__}.mp4"

            # Ensure minimum duration
        if scene.timeline.scene_duration_frames <= 0:
            scene.timeline.scene_duration_frames = scene.fps  # 1 second minimum

        renderer = VideoRenderer(scene, filename)
        renderer.generate_video()