import pygame
import math


class Connection(pygame.sprite.DirtySprite):
    """A line connection between two blocks using DirtySprite for optimized rendering."""

    def __init__(self, start_block, end_block, sprite_id, color=(255, 255, 255), width=2):
        super().__init__()

        self.sprite_id = sprite_id
        self.start_block = start_block
        self.end_block = end_block
        self.color = color
        self.line_width = width

        self.is_fading_in = False
        # Visual properties - start invisible for animation control
        self.alpha = 0
        self._visible = 0  # Start invisible, let animation controller handle this

        # DirtySprite specific attributes
        self.dirty = 1
        self.blendmode = 0
        self.source_rect = None
        self._layer = 0

        # Initialize the line
        self.update_line()

    @property
    def visible(self):
        """Get visibility state."""
        return self._visible

    @visible.setter
    def visible(self, value):
        """Set visibility and mark as dirty if changed."""
        if self._visible != value:
            self._visible = value
            if self.dirty < 2:
                self.dirty = 1
            self.update_line()

    def update_line(self):
        """Update the line based on current block positions."""
        if not (self.start_block and self.end_block):
            return

        start_center_x, start_center_y = self.start_block.x, self.start_block.y
        end_center_x, end_center_y = self.end_block.x, self.end_block.y

        start_half_size = self.start_block.size // 2
        end_half_size = self.end_block.size // 2

        # Calculate initial edge connection points
        start_x = start_center_x - start_half_size
        start_y = start_center_y
        end_x = end_center_x + end_half_size
        end_y = end_center_y

        # Calculate direction vector of the line
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.sqrt(dx * dx + dy * dy)

        if length == 0:
            return

            # Normalize the direction vector
        unit_dx = dx / length
        unit_dy = dy / length

        # Apply configurable margin to shorten the arrow tip side
        # The arrow tip will be drawn at 'adjusted_end_x, adjusted_end_y'
        # This pulls the end point back from the block's edge
        arrow_tip_margin = 15  # Example configurable margin in pixels
        adjusted_end_x = end_x - unit_dx * arrow_tip_margin
        adjusted_end_y = end_y - unit_dy * arrow_tip_margin

        # Create surface large enough for the line (using original end_x, end_y for rect calculation)
        margin = self.line_width + 2
        width = int(abs(dx) + margin * 2)
        height = int(abs(dy) + margin * 2)

        self.image = pygame.Surface((width, height), pygame.SRCALPHA)

        # Calculate line start/end points on the surface
        surface_start_x = margin if dx >= 0 else width - margin
        surface_start_y = margin if dy >= 0 else height - margin

        # Use adjusted_end_x, adjusted_end_y for drawing the line and arrow
        # These need to be relative to the surface's top-left
        surface_adjusted_end_x = surface_start_x + (adjusted_end_x - start_x)
        surface_adjusted_end_y = surface_start_y + (adjusted_end_y - start_y)

        if self._visible:
            self.draw_arrow(
                self.image,
                (surface_start_x, surface_start_y),
                (surface_adjusted_end_x, surface_adjusted_end_y),
                arrow_length=10  # This is the length of the arrow head itself
            )

            # Position the surface (using original min(start_x, end_x) for overall rect)
        self.rect = self.image.get_rect()
        self.rect.topleft = (
            min(start_x, end_x) - margin,
            min(start_y, end_y) - margin
        )

        self.image.set_alpha(self.alpha)
        if self.dirty < 2:
            self.dirty = 1

    def set_alpha(self, alpha):
        """Set line alpha and mark as dirty."""
        if self.alpha != alpha:
            self.alpha = alpha
            self.update_line()

    def set_visible(self, visible):
        """Set line visibility using the property."""
        self.visible = 1 if visible else 0

    def set_color(self, color):
        """Set line color and mark as dirty."""
        if self.color != color:
            self.color = color
            self.update_line()

    def set_width(self, width):
        """Set line width and mark as dirty."""
        if self.line_width != width:
            self.line_width = width
            self.update_line()

    def draw_arrow(self, surface, start, end, arrow_length=10):
        """Draw an arrow instead of a simple line."""
        # Draw main line  
        pygame.draw.line(surface, self.color, start, end, self.line_width)

        # Calculate arrow head  
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        arrow_angle = math.pi / 6

        # Arrow head points  
        p1 = (
            end[0] - arrow_length * math.cos(angle - arrow_angle),
            end[1] - arrow_length * math.sin(angle - arrow_angle)
        )
        p2 = (
            end[0] - arrow_length * math.cos(angle + arrow_angle),
            end[1] - arrow_length * math.sin(angle + arrow_angle)
        )

        # Draw arrow head  
        pygame.draw.polygon(surface, self.color, [end, p1, p2])

    def update_as_arrow(self, arrow_length=10):
        """Update the connection as an arrow instead of a line."""
        if not (self.start_block and self.end_block):
            return

            # Calculate line endpoints
        start_x, start_y = self.start_block.x, self.start_block.y
        end_x, end_y = self.end_block.x, self.end_block.y

        # Calculate line dimensions (account for arrow head)  
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.sqrt(dx * dx + dy * dy)

        if length == 0:
            return

            # Create surface large enough for the arrow
        margin = max(self.line_width + 2, arrow_length + 2)
        width = int(abs(dx) + margin * 2)
        height = int(abs(dy) + margin * 2)

        self.image = pygame.Surface((width, height), pygame.SRCALPHA)

        # Calculate arrow start/end points on the surface  
        surface_start_x = margin if dx >= 0 else width - margin
        surface_start_y = margin if dy >= 0 else height - margin
        surface_end_x = width - margin if dx >= 0 else margin
        surface_end_y = height - margin if dy >= 0 else margin

        # Draw the arrow only if visible  
        if self._visible:
            self.draw_arrow(
                self.image,
                (surface_start_x, surface_start_y),
                (surface_end_x, surface_end_y),
                arrow_length
            )

            # Position the surface
        self.rect = self.image.get_rect()
        self.rect.topleft = (
            min(start_x, end_x) - margin,
            min(start_y, end_y) - margin
        )

        # Always apply alpha  
        self.image.set_alpha(self.alpha)

        # Mark as dirty for next render  
        if self.dirty < 2:
            self.dirty = 1