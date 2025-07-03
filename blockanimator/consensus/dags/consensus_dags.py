# BlockAnimator\blockanimator\consensus\dags\consensus_dags.py

from typing import Protocol, List, Dict, Optional, Any, Tuple, runtime_checkable
from abc import abstractmethod
from ..blocks.consensus_block import ConsensusBlock


@runtime_checkable
class ConsensusDAG(Protocol):
    """Protocol for DAG implementations across different consensus algorithms."""

    # Core attributes
    consensus_type: str
    logical_blocks: Dict[str, ConsensusBlock]
    creation_order: List[str]

    @abstractmethod
    def add_logical_block(self, block_id: str, parents: List[str] = None, **kwargs) -> ConsensusBlock:
        """Add a logical block to the DAG."""
        ...

    @abstractmethod
    def calculate_block_position(self, block: ConsensusBlock) -> Tuple[float, float]:
        """Calculate visual position based on block's consensus data."""
        ...

    @abstractmethod
    def get_tips(self) -> List[str]:
        """Get current tip blocks."""
        ...

    @abstractmethod
    def validate_dag_integrity(self) -> bool:
        """Validate DAG structure according to consensus rules."""
        ...

        # Utility methods that can have default implementations

    def get_block_count(self) -> int:
        """Get total number of blocks in the DAG."""
        return len(self.logical_blocks)

    def get_block(self, block_id: str) -> Optional[ConsensusBlock]:
        """Get a block by its ID."""
        return self.logical_blocks.get(block_id)

    def get_blocks_in_creation_order(self) -> List[ConsensusBlock]:
        """Get all blocks in the order they were created."""
        return [self.logical_blocks[block_id] for block_id in self.creation_order if block_id in self.logical_blocks]

    # Type alias for cleaner signatures


DAGContext = Dict[str, ConsensusBlock]