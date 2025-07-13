# blockanimator/consensus/dags/nakamoto_consensus/bitcoin_dag.py

from typing import Dict, List, Optional, Tuple, Any
from ..base_dag import BlockDAG
from ...blocks.consensus_block import ConsensusBlock
from ...blocks.block_factory import ConsensusBlockFactory
from ....animation.anim_types import DeferredMoveAnimation


class BitcoinDAG(BlockDAG):
    """Unified Bitcoin DAG that handles both consensus logic and visual rendering with automatic reorganization."""

    def __init__(self, consensus_type: str, scene=None, spacing_multiplier=2, **kwargs):
        # Extract scene from kwargs if not provided as positional arg
        if scene is None:
            scene = kwargs.pop('scene', None)

        super().__init__(scene, **kwargs)
        self.consensus_type = consensus_type
        self.spacing_multiplier = spacing_multiplier
        self.genesis_pos = (10, 25)
        self.fork_vertical_offset = 8

        # Bitcoin-specific tracking
        self.chain_blocks: List[str] = []
        self.logical_blocks: Dict[str, ConsensusBlock] = {}
        self.creation_order: List[str] = []

    def add_bitcoin_block(self, block_id: str, parent_id: str = None, label: str = None, **kwargs):
        """Add a Bitcoin block with automatic reorganization detection."""
        # Phase 1: Create logical block
        parents = [parent_id] if parent_id else []
        logical_block = ConsensusBlockFactory.create_block(
            self.consensus_type, block_id, parents, **kwargs
        )

        # Store logical block
        logical_block.creation_order = len(self.creation_order)
        self.logical_blocks[block_id] = logical_block
        self.creation_order.append(block_id)

        # Calculate consensus data
        logical_block.calculate_consensus_data(0, self.logical_blocks)

        # Phase 2: Calculate visual position
        is_fork_block = parent_id and parent_id != self.get_chain_tip()

        if is_fork_block:
            # Fork blocks: position below genesis initially
            position = self.calculate_block_position(logical_block)
            position = (position[0], self.genesis_pos[1] - self.fork_vertical_offset)
        else:
            # Regular blocks: use standard positioning initially, will be adjusted by deferred animation
            position = self.calculate_block_position(logical_block)

            # Phase 3: Create visual representation
        kwargs['consensus_type'] = 'bitcoin'
        animations = super().add(block_id, position, label=label or block_id,
                                 parents=parents, **kwargs)

        # Phase 4: Add deferred positioning for non-fork blocks to inherit parent Y
        if not is_fork_block and parent_id and parent_id in self.blocks:
            # Create a deferred move animation that will position at parent's Y at render time
            parent_y_inherit = DeferredMoveAnimation(
                sprite_id=block_id,
                offset=(0, 0),  # Will be calculated to match parent's Y
                duration=0.01  # Very short duration for immediate positioning
            )

            # Override the offset calculation to inherit parent's Y position
            def calculate_parent_y_offset():
                if parent_id in self.blocks:
                    parent_block = self.blocks[parent_id]
                    current_block = self.blocks[block_id]
                    # Calculate offset needed to match parent's Y
                    y_offset = parent_block.grid_pos[1] - current_block.grid_pos[1]
                    return (0, y_offset)
                return (0, 0)

                # Store the calculation function for the animation handler to use

            parent_y_inherit.calculate_offset = calculate_parent_y_offset
            animations.append(parent_y_inherit)

            # Phase 5: Handle reorganization logic
        if is_fork_block:
            # Get the fork chain and main chain
            fork_chain = self._get_fork_chain(block_id)
            main_chain = self.chain_blocks[1:].copy()  # Exclude genesis

            fork_length = len(fork_chain)
            main_length = len(main_chain)

            print(f"DEBUG: Fork chain length: {fork_length}, Main chain length: {main_length}")
            print(f"DEBUG: Fork chain: {fork_chain}, Main chain: {main_chain}")

            # Find the fork point (common ancestor)
            fork_point = self._find_fork_point(fork_chain, main_chain)
            print(f"DEBUG: Fork point: {fork_point}")

            # Apply your desired positioning logic (including equal height case)
            reorganize_animations = self._reorganize_with_equal_height_logic(
                fork_chain, main_chain, fork_length, main_length, fork_point
            )

            return animations + reorganize_animations
        else:
            # Regular block on main chain
            self._update_chain_tracking(logical_block)

        return animations

    def _reorganize_with_equal_height_logic(self, fork_chain: List[str], main_chain: List[str],
                                            fork_length: int, main_length: int, fork_point: str):
        """Reorganize based on chain length comparison, only moving blocks after fork point."""
        animations = []
        delay = 1.0

        genesis_y = self.genesis_pos[1]
        half_offset = self.fork_vertical_offset / 2  # Half spacing for equal positioning

        # Get only the competing blocks (after fork point)
        competing_fork_blocks = self._get_blocks_after_fork_point(fork_chain, fork_point)
        competing_main_blocks = self._get_blocks_after_fork_point(main_chain, fork_point)

        print(f"DEBUG: Competing fork blocks: {competing_fork_blocks}")
        print(f"DEBUG: Competing main blocks: {competing_main_blocks}")

        if fork_length == main_length:
            # Both chains equal height: both offset equally from genesis Y
            print("DEBUG: Equal height chains - both offset equally from genesis")

            # Move main chain competing blocks up (half offset above genesis)
            main_target_y = genesis_y + half_offset
            for block_id in competing_main_blocks:
                if block_id in self.blocks:
                    current_pos = self.blocks[block_id].grid_pos
                    new_pos = (current_pos[0], main_target_y)
                    move_anim = self.move_to(block_id, new_pos, duration=2.0)
                    move_anim.delay = delay
                    animations.append(move_anim)

                    # Move fork chain competing blocks down (half offset below genesis)
            fork_target_y = genesis_y - half_offset
            for block_id in competing_fork_blocks:
                if block_id in self.blocks:
                    current_pos = self.blocks[block_id].grid_pos
                    new_pos = (current_pos[0], fork_target_y)
                    move_anim = self.move_to(block_id, new_pos, duration=2.0)
                    move_anim.delay = delay
                    animations.append(move_anim)

        elif fork_length > main_length:
            # Fork is longer: fork at genesis Y, main chain offset away
            print("DEBUG: Fork is longer - fork to genesis, main chain offset")

            # Move fork chain competing blocks to genesis Y (becomes main)
            for block_id in competing_fork_blocks:
                if block_id in self.blocks:
                    current_pos = self.blocks[block_id].grid_pos
                    new_pos = (current_pos[0], genesis_y)
                    move_anim = self.move_to(block_id, new_pos, duration=2.0)
                    move_anim.delay = delay
                    animations.append(move_anim)

                    # Move original main chain competing blocks away (full offset above genesis)
            orphan_target_y = genesis_y + self.fork_vertical_offset
            for block_id in competing_main_blocks:
                if block_id in self.blocks:
                    current_pos = self.blocks[block_id].grid_pos
                    new_pos = (current_pos[0], orphan_target_y)
                    move_anim = self.move_to(block_id, new_pos, duration=2.0)
                    move_anim.delay = delay
                    # Fade orphaned blocks
                    fade_anim = self.fade_to(block_id, 180, duration=2.0)
                    fade_anim.delay = delay
                    animations.extend([move_anim, fade_anim])

                    # Update chain tracking - fork becomes main chain
            self.chain_blocks = ["Genesis"] + fork_chain

            # Note: fork_length < main_length case doesn't trigger reorganization
        # The fork stays in its offset position

        return animations

    def _find_fork_point(self, fork_chain: List[str], main_chain: List[str]) -> str:
        """Find the common ancestor where the chains diverge."""
        # Build full chains including genesis for proper comparison
        full_main_chain = ["Genesis"] + main_chain
        full_fork_chain = ["Genesis"] + fork_chain

        # Find the last common block by comparing from genesis forward
        fork_point = "Genesis"
        min_length = min(len(full_main_chain), len(full_fork_chain))

        for i in range(min_length):
            if full_main_chain[i] == full_fork_chain[i]:
                fork_point = full_main_chain[i]
            else:
                break

        print(f"DEBUG: Fork point identified as: {fork_point}")
        return fork_point

    def _get_blocks_after_fork_point(self, chain: List[str], fork_point: str) -> List[str]:
        """Get only the blocks that come after the fork point in a chain."""
        if fork_point == "Genesis":
            return chain  # All blocks are after genesis

        # Find the fork point in the full chain (including genesis)
        full_chain = ["Genesis"] + chain
        try:
            fork_index = full_chain.index(fork_point)
            # Return only blocks after the fork point
            competing_blocks = full_chain[fork_index + 1:]
            print(f"DEBUG: Blocks after {fork_point}: {competing_blocks}")
            return competing_blocks
        except ValueError:
            print(f"DEBUG: Fork point {fork_point} not found in chain, returning all blocks")
            return chain

    def calculate_block_position(self, block: ConsensusBlock) -> Tuple[float, float]:
        """Calculate position based on Bitcoin chain height."""
        if block.is_genesis():
            return self.genesis_pos

        height = getattr(block.consensus_data, 'height', 0)
        x = self.genesis_pos[0] + (height * self._calculate_block_spacing())
        y = self.genesis_pos[1]
        return (x, y)

    def _calculate_block_spacing(self):
        """Calculate spacing based on block size."""
        block_size_in_grid_units = 4
        return block_size_in_grid_units * self.spacing_multiplier

    def _update_chain_tracking(self, block: ConsensusBlock):
        """Update Bitcoin chain tracking."""
        if block.is_genesis():
            self.chain_blocks = [block.block_id]
        else:
            self.chain_blocks.append(block.block_id)

    def _calculate_fork_chain_length(self, block_id: str) -> int:
        """Calculate the length of the chain ending at block_id."""
        length = 0
        current = block_id

        while current and current in self.logical_blocks:
            length += 1
            logical_block = self.logical_blocks[current]
            if logical_block.parents:
                current = logical_block.parents[0]
            else:
                break

        return length

    def _get_fork_chain(self, tip_block_id: str) -> List[str]:
        """Get the chain of blocks from genesis to tip_block_id."""
        chain = []
        current = tip_block_id

        while current and current in self.logical_blocks:
            chain.append(current)
            logical_block = self.logical_blocks[current]
            if logical_block.parents:
                current = logical_block.parents[0]
            else:
                break

                # Reverse to get genesis-to-tip order, exclude genesis
        chain.reverse()
        return [block for block in chain if block != "Genesis"]

        # Keep all the existing utility methods unchanged

    def get_chain_tip(self) -> Optional[str]:
        """Get the current tip of the Bitcoin chain."""
        return self.chain_blocks[-1] if self.chain_blocks else None

    def get_tips(self) -> List[str]:
        """Get current tip blocks (only one for Bitcoin)."""
        tip = self.get_chain_tip()
        return [tip] if tip else []

    def get_chain_length(self) -> int:
        """Get the length of the Bitcoin chain."""
        return len(self.chain_blocks)

    def get_block_height(self, block_id: str) -> Optional[int]:
        """Get the height of a specific block."""
        try:
            return self.chain_blocks.index(block_id)
        except ValueError:
            return None

    def get_chain_from_genesis(self) -> List[str]:
        """Get the complete chain from genesis to tip."""
        return self.chain_blocks.copy()

    def validate_dag_integrity(self) -> bool:
        """Validate Bitcoin chain structure and consensus rules."""
        # Validate logical structure
        for block_id, block in self.logical_blocks.items():
            if not block.validate_parents(self.logical_blocks):
                return False
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get Bitcoin chain statistics."""
        stats = {
            "total_blocks": len(self.logical_blocks),
            "consensus_type": self.consensus_type,
            "chain_length": self.get_chain_length(),
            "chain_tip": self.get_chain_tip(),
            "tips": self.get_tips(),
        }

        if self.chain_blocks:
            stats.update({
                "genesis_block": self.chain_blocks[0] if self.chain_blocks else None,
            })

        return stats

    def get_block_count(self) -> int:
        """Get total number of blocks in the DAG."""
        return len(self.logical_blocks)

    def get_block(self, block_id: str) -> Optional[ConsensusBlock]:
        """Get a block by its ID."""
        return self.logical_blocks.get(block_id)

    def get_blocks_in_creation_order(self) -> List[ConsensusBlock]:
        """Get all blocks in the order they were created."""
        return [self.logical_blocks[block_id] for block_id in self.creation_order if block_id in self.logical_blocks]

    def get_blocks_in_chain_order(self) -> List[ConsensusBlock]:
        """Get blocks in chain order (genesis to tip)."""
        return [self.logical_blocks[block_id] for block_id in self.chain_blocks if block_id in self.logical_blocks]