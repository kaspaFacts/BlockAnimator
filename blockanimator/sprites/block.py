# BlockAnimator/blockanimator/sprites/block.py

import pygame
from blockanimator.animation import BlockAnimationProxy


class Block(pygame.sprite.Sprite):
    """
    Base block sprite for any consensus mechanism.
    Handles basic rendering, positioning, and visual properties only.
    Consensus logic is handled by the consensus/blocks/ system.
    """

    def __init__(self, x, y, sprite_id, grid_size, text="Block", color=(0, 0, 255)):
        super().__init__()

        # Core visual properties
        self.size = int(grid_size * 4)  # 400% of grid unit
        self.grid_size = grid_size
        self.sprite_id = sprite_id
        self.color = color
        self.text = text

        # Create surface
        self.image = pygame.Surface((self.size + 10, self.size + 10), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

        # Store both pixel and grid positions
        self.x = float(x)
        self.y = float(y)
        self.grid_x = None  # Will be set by scene
        self.grid_y = None  # Will be set by scene
        self.grid_pos = None  # Initialize with position

        # Visual properties
        self.alpha = 0
        self.visible = False

        # List of connections observing this block's alpha
        self.alpha_observers = []

        # Calculate font size proportionally to grid_size
        font_size = max(int(grid_size * 2), 8)  # 200% of grid unit, minimum 8px

        # Font
        pygame.font.init()
        self.font = pygame.font.Font(None, font_size)

        self._animate = None  # Initialize the animate property

        self.render()

    @property
    def animate(self):
        """Return an animation proxy for this block."""
        if self._animate is None:
            self._animate = BlockAnimationProxy(self)
        return self._animate

    def render(self):
        """Render the block with consensus-specific customizations."""
        self.image.fill((0, 0, 0, 0))

        if not self.visible:
            return

            # Draw block
        block_rect = pygame.Rect(5, 5, self.size, self.size)
        pygame.draw.rect(self.image, self.color, block_rect)

        # Get consensus-specific outline properties
        outline_color, outline_width = self.get_outline_properties()
        pygame.draw.rect(self.image, outline_color, block_rect, outline_width)

        # Draw consensus-specific text
        display_text = self.get_display_text()
        self.render_text(display_text, block_rect)

        # Always apply alpha
        self.image.set_alpha(self.alpha)

    def get_outline_properties(self):
        """Get outline color and width. Override in subclasses for consensus-specific styling."""
        outline_color = (255, 255, 255)  # Default white
        outline_width = max(int(self.grid_size * 0.25), 1)  # 25% of grid unit, minimum 1px
        return outline_color, outline_width

    def get_display_text(self):
        """Get text to display. Override in subclasses for consensus-specific info."""
        return self.text

    def render_text(self, display_text, block_rect):
        """Render text on the block."""
        text_lines = display_text.split('\n')

        for i, line in enumerate(text_lines):
            text_surface = self.font.render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect(
                center=(block_rect.centerx, block_rect.centery + i * 15)
            )
            self.image.blit(text_surface, text_rect)

    def set_position(self, x, y):
        """Set sprite position."""
        self.x = float(x)
        self.y = float(y)
        self.rect.center = (int(x), int(y))

    def set_alpha(self, alpha):
        """Set sprite alpha."""
        if self.alpha != alpha:
            self.alpha = alpha
            self.render()
            # Notify observers
            for observer in self.alpha_observers:
                observer.on_alpha_change(alpha)

    def set_visible(self, visible):
        """Set sprite visibility."""
        self.visible = visible
        self.render()

    def set_color(self, color):
        """Set sprite color."""
        self.color = color
        self.render()


class BitcoinBlock(Block):
    """
    Bitcoin-specific visual block sprite.
    Visual representation only - consensus logic handled by consensus/blocks/nakamoto_consensus/
    """

    def __init__(self, x, y, sprite_id, grid_size, text="Block", color=(255, 165, 0),
                 parent: str = None, **kwargs):
        super().__init__(x, y, sprite_id, grid_size, text, color)

        # Store parent info for visual display only
        # Actual consensus logic is in BitcoinBlock from consensus/blocks/
        self.parent = parent
        self.parents = [parent] if parent else []

    def get_display_text(self):
        """Bitcoin-specific text display."""
        if self.parent:
            return f"{self.text}\nParent: {self.parent[:6]}..."
        else:
            return f"{self.text}\n(Genesis)"

    def get_outline_properties(self):
        """Bitcoin-specific orange outline."""
        outline_color = (255, 140, 0)  # Orange outline for Bitcoin
        outline_width = max(int(self.grid_size * 0.3), 2)  # Slightly thicker
        return outline_color, outline_width


class GhostdagBlock(Block):
    """
    GHOSTDAG-specific visual block sprite.
    Visual representation only - consensus logic handled by consensus/blocks/ghostdag/
    """

    def __init__(self, x, y, sprite_id, grid_size, text="Block", color=(0, 0, 255),
                 parents: list = None, logical_block=None, **kwargs):
        super().__init__(x, y, sprite_id, grid_size, text, color)

        # Store parent info for visual display only
        self.parents = parents or []

        # Reference to logical block for getting consensus data
        # This is set by VisualBlock wrapper in the new system
        self.logical_block = logical_block

    def get_display_text(self):
        """GHOSTDAG-specific text display - get data from logical block if available."""
        if (self.logical_block and
                hasattr(self.logical_block, 'consensus_data') and
                self.logical_block.consensus_data and
                hasattr(self.logical_block.consensus_data, 'blue_score')):
            return f"{self.text}\nBS:{self.logical_block.consensus_data.blue_score}"
        else:
            # Fallback display when no logical block is connected
            return f"{self.text}\nBS:?"

    def get_outline_properties(self):
        """GHOSTDAG-specific blue outline."""
        outline_color = (100, 150, 255)  # Light blue outline for GHOSTDAG
        outline_width = max(int(self.grid_size * 0.25), 1)  # Standard width
        return outline_color, outline_width