# blockanimator/consensus/logical_block.py

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from .ghostdag_algorithm import GhostdagAlgorithm, GhostdagData


@dataclass
class BitcoinData:
    """Bitcoin-specific consensus data"""
    parent: Optional[str] = None
    height: int = 0

    def __post_init__(self):
        if self.parent is None:
            self.height = 0  # Genesis block


class LogicalBlock:
    """
    Pure logical block representation without visual components.
    Handles consensus logic, parent relationships, and creation ordering.
    """

    def __init__(self, block_id: str, parents: List[str] = None, consensus_type: str = "basic", **kwargs):
        self.block_id = block_id
        self.parents = parents or []
        self.consensus_type = consensus_type
        self.creation_order = None  # Set when added to DAG
        self.consensus_data = None  # Will hold consensus-specific data
        self.metadata = kwargs  # Store additional block metadata

        # Initialize consensus-specific data
        self._initialize_consensus_data()

    def _initialize_consensus_data(self):
        """Initialize consensus-specific data structures"""
        if self.consensus_type == "ghostdag":
            self.consensus_data = GhostdagData(hash=self.block_id)
        elif self.consensus_type == "bitcoin":
            parent = self.parents[0] if self.parents else None
            self.consensus_data = BitcoinData(parent=parent)
        else:
            self.consensus_data = None

    def calculate_consensus_data(self, ghostdag_k: int, dag_context: Dict[str, 'LogicalBlock']):
        """Calculate consensus data using pure algorithms"""
        if self.consensus_type == "ghostdag":
            # Convert logical blocks to format expected by algorithm
            dag_blocks = {}
            for block_id, logical_block in dag_context.items():
                if logical_block.consensus_data:
                    dag_blocks[block_id] = logical_block

            self.consensus_data = GhostdagAlgorithm.run_ghostdag_algorithm(
                self.block_id, self.parents, ghostdag_k, dag_blocks
            )
        elif self.consensus_type == "bitcoin":
            # Bitcoin consensus is simpler - just track height
            if self.parents:
                parent_block = dag_context.get(self.parents[0])
                if parent_block and parent_block.consensus_data:
                    self.consensus_data.height = parent_block.consensus_data.height + 1

    def get_display_info(self) -> str:
        """Get display text based on consensus type"""
        if self.consensus_type == "ghostdag" and self.consensus_data:
            return f"{self.block_id}\nBS:{self.consensus_data.blue_score}"
        elif self.consensus_type == "bitcoin" and self.consensus_data:
            if self.consensus_data.parent:
                return f"{self.block_id}\nParent: {self.consensus_data.parent[:6]}..."
            return f"{self.block_id}\n(Genesis)"
        return self.block_id

    def validate_parents(self, dag_context: Dict[str, 'LogicalBlock']) -> bool:
        """Validate parent relationships based on consensus type"""
        if self.consensus_type == "bitcoin":
            # Bitcoin blocks can only have one parent (except genesis)
            if len(self.parents) > 1:
                return False
            if self.parents and self.parents[0] not in dag_context:
                return False
        elif self.consensus_type == "ghostdag":
            # GHOSTDAG blocks can have multiple parents
            for parent_id in self.parents:
                if parent_id not in dag_context:
                    return False
        return True


class LogicalBitcoinBlock(LogicalBlock):
    """Bitcoin-specific logical block with single-parent validation"""

    def __init__(self, block_id: str, parent: str = None, **kwargs):
        parents = [parent] if parent else []
        super().__init__(block_id, parents, "bitcoin", **kwargs)
        self.parent = parent

class LogicalGhostdagBlock(LogicalBlock):
    """GHOSTDAG-specific logical block with multiple-parent support"""

    def __init__(self, block_id: str, parents: List[str] = None, **kwargs):
        super().__init__(block_id, parents or [], "ghostdag", **kwargs)

class LogicalDAG:
    """
    DAG with clean logical/visual separation.
    Manages logical blocks and their consensus relationships.
    """

    def __init__(self, consensus_type: str = "basic", ghostdag_k: int = 3):
        self.consensus_type = consensus_type
        self.ghostdag_k = ghostdag_k

        # Core data structures
        self.logical_blocks: Dict[str, LogicalBlock] = {}
        self.creation_order: List[str] = []  # Ordered list for deterministic rendering

        # Consensus-specific tracking
        if consensus_type == "bitcoin":
            self.chain_blocks: List[str] = []  # Bitcoin chain order

    def add_logical_block(self, block_id: str, parents: List[str] = None, **kwargs) -> LogicalBlock:
        """
        Phase 1: Create logical block without visual representation

        Args:
            block_id: Unique identifier for the block
            parents: List of parent block IDs
            **kwargs: Additional metadata for the block

        Returns:
            Created LogicalBlock instance
        """
        if block_id in self.logical_blocks:
            raise ValueError(f"Block {block_id} already exists")

            # Create appropriate logical block type
        if self.consensus_type == "bitcoin":
            parent = parents[0] if parents else None
            logical_block = LogicalBitcoinBlock(block_id, parent, **kwargs)
        elif self.consensus_type == "ghostdag":
            logical_block = LogicalGhostdagBlock(block_id, parents, **kwargs)
        else:
            logical_block = LogicalBlock(block_id, parents, self.consensus_type, **kwargs)

            # Validate parents exist
        if not logical_block.validate_parents(self.logical_blocks):
            raise ValueError(f"Invalid parents for block {block_id}")

            # Set creation order
        logical_block.creation_order = len(self.creation_order)

        # Store block
        self.logical_blocks[block_id] = logical_block
        self.creation_order.append(block_id)

        # Update consensus-specific tracking
        if self.consensus_type == "bitcoin":
            if not parents:  # Genesis block
                self.chain_blocks = [block_id]
            else:
                self.chain_blocks.append(block_id)

                # Calculate consensus data
        logical_block.calculate_consensus_data(self.ghostdag_k, self.logical_blocks)

        return logical_block

    def get_block(self, block_id: str) -> Optional[LogicalBlock]:
        """Get a logical block by ID"""
        return self.logical_blocks.get(block_id)

    def get_blocks_in_creation_order(self) -> List[LogicalBlock]:
        """Get all blocks in the order they were created"""
        return [self.logical_blocks[block_id] for block_id in self.creation_order]

    def get_tips(self) -> List[str]:
        """Get current tip blocks (blocks with no children)"""
        tips = []
        for block_id in self.logical_blocks:
            has_children = False
            for other_id, other_block in self.logical_blocks.items():
                if other_id != block_id and block_id in other_block.parents:
                    has_children = True
                    break
            if not has_children:
                tips.append(block_id)
        return tips

    def validate_dag_integrity(self) -> bool:
        """Validate the entire DAG structure"""
        for block_id, block in self.logical_blocks.items():
            if not block.validate_parents(self.logical_blocks):
                print(f"DAG integrity error: Block {block_id} has invalid parents")
                return False

                # Consensus-specific validation
        if self.consensus_type == "bitcoin":
            return self._validate_bitcoin_chain()

        return True

    def _validate_bitcoin_chain(self) -> bool:
        """Validate Bitcoin chain integrity"""
        for i, block_id in enumerate(self.chain_blocks):
            if block_id not in self.logical_blocks:
                print(f"Chain integrity error: Block {block_id} not found")
                return False

            block = self.logical_blocks[block_id]

            if i == 0:  # Genesis block
                if block.parents:
                    print(f"Chain integrity error: Genesis block {block_id} should have no parents")
                    return False
            else:  # Non-genesis blocks
                expected_parent = self.chain_blocks[i - 1]
                if len(block.parents) != 1 or block.parents[0] != expected_parent:
                    print(f"Chain integrity error: Block {block_id} parent mismatch")
                    return False

        return True

    def get_chain_tip(self) -> Optional[str]:
        """Get the current tip of the Bitcoin chain (Bitcoin consensus only)"""
        if self.consensus_type == "bitcoin" and self.chain_blocks:
            return self.chain_blocks[-1]
        return None

    def get_chain_length(self) -> int:
        """Get the length of the Bitcoin chain (Bitcoin consensus only)"""
        if self.consensus_type == "bitcoin":
            return len(self.chain_blocks)
        return 0

    def get_block_height(self, block_id: str) -> Optional[int]:
        """Get the height of a block in the Bitcoin chain"""
        if self.consensus_type == "bitcoin":
            try:
                return self.chain_blocks.index(block_id)
            except ValueError:
                return None
        return None

    def reorganize_chain(self, new_chain_blocks: List[str]):
        """Reorganize the Bitcoin chain (for fork scenarios)"""
        if self.consensus_type != "bitcoin":
            raise ValueError("Chain reorganization only supported for Bitcoin consensus")

            # Validate all blocks exist
        for block_id in new_chain_blocks:
            if block_id not in self.logical_blocks:
                raise ValueError(f"Block {block_id} not found for reorganization")

                # Update chain tracking
        old_chain = self.chain_blocks.copy()
        self.chain_blocks = new_chain_blocks

        # Recalculate consensus data for affected blocks
        for block_id in new_chain_blocks:
            block = self.logical_blocks[block_id]
            block.calculate_consensus_data(self.ghostdag_k, self.logical_blocks)

        return old_chain

    def create_fork_from_point(self, fork_point_id: str, fork_blocks: List[str]) -> List[LogicalBlock]:
        """
        Create a logical fork from a specific point

        Args:
            fork_point_id: Block ID where the fork starts
            fork_blocks: List of new block IDs for the fork

        Returns:
            List of created fork blocks
        """
        if fork_point_id not in self.logical_blocks:
            raise ValueError(f"Fork point {fork_point_id} not found")

        created_blocks = []

        for i, block_id in enumerate(fork_blocks):
            if i == 0:
                # First fork block connects to fork point
                parent = fork_point_id
            else:
                # Subsequent blocks connect to previous fork block
                parent = fork_blocks[i - 1]

            fork_block = self.add_logical_block(block_id, [parent])
            created_blocks.append(fork_block)

        return created_blocks

    def get_statistics(self) -> Dict[str, Any]:
        """Get DAG statistics"""
        stats = {
            "total_blocks": len(self.logical_blocks),
            "consensus_type": self.consensus_type,
            "tips": self.get_tips(),
        }

        if self.consensus_type == "bitcoin":
            stats.update({
                "chain_length": self.get_chain_length(),
                "chain_tip": self.get_chain_tip(),
            })
        elif self.consensus_type == "ghostdag":
            stats.update({
                "ghostdag_k": self.ghostdag_k,
            })

        return stats