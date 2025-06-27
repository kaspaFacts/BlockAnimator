# BlockAnimator\blockanimator\animation\proxy.py

from .anim_types import MoveToAnimation, FadeToAnimation, ColorChangeAnimation


class BlockAnimationProxy:
    def __init__(self, block):
        self.block = block
        self.scene = None  # This will be set by the Scene when the block is added

    def move_to(self, target_pos, duration=1.0):
        """Create movement animation for this block."""
        target_x, target_y = target_pos
        return MoveToAnimation(
            sprite_id=self.block.sprite_id,
            target_grid_x=target_x,
            target_grid_y=target_y,
            duration=duration
        )

    def fade_to(self, target_alpha, duration=1.0):
        """Create fade animation for this block."""
        return FadeToAnimation(
            sprite_id=self.block.sprite_id,
            target_alpha=target_alpha,
            duration=duration
        )

    def change_color(self, target_color, duration=1.0):
        """Create color change animation for this block."""
        return ColorChangeAnimation(
            sprite_id=self.block.sprite_id,
            target_color=target_color,
            duration=duration
        )