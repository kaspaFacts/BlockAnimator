# engine/sprites/block.py
import pygame


class Block(pygame.sprite.Sprite):
    """A simple block sprite."""

    def __init__(self, x, y, sprite_id, text="Block", size=60, color=(255, 0, 0)):
        super().__init__()

        self.sprite_id = sprite_id
        self.size = size
        self.color = color
        self.text = text

        # Create surface
        self.image = pygame.Surface((size + 10, size + 10), pygame.SRCALPHA)
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

        # Font
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)

        self.render()

    def render(self):
        """Render the block."""
        self.image.fill((0, 0, 0, 0))

        if not self.visible:
            return

            # Draw block
        block_rect = pygame.Rect(5, 5, self.size, self.size)
        pygame.draw.rect(self.image, self.color, block_rect)
        pygame.draw.rect(self.image, (255, 255, 255), block_rect, 3)

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