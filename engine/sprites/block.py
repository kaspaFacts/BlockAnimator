# engine/sprites/block.py
import pygame


class Block(pygame.sprite.Sprite):
    """A simple block sprite."""

    def __init__(self, x, y, sprite_id, grid_size, text="Block", color=(255, 0, 0)):
        super().__init__()

        # Always calculate size based on grid_size (no fallback)
        self.size = int(grid_size * 5)  # 500% of grid unit
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

        # Visual properties
        self.alpha = 0
        self.visible = False

        # List of connections observing this block's alpha
        self.alpha_observers = []

        # Calculate font size proportionally to grid_size
        font_size = max(int(grid_size * 2), 8)  # 30% of grid unit, minimum 8px

        # Font
        pygame.font.init()
        self.font = pygame.font.Font(None, font_size)

        self.render()

    def render(self):
        """Render the block."""
        self.image.fill((0, 0, 0, 0))

        if not self.visible:
            return

            # Draw block
        block_rect = pygame.Rect(5, 5, self.size, self.size)
        pygame.draw.rect(self.image, self.color, block_rect)
        # Calculate outline width proportionally to grid_size
        outline_width = max(int(self.grid_size * 0.25), 1)  # 10% of grid unit, minimum 1px
        pygame.draw.rect(self.image, (255, 255, 255), block_rect, outline_width)

        # Draw text
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=block_rect.center)
        self.image.blit(text_surface, text_rect)

        # Apply alpha
        if self.alpha < 255:
            self.image.set_alpha(self.alpha)

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