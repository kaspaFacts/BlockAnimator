# BlockAnimator\blockanimator\consensus\visual_block.py

import pygame


class VisualBlock(pygame.sprite.Sprite):
    """Pure visual representation - references logical block"""

    def __init__(self, x, y, logical_block, grid_size, color=(0, 0, 255)):
        super().__init__()
        self.logical_block = logical_block  # Reference to logical data
        self.sprite_id = logical_block.block_id

        # Only visual properties here
        self.size = int(grid_size * 4)
        self.grid_size = grid_size
        self.color = color
        self.alpha = 0
        self.visible = False

        # Visual setup
        self.image = pygame.Surface((self.size + 10, self.size + 10), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.x = float(x)
        self.y = float(y)

        # Add grid position tracking for animation system
        self.grid_x = None  # Will be set by scene
        self.grid_y = None  # Will be set by scene
        self.grid_pos = None

        # List of connections observing this block's alpha
        self.alpha_observers = []

        # Initialize font
        pygame.font.init()

        self.render()

    def render(self):
        """Render the block with visual properties"""
        self.image.fill((0, 0, 0, 0))  # Clear the surface

        if not self.visible:
            return

            # Draw the block rectangle
        block_rect = pygame.Rect(5, 5, self.size, self.size)
        pygame.draw.rect(self.image, self.color, block_rect)

        # Draw outline
        outline_color = (255, 255, 255)  # White outline
        outline_width = max(int(self.grid_size * 0.25), 1)
        pygame.draw.rect(self.image, outline_color, block_rect, outline_width)

        # Render text from logical block
        display_text = self.get_display_text()
        self.render_text(display_text, block_rect)

        # Apply alpha
        self.image.set_alpha(self.alpha)

    def render_text(self, display_text, block_rect):
        """Render text on the block"""
        # Initialize font
        font_size = max(int(self.grid_size * 2), 8)
        font = pygame.font.Font(None, font_size)

        text_lines = display_text.split('\n')
        for i, line in enumerate(text_lines):
            text_surface = font.render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect(
                center=(block_rect.centerx, block_rect.centery + i * 15)
            )
            self.image.blit(text_surface, text_rect)

    def get_display_text(self):
        """Get text from logical block data"""
        if self.logical_block.consensus_type == "ghostdag":
            return f"{self.logical_block.block_id}\nBS:{self.logical_block.consensus_data.blue_score}"
        elif self.logical_block.consensus_type == "bitcoin":
            parent = getattr(self.logical_block, 'parent', None)
            if parent:
                return f"{self.logical_block.block_id}\nParent: {parent[:6]}..."
            return f"{self.logical_block.block_id}\n(Genesis)"
        return self.logical_block.block_id

    def set_alpha(self, alpha):
        """Set sprite alpha"""
        if self.alpha != alpha:
            self.alpha = alpha
            self.render()
            # Notify observers
            for observer in self.alpha_observers:
                observer.on_alpha_change(alpha)

    def set_visible(self, visible):
        """Set sprite visibility"""
        self.visible = visible
        self.render()

    def set_color(self, color):
        """Set sprite color"""
        self.color = color
        self.render()

    def set_position(self, x, y):
        """Set sprite position"""
        self.x = float(x)
        self.y = float(y)
        self.rect.center = (int(x), int(y))