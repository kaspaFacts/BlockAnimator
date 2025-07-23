# BlockAnimator\blockanimator\animation\proxy.py

from .anim_types import MoveToAnimation, FadeToAnimation, ColorChangeAnimation, RelativeMoveAnimation


class BlockAnimationProxy:
    def __init__(self, block):
        self.block = block
        self.scene = None
        self.pending_animations = []  # Collect chained animations

    def shift(self, offset, duration=1.0):
        """Move block by grid offset (x, y)."""
        animation = RelativeMoveAnimation(
            sprite_id=self.block.sprite_id,
            offset=offset,
            duration=duration
        )
        self.pending_animations.append(animation)
        return self  # Enable chaining

    def fade_to(self, target_alpha, duration=1.0):
        """Create fade animation for this block."""
        animation = FadeToAnimation(
            sprite_id=self.block.sprite_id,
            target_alpha=target_alpha,
            duration=duration
        )
        self.pending_animations.append(animation)
        return self  # Enable chaining

    def fade_in(self, duration=1.0):
        """Fade block in to full opacity."""
        return self.fade_to(255, duration)

    def fade_out(self, duration=1.0):
        """Fade block out to transparent."""
        return self.fade_to(0, duration)

    def moveX(self, grid_offset, duration=1.0):
        """Move block by grid offset in X direction."""
        animation = RelativeMoveAnimation(
            sprite_id=self.block.sprite_id,
            offset=(grid_offset, 0),
            duration=duration
        )
        self.pending_animations.append(animation)
        return self

    def moveY(self, grid_offset, duration=1.0):
        """Move block by grid offset in Y direction."""
        animation = RelativeMoveAnimation(
            sprite_id=self.block.sprite_id,
            offset=(0, grid_offset),
            duration=duration
        )
        self.pending_animations.append(animation)
        return self

    def change_color(self, target_color, duration=1.0):
        """Create color change animation for this block."""
        animation = ColorChangeAnimation(
            sprite_id=self.block.sprite_id,
            target_color=target_color,
            duration=duration
        )
        self.pending_animations.append(animation)
        return self

    def move_to(self, target_pos, duration=1.0):
        """Move block to absolute grid position (x, y)."""
        target_x, target_y = target_pos
        animation = MoveToAnimation(
            sprite_id=self.block.sprite_id,
            target_grid_x=target_x,
            target_grid_y=target_y,
            duration=duration
        )
        self.pending_animations.append(animation)
        return self