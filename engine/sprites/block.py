# engine/sprites/block.py
import pygame
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class GhostdagData:
    """GHOSTDAG data calculated when block is created"""
    blue_score: int = 0
#    blue_work: int = 0  # currently not used or calculated
    selected_parent: Optional[str] = None  # sprite_id of selected parent
    mergeset_blues: List[str] = None  # List of blue block sprite_ids
    mergeset_reds: List[str] = None  # List of red block sprite_ids
    blues_anticone_sizes: Dict[str, int] = None  # Map of blue block -> anticone size
    hash: str = None  # Block hash for tiebreaking (using sprite_id)

    def __post_init__(self):
        if self.mergeset_blues is None:
            self.mergeset_blues = []
        if self.mergeset_reds is None:
            self.mergeset_reds = []
        if self.blues_anticone_sizes is None:
            self.blues_anticone_sizes = {}
        # Set hash to sprite_id if not provided
        if self.hash is None and hasattr(self, '_sprite_id'):
            self.hash = self._sprite_id

class Block(pygame.sprite.Sprite):
    """
    Base block sprite for any consensus mechanism.
    Handles basic rendering, positioning, and visual properties.
    """

    def __init__(self, x, y, sprite_id, grid_size, text="Block", color=(0, 0, 255)):
        super().__init__()

        # Core visual properties
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
        outline_width = max(int(self.grid_size * 0.25), 1)  # 10% of grid unit, minimum 1px
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

            # Keep all existing methods unchanged

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

class GhostdagBlock(Block):
    def __init__(self, x, y, sprite_id, grid_size, text="Block", color=(0, 0, 255),
                 parents=None, ghostdag_k=3, scene_registry=None, ghostdag_parents=None, **kwargs):
        # Initialize base block first
        super().__init__(x, y, sprite_id, grid_size, text, color)

        # GHOSTDAG-specific data - use ghostdag_parents if available
        self.parents = ghostdag_parents or parents or []
        self.ghostdag_k = ghostdag_k
        self.scene_registry = scene_registry

        # Calculate GHOSTDAG data at creation time
        self.ghostdag_data = self._calculate_ghostdag_data()

    def _calculate_ghostdag_data(self):
        """Calculate GHOSTDAG data when block is created"""
        print(f"Block {self.sprite_id}: parents={self.parents}")
        print(
            f"Block {self.sprite_id}: registry keys={list(self.scene_registry.keys()) if self.scene_registry else 'None'}")

        selected_parent = self._find_selected_parent()
        print(f"Block {self.sprite_id}: selected_parent={selected_parent}")

        selected_parent = self._find_selected_parent()

        # Initialize with basic data, including hash
        ghostdag_data = GhostdagData(
            selected_parent=selected_parent,
            hash=self.sprite_id  # Use sprite_id as hash
        )

        # If we have a scene registry, we can do more sophisticated calculations
        # This is where _run_ghostdag_algorithm is called
        if self.scene_registry and self.parents:  # Only run algorithm if parents exist
            ghostdag_data = self._run_ghostdag_algorithm(ghostdag_data)
        elif not self.parents:  # Handle genesis block or blocks without parents
            ghostdag_data.blue_score = 0
            ghostdag_data.mergeset_blues = []
            ghostdag_data.mergeset_reds = []
            ghostdag_data.blues_anticone_sizes = {}

        return ghostdag_data

    def _find_selected_parent(self):
        """Find parent with highest blue score, using hash as tiebreaker (lowest hash wins)"""
        if not self.parents or not self.scene_registry:
            return self.parents[0] if self.parents else None

        best_parent = None
        best_blue_score = -1
        best_hash = None

        for parent_id in self.parents:
            if parent_id in self.scene_registry:
                parent_block = self.scene_registry[parent_id]
                if hasattr(parent_block, 'ghostdag_data'):
                    parent_blue_score = parent_block.ghostdag_data.blue_score
                    parent_hash = parent_block.ghostdag_data.hash

                    # Primary comparison: blue score (higher is better)
                    if parent_blue_score > best_blue_score:
                        best_blue_score = parent_blue_score
                        best_parent = parent_id
                        best_hash = parent_hash
                        # Tiebreaker: lexicographic hash comparison (lower hash wins)
                    elif parent_blue_score == best_blue_score and (best_hash is None or parent_hash < best_hash):
                        best_parent = parent_id
                        best_hash = parent_hash

        return best_parent or (self.parents[0] if self.parents else None)

    def _run_ghostdag_algorithm(self, ghostdag_data):
        """Run proper GHOSTDAG algorithm using blue score"""
        if not self.scene_registry:
            return ghostdag_data

        selected_parent_id = ghostdag_data.selected_parent

        # FIRST: Populate the mergeset by processing non-selected parents
        for parent_id in self.parents:
            if parent_id != selected_parent_id and parent_id in self.scene_registry:
                # Simplified k-cluster check: if we have fewer than k blues, add as blue
                if len(ghostdag_data.mergeset_blues) < self.ghostdag_k:
                    ghostdag_data.mergeset_blues.append(parent_id)
                else:
                    ghostdag_data.mergeset_reds.append(parent_id)

                    # SECOND: Calculate blue score after mergeset is populated
        if selected_parent_id and selected_parent_id in self.scene_registry:
            selected_parent_block = self.scene_registry[selected_parent_id]
            if hasattr(selected_parent_block, 'ghostdag_data'):
                # Blue score = selected parent's blue score + 1 (for selected parent) + mergeset blues
                ghostdag_data.blue_score = selected_parent_block.ghostdag_data.blue_score + 1 + len(
                    ghostdag_data.mergeset_blues)
            else:
                ghostdag_data.blue_score = 1 + len(ghostdag_data.mergeset_blues)
        else:
            # Genesis block case - no selected parent
            ghostdag_data.blue_score = len(ghostdag_data.mergeset_blues)

        return ghostdag_data

    def get_outline_properties(self):
        """GHOSTDAG-specific outline styling"""
        # Green outline for blocks with selected parent
        if self.ghostdag_data.selected_parent:
            outline_color = (0, 255, 0)
            # Gold outline for blocks that are selected parents of others
        elif self.is_selected_parent():
            outline_color = (255, 215, 0)
        else:
            outline_color = (255, 255, 255)  # Default white

        outline_width = max(int(self.grid_size * 0.25), 1)
        return outline_color, outline_width

    def get_display_text(self):
        """GHOSTDAG-specific text display"""
        base_text = self.text
        blue_score_text = f"BS:{self.ghostdag_data.blue_score}"
        return f"{base_text}\n{blue_score_text}"

    def is_selected_parent(self):
        """Check if this block is a selected parent of any other block"""
        if not self.scene_registry:
            return False

        for block in self.scene_registry.values():
            if (hasattr(block, 'ghostdag_data') and
                    block.ghostdag_data.selected_parent == self.sprite_id):
                return True
        return False

    def get_mergeset_blocks(self):
        """Get all blocks in this block's mergeset"""
        if not self.scene_registry:
            return []

        mergeset_ids = (self.ghostdag_data.mergeset_blues +
                        self.ghostdag_data.mergeset_reds)
        return [self.scene_registry[bid] for bid in mergeset_ids
                if bid in self.scene_registry]

    def is_blue_relative_to(self, other_block_id):
        """Check if this block is blue relative to another block"""
        if not self.scene_registry or other_block_id not in self.scene_registry:
            return False

        other_block = self.scene_registry[other_block_id]
        if hasattr(other_block, 'ghostdag_data'):
            return self.sprite_id in other_block.ghostdag_data.mergeset_blues
        return False

    def is_red_relative_to(self, other_block_id):
        """Check if this block is red relative to another block"""
        if not self.scene_registry or other_block_id not in self.scene_registry:
            return False

        other_block = self.scene_registry[other_block_id]
        if hasattr(other_block, 'ghostdag_data'):
            return self.sprite_id in other_block.ghostdag_data.mergeset_reds
        return False

#   TODO calculate blue_work for ghostdag blocks, by using a fast hash of the id that outputs binary,
#        every hash will be difficulty 0 (sufficient difficulty), and leading zeros will increase difficulty