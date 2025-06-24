# engine/sprites/block.py
import pygame
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class GhostdagData:
    """GHOSTDAG data calculated when block is created"""
    blue_score: int = 0
    selected_parent: Optional[str] = None  # sprite_id of selected parent
    mergeset: List[str] = None  # Full ordered mergeset (selected parent first, then ordered mergeset)
    blues_anticone_sizes: Dict[str, int] = None  # Map of blue block -> anticone size
    hash: str = None  # Block hash for tiebreaking (using sprite_id)

    def __post_init__(self):
        if self.mergeset is None:
            self.mergeset = []
        if self.blues_anticone_sizes is None:
            self.blues_anticone_sizes = {}
        if self.hash is None and hasattr(self, '_sprite_id'):
            self.hash = self._sprite_id

    def get_mergeset_blues(self):
        """Extract blue blocks from mergeset (first k+1 blocks including selected parent)"""
        # In real GHOSTDAG, blues are stored in order with selected parent first
        return self.mergeset[:len(self.mergeset) - len(self.get_mergeset_reds())]

    def get_mergeset_reds(self):
        """Extract red blocks from mergeset (remaining blocks after blues)"""
        blues_count = len(self.mergeset) - len([b for b in self.mergeset if self._is_red(b)])
        return self.mergeset[blues_count:]

    def _is_red(self, block_id):
        """Helper to determine if a block is red - implement based on your k-cluster logic"""
        # This would need to be implemented based on your actual blue/red determination
        pass

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

    def _calculate_mergeset(self, selected_parent_id, parent_ids):
        """Calculate the mergeset - all blocks in anticone of selected parent"""
        if not self.scene_registry or not selected_parent_id:
            return set()

            # Start with non-selected parents
        queue = [pid for pid in parent_ids if pid != selected_parent_id]
        mergeset = set(queue)
        past_of_selected = set()

        while queue:
            current = queue.pop(0)
            if current not in self.scene_registry:
                continue

            current_block = self.scene_registry[current]
            if not hasattr(current_block, 'parents'):
                continue

                # For each parent of current block
            for parent_id in current_block.parents:
                if parent_id in mergeset or parent_id in past_of_selected:
                    continue

                    # Check if parent is in past of selected parent
                if self._is_ancestor(parent_id, selected_parent_id):
                    past_of_selected.add(parent_id)
                    continue

                    # Add to mergeset and queue for processing
                mergeset.add(parent_id)
                queue.append(parent_id)

        return mergeset

    def _is_ancestor(self, ancestor_id, descendant_id):
        """Check if ancestor_id is in the past of descendant_id"""
        if not self.scene_registry or ancestor_id == descendant_id:
            return False

            # Simple BFS to check reachability
        visited = set()
        queue = [descendant_id]

        while queue:
            current = queue.pop(0)
            if current == ancestor_id:
                return True
            if current in visited:
                continue
            visited.add(current)

            if current in self.scene_registry:
                current_block = self.scene_registry[current]
                if hasattr(current_block, 'parents'):
                    queue.extend(current_block.parents)

        return False

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
        """Run proper GHOSTDAG algorithm using mergeset calculation and k-cluster validation."""
        if not self.scene_registry:
            return ghostdag_data

        selected_parent_id = ghostdag_data.selected_parent

        # STEP 1: Calculate the actual mergeset (anticone of selected parent)
        mergeset_candidates = self._calculate_mergeset(selected_parent_id, self.parents)

        # STEP 2: Build ordered mergeset starting with selected parent
        ordered_mergeset = []
        if selected_parent_id:
            ordered_mergeset.append(selected_parent_id)

        # Initialize temporary mergeset blues and reds for the new block
        temp_mergeset_blues = [selected_parent_id] if selected_parent_id else []
        temp_mergeset_reds = []
        temp_blues_anticone_sizes = {selected_parent_id: 0} if selected_parent_id else {}

        # STEP 3: Process candidates and add to mergeset in order, applying k-cluster rules
        for candidate_id in sorted(mergeset_candidates):  # Sort for deterministic order
            # Create a temporary GhostdagData to simulate the new block's state if candidate is blue
            # This is a simplified representation of the Rust `new_block_data` being passed around
            temp_new_block_data = GhostdagData(
                blue_score=0,  # This will be recalculated later
                selected_parent=selected_parent_id,
                mergeset=temp_mergeset_blues + temp_mergeset_reds,  # Current state of mergeset
                blues_anticone_sizes=temp_blues_anticone_sizes.copy(),
                hash=self.sprite_id
            )

            coloring_output = self._check_blue_candidate(temp_new_block_data, candidate_id, self.ghostdag_k)

            if coloring_output['is_blue']:
                temp_mergeset_blues.append(candidate_id)
                temp_blues_anticone_sizes.update(coloring_output['blues_anticone_sizes'])
            else:
                temp_mergeset_reds.append(candidate_id)

        # Finalize the mergeset for the new block
        ghostdag_data.mergeset = temp_mergeset_blues + temp_mergeset_reds

        # Calculate blue score
        if selected_parent_id and selected_parent_id in self.scene_registry:
            selected_parent_block = self.scene_registry[selected_parent_id]
            if hasattr(selected_parent_block, 'ghostdag_data'):
                # Blue score = selected parent's blue score + 1 (for selected parent) + blue blocks in mergeset
                blue_blocks_in_mergeset = len(
                    temp_mergeset_blues) - 1  # Subtract 1 because selected parent is already counted
                ghostdag_data.blue_score = selected_parent_block.ghostdag_data.blue_score + 1 + blue_blocks_in_mergeset
        else:
            # Genesis block case or no selected parent
            ghostdag_data.blue_score = len(temp_mergeset_blues)  # Only count its own blue mergeset blocks

        # Store the final blues_anticone_sizes
        ghostdag_data.blues_anticone_sizes = temp_blues_anticone_sizes

        return ghostdag_data

    def _check_blue_candidate(self, new_block_data, blue_candidate_id, k):
        """
        Determines if a candidate block can be colored blue based on k-cluster rules.
        Returns a dict indicating if blue, and updated anticone sizes if so.
        """
        # Condition 1: The maximum length of new_block_data.mergeset_blues can be K+1
        # (selected parent + k blue blocks)
        if len(new_block_data.mergeset) >= k + 1:  # This check is simplified, should be based on actual blues
            return {'is_blue': False}

        candidate_blues_anticone_sizes = {}  # This will store anticone sizes for blue blocks if candidate is blue
        candidate_blue_anticone_size = 0

        # Simulate walking the chain from the new block's selected parent backwards
        current_chain_block_id = new_block_data.selected_parent
        while current_chain_block_id:
            if current_chain_block_id == blue_candidate_id:
                # If blue_candidate is in the past of the current chain block, it can be blue
                return {'is_blue': True, 'blues_anticone_sizes': candidate_blues_anticone_sizes}

            if current_chain_block_id not in self.scene_registry:
                break  # Should not happen in a valid DAG

            current_chain_block = self.scene_registry[current_chain_block_id]
            if not hasattr(current_chain_block, 'ghostdag_data'):
                break  # Should not happen for GhostdagBlocks

            # Check blue peers in the current chain block's mergeset (simplified)
            # In the real algorithm, this iterates over the blue set of the *new block*
            # and checks against the candidate.
            for peer_id in current_chain_block.ghostdag_data.mergeset:  # Simplified: iterate over current block's mergeset
                if peer_id == blue_candidate_id:
                    continue  # Skip self

                # Check if peer is in the past of blue_candidate (not in its anticone)
                if self._is_ancestor(peer_id, blue_candidate_id):
                    continue

                    # Peer is in anticone of blue_candidate, check k limits
                # This is where the complex anticone size calculation and comparison happens
                # For a full implementation, you'd need to calculate the actual anticone size
                # of `peer_id` with respect to `blue_candidate_id` and the current `new_block_data`

                # Simplified check: just count
                candidate_blue_anticone_size += 1
                if candidate_blue_anticone_size > k:
                    return {'is_blue': False}

                    # This is a placeholder for the second k-cluster condition:
                # For every blue block in new_block_data.mergeset_blues,
                # |(anticone-of-blue-block ∩ blue-set-new-block) ∪ {candidate-block}| ≤ K
                # This requires calculating anticone sizes for existing blue blocks if candidate is added.
                # For now, we'll just add a dummy entry.
                candidate_blues_anticone_sizes[peer_id] = 0  # Placeholder, needs real calculation

            current_chain_block_id = current_chain_block.ghostdag_data.selected_parent  # Move up the chain

        # If loop finishes without returning, it means no violation found
        return {'is_blue': True, 'blues_anticone_sizes': candidate_blues_anticone_sizes}

    def _blue_anticone_size(self, block_id, context_ghostdag_data):
        """
        Calculates the blue anticone size of 'block_id' within the context of 'context_ghostdag_data'.
        This is a highly simplified placeholder. A full implementation requires:
        1. Traversing the past of 'context_ghostdag_data' (the new block)
        2. For each block in that past, checking if it's in the anticone of 'block_id'
        3. Counting only the *blue* blocks that satisfy this condition.
        4. Using the stored `blues_anticone_sizes` from previous blocks to optimize.
        """
        # This is a very complex part of the algorithm. For a visualization,
        # you might need to simplify or approximate.
        # A proper implementation would involve:
        # - A BFS/DFS traversal from `context_ghostdag_data`'s selected parent and mergeset blues.
        # - For each visited block, check if it's in the anticone of `block_id`
        #   (i.e., not in the past of `block_id` and `block_id` not in its past).
        # - Counting only the blue blocks.
        # - Utilizing `context_ghostdag_data.blues_anticone_sizes` for memoization.

        # For now, return a dummy value or a simple count based on direct parents
        # This will likely lead to incorrect GHOSTDAG behavior for complex DAGs.

        # A very basic approximation: count how many blue blocks in context are not ancestors of block_id
        count = 0
        if block_id in self.scene_registry:
            for blue_block_in_context in context_ghostdag_data.mergeset:  # Simplified: iterate over context's mergeset
                if blue_block_in_context == block_id:
                    continue
                    # Check if blue_block_in_context is in anticone of block_id
                if not self._is_ancestor(blue_block_in_context, block_id) and \
                        not self._is_ancestor(block_id, blue_block_in_context):
                    count += 1
        return count

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