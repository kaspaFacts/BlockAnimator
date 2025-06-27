# BlockAnimator\blockanimator\consensus\bitcoin_dag.py

from .base_dag import BlockDAG
from blockanimator.animation import ColorChangeAnimation

class BitcoinDAG(BlockDAG):
    def __init__(self, scene, spacing_multiplier=2, **kwargs):
        super().__init__(scene, **kwargs)
        self.spacing_multiplier = spacing_multiplier  # Multiplier relative to block size
        self.genesis_pos = (10, 25)
        self.chain_blocks = []

    def _calculate_block_spacing(self):
        """Calculate spacing based on actual block size."""
        # Block size is grid_size * 4 (from your Block class)
        block_size_in_grid_units = 4
        return block_size_in_grid_units * self.spacing_multiplier

    def add_bitcoin_block(self, block_id, parent_id=None, label=None, **kwargs):
        """Add a Bitcoin block with spacing relative to block size."""
        # Enforce single parent rule
        if parent_id is not None:
            if not isinstance(parent_id, str):
                raise ValueError("Bitcoin blocks can only have a single parent (string ID)")
            parents = [parent_id]
        else:
            parents = []  # Genesis block

        # Calculate position based on chain length
        if not parents:  # Genesis block
            pos = self.genesis_pos
            self.chain_blocks = [block_id]  # Start new chain
        else:
            # Verify parent exists and is the current tip
            if parent_id not in self.blocks:
                raise ValueError(f"Parent block '{parent_id}' not found")
            if parent_id != self.get_chain_tip():
                raise ValueError(
                    f"Bitcoin blocks must extend the chain tip. Expected: {self.get_chain_tip()}, got: {parent_id}")

                # Use calculated spacing based on block size instead of fixed spacing
            block_spacing = self._calculate_block_spacing()
            parent_pos = self.blocks[parent_id].grid_pos
            pos = (parent_pos[0] + block_spacing, parent_pos[1])
            self.chain_blocks.append(block_id)

            # Force bitcoin consensus type
        kwargs['consensus_type'] = 'bitcoin'

        # Use parent BlockDAG add method
        animations = super().add(block_id, pos, label=label, parents=parents, **kwargs)

        return animations

    def get_chain_tip(self):
        """Get the current tip of the Bitcoin chain."""
        return self.chain_blocks[-1] if self.chain_blocks else None

    def get_chain_length(self):
        """Get the length of the Bitcoin chain."""
        return len(self.chain_blocks)

    def get_block_height(self, block_id):
        """Get the height (index) of a block in the chain."""
        try:
            return self.chain_blocks.index(block_id)
        except ValueError:
            return None

    def validate_chain_integrity(self):
        """Validate that the chain maintains Bitcoin's linear structure."""
        for i, block_id in enumerate(self.chain_blocks):
            if block_id not in self.blocks:
                print(f"Chain integrity error: Block {block_id} not found in blocks")
                return False

            block = self.blocks[block_id]

            if i == 0:  # Genesis block
                if hasattr(block, 'parents') and block.parents:
                    print(f"Chain integrity error: Genesis block {block_id} should have no parents")
                    return False
            else:  # Non-genesis blocks
                expected_parent = self.chain_blocks[i - 1]
                if not hasattr(block, 'parents') or len(block.parents) != 1:
                    print(f"Chain integrity error: Block {block_id} should have exactly one parent")
                    return False
                if block.parents[0] != expected_parent:
                    print(
                        f"Chain integrity error: Block {block_id} parent mismatch. Expected: {expected_parent}, got: {block.parents[0]}")
                    return False

        return True

    def create_chain_animation(self, highlight_color=(255, 165, 0)):
        """Create animation to highlight the entire Bitcoin chain."""
        animations = []

        for i, block_id in enumerate(self.chain_blocks):
            # Color each block with a slight delay
            animations.append(ColorChangeAnimation(
                sprite_id=block_id,
                target_color=highlight_color,
                duration=0.5,
                delay=i * 0.1
            ))

        return animations

    def _get_current_tips(self):
        """Override to return only the chain tip for Bitcoin."""
        tip = self.get_chain_tip()
        return [tip] if tip else []

    def reorganize_chain(self, new_blocks_data):
        """Handle chain reorganization (for advanced Bitcoin scenarios)."""
        # This would be used for demonstrating Bitcoin forks and reorganizations
        # For now, just validate that any reorganization maintains single-parent structure
        for block_data in new_blocks_data:
            block_id = block_data['id']
            parent_id = block_data.get('parent')

            if parent_id and parent_id not in self.blocks:
                raise ValueError(f"Reorganization error: Parent {parent_id} not found")

                # Implementation would depend on specific reorganization logic needed
        pass
