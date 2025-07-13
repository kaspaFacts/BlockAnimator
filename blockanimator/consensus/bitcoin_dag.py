# BlockAnimator\blockanimator\consensus\nakamoto_consensus.py

from blockanimator.consensus.dags.base_dag import BlockDAG
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

    def create_hidden_fork(self, fork_blocks_data, start_position, opacity=127):
        """Create hidden fork blocks at 50% opacity"""
        hidden_animations = []

        for i, block_data in enumerate(fork_blocks_data):
            block_id = block_data['id']
            # Position fork blocks parallel to main chain
            pos = (start_position[0] + i * self._calculate_block_spacing(),
                   start_position[1] + 10)  # Offset vertically

            # Add block without updating chain_blocks list
            animations = super().add(block_id, pos,
                                     consensus_type='bitcoin',
                                     **block_data.get('kwargs', {}))

            # Set to 50% opacity immediately
            hidden_animations.append(
                self.scene.change_appearance(block_id, target_alpha=opacity, duration=0.1)
            )

        return hidden_animations

    def reveal_and_reorganize_fork(self, hidden_fork_blocks, orphan_from_height=None):
        """Reveal hidden fork and reorganize the chain"""
        reveal_animations = []

        # Phase 1: Fade hidden fork to full opacity
        for block_id in hidden_fork_blocks:
            reveal_animations.append(
                self.scene.change_appearance(block_id, target_alpha=255, duration=2.0)
            )

            # Phase 2: Move hidden fork to main chain position
        main_chain_y = self.genesis_pos[1]
        fork_start_x = self.genesis_pos[0] + (orphan_from_height or 2) * self._calculate_block_spacing()

        for i, block_id in enumerate(hidden_fork_blocks):
            new_pos = (fork_start_x + i * self._calculate_block_spacing(), main_chain_y)
            reveal_animations.append(
                self.scene.move_to(block_id, new_pos, duration=2.0)
            )

            # Phase 3: Move orphaned blocks down
        if orphan_from_height is not None:
            orphaned_blocks = self.chain_blocks[orphan_from_height:]
            orphan_y = main_chain_y - 15

            for i, block_id in enumerate(orphaned_blocks):
                current_pos = self.blocks[block_id].grid_pos
                orphan_pos = (current_pos[0], orphan_y)
                reveal_animations.append(
                    self.scene.move_to(block_id, orphan_pos, duration=2.0)
                )
                # Fade orphaned blocks
                reveal_animations.append(
                    self.scene.change_appearance(block_id, target_alpha=128,
                                                 target_color=(255, 100, 100), duration=2.0)
                )

        return reveal_animations

    def create_fork_state_animation(self, main_chain_color=(0, 255, 0), orphan_color=(255, 100, 100)):
        """Create animation showing main chain vs orphaned blocks"""
        animations = []

        # Highlight current main chain
        for i, block_id in enumerate(self.chain_blocks):
            animations.append(ColorChangeAnimation(
                sprite_id=block_id,
                target_color=main_chain_color,
                duration=0.5,
                delay=i * 0.1
            ))

            # You could track orphaned blocks separately if needed
        # This would require extending the class to maintain orphan state

        return animations

    def finalize_reorganization(self, hidden_fork_blocks, orphan_from_height=None):
        """Update internal chain tracking after reorganization"""
        if orphan_from_height is not None:
            # Keep blocks up to the fork point, replace with hidden fork
            self.chain_blocks = self.chain_blocks[:orphan_from_height] + hidden_fork_blocks
        else:
            self.chain_blocks = hidden_fork_blocks

    def create_hidden_fork_blocks(self, fork_point_id, num_blocks=3, opacity=127):
        """Create hidden fork blocks at reduced opacity"""
        if fork_point_id not in self.blocks:
            raise ValueError(f"Fork point {fork_point_id} not found")

        fork_start_pos = self.blocks[fork_point_id].grid_pos
        hidden_fork_blocks = []
        hidden_animations = []

        for i in range(1, num_blocks + 1):
            fork_block_id = f"Fork_{i}"
            hidden_fork_blocks.append(fork_block_id)

            # Position fork blocks offset from main chain
            fork_pos = (
                fork_start_pos[0] + i * self._calculate_block_spacing(),
                fork_start_pos[1] + 15  # Vertical offset
            )

            # Add block using parent BlockDAG method
            animations = super().add(fork_block_id, fork_pos,
                                     label=f"F{i}",
                                     parents=[fork_point_id if i == 1 else f"Fork_{i - 1}"],
                                     consensus_type='bitcoin')

            # Set to reduced opacity
            opacity_anim = self.scene.change_appearance(fork_block_id, target_alpha=opacity, duration=0.1)
            hidden_animations.append(opacity_anim)

        return hidden_fork_blocks, hidden_animations

    def reveal_fork_and_reorganize(self, hidden_fork_blocks, honest_chain_blocks):
        """Reveal hidden fork and displace honest chain"""
        reveal_animations = []

        # Phase 1: Fade hidden fork to 100% opacity
        for block_id in hidden_fork_blocks:
            reveal_animations.append(
                self.scene.change_appearance(block_id, target_alpha=255, duration=1.0)
            )

            # Phase 2: Move hidden fork to main chain position
        main_chain_y = self.genesis_pos[1]
        for i, block_id in enumerate(hidden_fork_blocks):
            new_pos = (self.genesis_pos[0] + i * self._calculate_block_spacing(),
                       main_chain_y)
            reveal_animations.append(
                self.scene.move_to(block_id, new_pos, duration=2.0)
            )

            # Phase 3: Move honest chain blocks to orphaned position
        orphan_y = main_chain_y - 15
        for i, block_id in enumerate(honest_chain_blocks):
            orphan_pos = (self.genesis_pos[0] + i * self._calculate_block_spacing(),
                          orphan_y)
            reveal_animations.append(
                self.scene.move_to(block_id, orphan_pos, duration=2.0)
            )
            # Optional: fade honest chain to show it's orphaned
            reveal_animations.append(
                self.scene.change_appearance(block_id, target_alpha=128, duration=2.0)
            )

            # Execute all animations simultaneously
        self.scene.play(reveal_animations)

        # Update internal chain tracking
        self.chain_blocks = hidden_fork_blocks

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
