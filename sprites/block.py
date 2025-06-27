import pygame
from dataclasses import dataclass
from typing import List, Dict, Optional
from animation.proxy import BlockAnimationProxy


@dataclass
class GhostdagData:
    """GHOSTDAG data calculated when block is created"""
    blue_score: int = 0
    blue_work: int = 0  # For future implementation
    selected_parent: Optional[str] = None
    mergeset_blues: List[str] = None  # Separate blue blocks
    mergeset_reds: List[str] = None  # Separate red blocks
    blues_anticone_sizes: Dict[str, int] = None
    hash: str = None

    def __post_init__(self):
        if self.mergeset_blues is None:
            self.mergeset_blues = []
        if self.mergeset_reds is None:
            self.mergeset_reds = []
        if self.blues_anticone_sizes is None:
            self.blues_anticone_sizes = {}
        if self.hash is None and hasattr(self, '_sprite_id'):
            self.hash = self._sprite_id

    @property
    def mergeset(self):
        """Combined mergeset for backward compatibility - returns consensus ordered"""
        return self.consensus_ordered_mergeset

    @property
    def consensus_ordered_mergeset(self):
        """Returns mergeset in consensus order: selected parent first, then blues, then reds"""
        return [self.selected_parent] + self.mergeset_blues[1:] + self.mergeset_reds

    @property
    def consensus_ordered_mergeset_without_selected_parent(self):
        """Returns mergeset without selected parent in consensus order"""
        return self.mergeset_blues[1:] + self.mergeset_reds

    @property
    def unordered_mergeset(self):
        """Returns all mergeset blocks including selected parent"""
        return self.mergeset_blues + self.mergeset_reds

    @property
    def unordered_mergeset_without_selected_parent(self):
        """Returns all mergeset blocks except selected parent (no specific order)"""
        return self.mergeset_blues[1:] + self.mergeset_reds

    @property
    def mergeset_size(self):
        """Returns total size of mergeset"""
        return len(self.mergeset_blues) + len(self.mergeset_reds)


class Block(pygame.sprite.Sprite):
    """
    Base block sprite for any consensus mechanism.
    Handles basic rendering, positioning, and visual properties.
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
        font_size = max(int(grid_size * 2), 8)  # 30% of grid unit, minimum 8px

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


class BitcoinBlock(Block):
    def __init__(self, x, y, sprite_id, grid_size, text="Block", color=(255, 165, 0),
                 parent: str = None, **kwargs):
        super().__init__(x, y, sprite_id, grid_size, text, color)

        # Bitcoin blocks have exactly one parent (except genesis)
        if parent is not None:
            self.parents = [parent]  # Single parent as list for compatibility
            self.parent = parent  # Direct access to single parent
        else:
            self.parents = []  # Genesis block
            self.parent = None

    def set_parent(self, parent_id: str):
        """Set the single parent for this Bitcoin block."""
        if self.parents:
            raise ValueError("Bitcoin blocks can only have one parent. Use replace_parent() instead.")
        self.parent = parent_id
        self.parents = [parent_id]

    def replace_parent(self, new_parent_id: str):
        """Replace the existing parent (for reorganizations)."""
        self.parent = new_parent_id
        self.parents = [new_parent_id]

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
    def __init__(self, x, y, sprite_id, grid_size, text="Block", color=(0, 0, 255),
                 parents: list = None, **kwargs):
        super().__init__(x, y, sprite_id, grid_size, text, color)

        self.parents = parents or []
        self.ghostdag_data = GhostdagData(hash=self.sprite_id)  # Initialize with default data

    #
    def calculate_ghostdag_data(self, ghostdag_k, dag_blocks):
        """Calculate GHOSTDAG data with external parameters"""
        self.ghostdag_data = self._run_ghostdag_algorithm(ghostdag_k, dag_blocks)
        #

    def _run_ghostdag_algorithm(self, ghostdag_k, dag_blocks):
        """Run GHOSTDAG algorithm with passed parameters"""
        selected_parent = self._find_selected_parent(dag_blocks)
        print(f"DEBUG: Block {self.sprite_id} selected parent: {selected_parent}")
        ghostdag_data = GhostdagData(selected_parent=selected_parent, hash=self.sprite_id)

        if dag_blocks and self.parents:
            # Extract parent IDs from Parent objects consistently
            parent_ids = []
            for p in self.parents:
                if hasattr(p, 'parent_id'):
                    parent_ids.append(p.parent_id)
                else:
                    parent_ids.append(str(p))  # Ensure it's a string

            mergeset_candidates = self._calculate_mergeset(selected_parent, parent_ids, dag_blocks)

            # Ensure all candidates are strings
            mergeset_candidates = {str(candidate) for candidate in mergeset_candidates}

            # Initialize with selected parent as first blue block
            mergeset_blues = [selected_parent] if selected_parent else []
            mergeset_reds = []
            blues_anticone_sizes = {selected_parent: 0} if selected_parent else {}

            # Process candidates using k-cluster check - now safe to sort
            for candidate_id in sorted(mergeset_candidates):
                if self._can_be_blue(candidate_id, mergeset_blues, ghostdag_k, dag_blocks):
                    mergeset_blues.append(candidate_id)
                    blues_anticone_sizes[candidate_id] = 0
                else:
                    mergeset_reds.append(candidate_id)

                    # Update ghostdag data and calculate blue score
            ghostdag_data.mergeset_blues = mergeset_blues
            ghostdag_data.mergeset_reds = mergeset_reds
            ghostdag_data.blues_anticone_sizes = blues_anticone_sizes
            ghostdag_data.blue_score = self._calculate_blue_score(selected_parent, mergeset_blues, dag_blocks)
        else:
            # Genesis block case
            ghostdag_data.blue_score = 0

        print(f"DEBUG: Final blue score for {self.sprite_id}: {ghostdag_data.blue_score}")
        print(f"DEBUG: Mergeset blues: {ghostdag_data.mergeset_blues}")
        print(f"DEBUG: Mergeset reds: {ghostdag_data.mergeset_reds}")
        return ghostdag_data
        #

    def _find_selected_parent(self, dag_blocks):
        """Find parent with highest blue score, using hash as tiebreaker"""
        # Genesis block has no parents
        if not self.parents:
            return None

            # If no DAG blocks available, return first parent ID as fallback
        if not dag_blocks:
            first_parent = self.parents[0]
            parent_id = first_parent.parent_id if hasattr(first_parent, 'parent_id') else first_parent
            return str(parent_id)  # Ensure string return

        best_parent = None
        best_blue_score = -1
        best_hash = None

        for parent in self.parents:
            # Extract parent ID from Parent object
            parent_id = parent.parent_id if hasattr(parent, 'parent_id') else parent
            parent_id = str(parent_id)  # Ensure string

            if parent_id in dag_blocks:
                parent_block = dag_blocks[parent_id]
                parent_blue_score = parent_block.ghostdag_data.blue_score
                parent_hash = parent_block.ghostdag_data.hash

                if (parent_blue_score > best_blue_score or
                        (parent_blue_score == best_blue_score and parent_hash < best_hash)):
                    best_blue_score = parent_blue_score
                    best_parent = parent_id
                    best_hash = parent_hash

                    # Return best parent found, or first parent ID as fallback
        if best_parent is not None:
            return best_parent
        else:
            first_parent = self.parents[0]
            parent_id = first_parent.parent_id if hasattr(first_parent, 'parent_id') else first_parent
            return str(parent_id)
            #

    def _calculate_mergeset(self, selected_parent_id, parent_ids, dag_blocks):
        """Calculate the mergeset - all blocks in anticone of selected parent"""
        if not dag_blocks or not selected_parent_id:
            return set()

            # Start with all parents except the selected parent
        queue = [pid for pid in parent_ids if pid != selected_parent_id]
        mergeset = set(queue)
        past_of_selected = set()

        while queue:
            current = queue.pop(0)
            if current not in dag_blocks:
                continue

            current_block = dag_blocks[current]
            # Extract parent IDs from Parent objects
            current_parent_ids = []
            for p in current_block.parents:
                if hasattr(p, 'parent_id'):
                    current_parent_ids.append(p.parent_id)
                else:
                    current_parent_ids.append(str(p))

                    # For each parent of the current block
            for parent_id in current_parent_ids:
                # Skip if already processed
                if parent_id in mergeset or parent_id in past_of_selected:
                    continue

                    # Check if parent_id is in the past of selected_parent_id
                # This is the key fix - we need to check if selected_parent can reach parent_id
                if self._is_ancestor(parent_id, selected_parent_id, dag_blocks):
                    past_of_selected.add(parent_id)
                    continue

                    # Otherwise, add to mergeset and queue for further processing
                mergeset.add(parent_id)
                queue.append(parent_id)

        return mergeset
    #
    def _is_ancestor(self, ancestor_id, descendant_id, dag_blocks):
        """Check if ancestor_id is in the past of descendant_id (i.e., descendant can reach ancestor)"""
        if not dag_blocks or ancestor_id == descendant_id:
            return ancestor_id == descendant_id  # A block is considered ancestor of itself

        visited = set()
        queue = [descendant_id]

        while queue:
            current = queue.pop(0)
            if current == ancestor_id:
                return True
            if current in visited:
                continue
            visited.add(current)

            if current in dag_blocks:
                current_block = dag_blocks[current]
                # Extract parent IDs properly
                for p in current_block.parents:
                    parent_id = p.parent_id if hasattr(p, 'parent_id') else str(p)
                    if parent_id not in visited:
                        queue.append(parent_id)

        return False
        #

    def _can_be_blue(self, candidate_id, current_blues, ghostdag_k, dag_blocks):
        """Simplified k-cluster check using dataclass properties"""
        # Rule 1: Can't exceed k+1 total blues
        if len(current_blues) >= ghostdag_k + 1:
            return False

            # Rule 2: Simplified anticone check
        anticone_count = sum(1 for blue_id in current_blues
                             if blue_id != candidate_id
                             and not self._is_ancestor(blue_id, candidate_id, dag_blocks)  # Pass dag_blocks
                             and not self._is_ancestor(candidate_id, blue_id, dag_blocks))  # Pass dag_blocks

        return anticone_count <= ghostdag_k
        #

    def _calculate_blue_score(self, selected_parent_id, mergeset_blues, dag_blocks):
        """Calculate blue score using Kaspa's formula"""
        # Genesis block case - no selected parent
        if not selected_parent_id:
            return 0  # Genesis always has blue score 0

        if selected_parent_id not in dag_blocks:
            return len(mergeset_blues)

        parent_block = dag_blocks[selected_parent_id]
        # Use Kaspa's exact formula: parent_blue_score + mergeset_blues.len()
        return parent_block.ghostdag_data.blue_score + len(mergeset_blues)

    def get_display_text(self):
        """GHOSTDAG-specific text display for debug"""
        return f"{self.text}\nBS:{self.ghostdag_data.blue_score}"

    #   TODO calculate blue_work for ghostdag blocks, by using a fast hash of the id that outputs binary,
    #        every hash will be difficulty 0 (sufficient difficulty), and leading zeros will increase difficulty