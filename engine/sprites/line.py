# engine/sprites/line.py
import pygame
import math


class Connection(pygame.sprite.Sprite):
    """A line connection between two blocks."""

    def __init__(self, start_block, end_block, sprite_id, color=(255, 255, 255), width=2):
        super().__init__()

        self.sprite_id = sprite_id
        self.start_block = start_block
        self.end_block = end_block
        self.color = color
        self.line_width = width

        # Visual properties
        self.alpha = 0
        self.visible = False

        self.update_line()

    def update_line(self):
        """Update the line based on current block positions."""
        if not (self.start_block and self.end_block):
            return

            # Calculate line endpoints
        start_x, start_y = self.start_block.x, self.start_block.y
        end_x, end_y = self.end_block.x, self.end_block.y

        # Calculate line dimensions
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.sqrt(dx * dx + dy * dy)

        if length == 0:
            return

            # Create surface large enough for the line
        margin = self.line_width + 2
        width = int(abs(dx) + margin * 2)
        height = int(abs(dy) + margin * 2)

        self.image = pygame.Surface((width, height), pygame.SRCALPHA)

        # Calculate line start/end points on the surface
        surface_start_x = margin if dx >= 0 else width - margin
        surface_start_y = margin if dy >= 0 else height - margin
        surface_end_x = width - margin if dx >= 0 else margin
        surface_end_y = height - margin if dy >= 0 else margin

        # Draw the line
        if self.visible:
            pygame.draw.line(
                self.image,
                self.color,
                (surface_start_x, surface_start_y),
                (surface_end_x, surface_end_y),
                self.line_width
            )

            # Position the surface
        self.rect = self.image.get_rect()
        self.rect.topleft = (
            min(start_x, end_x) - margin,
            min(start_y, end_y) - margin
        )

        # Apply alpha
        if self.alpha < 255:
            self.image.set_alpha(self.alpha)

    def set_alpha(self, alpha):
        """Set line alpha."""
        self.alpha = alpha
        self.update_line()

    def set_visible(self, visible):
        """Set line visibility."""
        self.visible = visible
        self.update_line()

    def set_color(self, color):
        """Set line color."""
        self.color = color
        self.update_line()

    def on_alpha_change(self, new_alpha):

        """Callback when an observed block's alpha changes."""

        self.set_alpha(new_alpha)