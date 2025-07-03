# blockanimator/consensus/dags/nakamoto_consensus/bitcoin_dag.py

from typing import Dict, List, Optional, Tuple, Any
from ..consensus_dags import ConsensusDAG
from ...blocks.consensus_block import ConsensusBlock, ConsensusBlockBuilder
from ...blocks.nakamoto_consensus.bitcoin_block import BitcoinBlock


class BitcoinDAG:
    """Bitcoin-specific DAG implementation with single-parent chain structure."""

    def __init__(self, consensus_type: str, **kwargs):
        self.consensus_type = consensus_type
        self.logical_blocks: Dict[str, ConsensusBlock] = {}
        self.creation_order: List[str] = []

        # Bitcoin-specific tracking
        self.chain_blocks: List[str] = []  # Ordered chain of blocks
        self.chain_tip: Optional[str] = None
        self.block_heights: Dict[str, int] = {}

        # Configuration
        self.config = kwargs

    def add_logical_block(self, block_id: str, parents: List[str] = None, **kwargs) -> ConsensusBlock:
        """Add a logical block to the Bitcoin chain."""
        if block_id in self.logical_blocks:
            raise ValueError(f"Block {block_id} already exists")

            # Create Bitcoin block using builder pattern
        block = (ConsensusBlockBuilder.create(self.consensus_type, block_id)
                 .with_parents(parents)
                 .with_metadata(**kwargs)
                 .build())

        # Validate parents exist and follow Bitcoin rules
        if not block.validate_parents(self.logical_blocks):
            raise ValueError(f"Invalid parents for block {block_id}")

            # Set creation order
        block.creation_order = len(self.creation_order)

        # Store block
        self.logical_blocks[block_id] = block
        self.creation_order.append(block_id)

        # Calculate Bitcoin consensus data (height)
        block.calculate_consensus_data(0, self.logical_blocks)  # k parameter not used for Bitcoin

        # Update Bitcoin-specific tracking
        self._update_chain_tracking(block)

        return block

    def _update_chain_tracking(self, block: ConsensusBlock) -> None:
        """Update Bitcoin chain tracking."""
        if block.is_genesis():
            # Genesis block starts the chain
            self.chain_blocks = [block.block_id]
            self.chain_tip = block.block_id
            self.block_heights[block.block_id] = 0
        else:
            # Add to end of chain
            self.chain_blocks.append(block.block_id)
            self.chain_tip = block.block_id
            height = getattr(block.consensus_data, 'height', len(self.chain_blocks) - 1)
            self.block_heights[block.block_id] = height

    def calculate_block_position(self, block: ConsensusBlock) -> Tuple[float, float]:
        """Calculate position based on Bitcoin chain height."""
        if block.is_genesis():
            return (10.0, 25.0)

            # Linear positioning based on height
        height = getattr(block.consensus_data, 'height', 0)
        x = 10.0 + (height * 25.0)  # 25 units spacing between blocks
        y = 25.0  # All blocks on same horizontal line

        return (x, y)

    def get_tips(self) -> List[str]:
        """Get current tip blocks (only one for Bitcoin)."""
        if self.chain_tip:
            return [self.chain_tip]
        return []

    def get_chain_length(self) -> int:
        """Get the length of the Bitcoin chain."""
        return len(self.chain_blocks)

    def get_block_height(self, block_id: str) -> Optional[int]:
        """Get the height of a specific block."""
        return self.block_heights.get(block_id)

    def get_chain_from_genesis(self) -> List[str]:
        """Get the complete chain from genesis to tip."""
        return self.chain_blocks.copy()

    def validate_dag_integrity(self) -> bool:
        """Validate Bitcoin chain structure and consensus rules."""
        # Basic DAG validation
        for block_id, block in self.logical_blocks.items():
            if not block.validate_parents(self.logical_blocks):
                print(f"Chain integrity error: Block {block_id} has invalid parents")
                return False

                # Bitcoin-specific validation
        return self._validate_chain_properties()

    def _validate_chain_properties(self) -> bool:
        """Validate Bitcoin chain-specific properties."""
        if not self.chain_blocks:
            return True

            # Validate genesis block
        genesis_id = self.chain_blocks[0]
        if genesis_id not in self.logical_blocks:
            print(f"Chain error: Genesis block {genesis_id} not found")
            return False

        genesis_block = self.logical_blocks[genesis_id]
        if not genesis_block.is_genesis():
            print(f"Chain error: Genesis block {genesis_id} has parents")
            return False

            # Validate chain continuity
        for i in range(1, len(self.chain_blocks)):
            current_id = self.chain_blocks[i]
            expected_parent_id = self.chain_blocks[i - 1]

            if current_id not in self.logical_blocks:
                print(f"Chain error: Block {current_id} not found")
                return False

            current_block = self.logical_blocks[current_id]
            if len(current_block.parents) != 1 or current_block.parents[0] != expected_parent_id:
                print(f"Chain error: Block {current_id} parent mismatch")
                return False

                # Validate heights
        for i, block_id in enumerate(self.chain_blocks):
            expected_height = i
            actual_height = self.block_heights.get(block_id, -1)
            if actual_height != expected_height:
                print(f"Chain error: Block {block_id} height mismatch")
                return False

        return True

    def create_fork_from_point(self, fork_point_id: str, fork_blocks: List[str]) -> List[ConsensusBlock]:
        """
        Create a fork from a specific point (for testing/simulation).
        Note: This creates an alternative chain, not part of the main chain.
        """
        if fork_point_id not in self.logical_blocks:
            raise ValueError(f"Fork point {fork_point_id} not found")

        created_blocks = []
        current_parent = fork_point_id

        for block_id in fork_blocks:
            # Create block with single parent
            fork_block = (ConsensusBlockBuilder.create(self.consensus_type, block_id)
                          .with_parents([current_parent])
                          .with_metadata(is_fork=True)
                          .build())

            # Set creation order
            fork_block.creation_order = len(self.creation_order)

            # Store block (but don't add to main chain)
            self.logical_blocks[fork_block.block_id] = fork_block
            self.creation_order.append(fork_block.block_id)

            # Calculate consensus data
            fork_block.calculate_consensus_data(0, self.logical_blocks)

            created_blocks.append(fork_block)
            current_parent = block_id

        return created_blocks

    def reorganize_chain(self, new_chain_blocks: List[str]) -> List[str]:
        """
        Reorganize the chain to a new sequence (for fork resolution).
        Returns the old chain.
        """
        # Validate all blocks exist
        for block_id in new_chain_blocks:
            if block_id not in self.logical_blocks:
                raise ValueError(f"Block {block_id} not found for reorganization")

                # Store old chain
        old_chain = self.chain_blocks.copy()

        # Update to new chain
        self.chain_blocks = new_chain_blocks
        self.chain_tip = new_chain_blocks[-1] if new_chain_blocks else None

        # Recalculate heights
        self.block_heights.clear()
        for i, block_id in enumerate(new_chain_blocks):
            self.block_heights[block_id] = i

            # Recalculate consensus data
            block = self.logical_blocks[block_id]
            block.calculate_consensus_data(0, self.logical_blocks)

        return old_chain

    def get_statistics(self) -> Dict[str, Any]:
        """Get Bitcoin chain statistics."""
        stats = {
            "total_blocks": len(self.logical_blocks),
            "consensus_type": self.consensus_type,
            "chain_length": self.get_chain_length(),
            "chain_tip": self.chain_tip,
            "tips": self.get_tips(),
        }

        if self.block_heights:
            stats.update({
                "max_height": max(self.block_heights.values()),
                "genesis_block": self.chain_blocks[0] if self.chain_blocks else None,
            })

        return stats

        # Protocol compliance methods

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