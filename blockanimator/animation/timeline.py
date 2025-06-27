# BlockAnimator\blockanimator\animation\timeline.py

from .groups import TimelineEvent


class Timeline:
    def __init__(self, fps=30):
        self.fps = fps
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

    def update_timing(self, end_frame):
        """Update current frame and scene duration."""
        self.current_frame = end_frame
        self.scene_duration_frames = max(self.scene_duration_frames, end_frame)