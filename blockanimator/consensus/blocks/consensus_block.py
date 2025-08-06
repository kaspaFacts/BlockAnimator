# BlockAnimator/blockanimator/consensus/blocks/consensus_block.py

from typing import Protocol, List, Dict, Optional, Any, Union, runtime_checkable
from abc import abstractmethod


@runtime_checkable
class ConsensusBlock(Protocol):
    """Protocol for consensus block implementations across different algorithms."""

    # Core attributes
    block_id: str
    parents: List[str]
    consensus_type: str
    creation_order: Optional[int]
    consensus_data: Any
    metadata: Dict[str, Any]

    @abstractmethod
    def calculate_consensus_data(self, k: int, dag_context: Dict[str, 'ConsensusBlock']) -> None:
        """Calculate consensus-specific data for this block."""
        ...

    @abstractmethod
    def validate_parents(self, dag_context: Dict[str, 'ConsensusBlock']) -> bool:
        """Validate parent relationships according to consensus rules."""
        ...

    @abstractmethod
    def get_display_info(self) -> str:
        """Get display text for visual representation."""
        ...

        # Simple utility methods

    def get_parent_count(self) -> int:
        return len(self.parents)

    def is_genesis(self) -> bool:
        return len(self.parents) == 0

    def has_parent(self, parent_id: str) -> bool:
        return parent_id in self.parents

    def set_label(self, new_label: str) -> None:
        """Set block label (optional - not all consensus types support this)."""
        ...

    def change_label(self, new_label: str, delay: float = 0.0, duration: float = 0.1):
        """Create label change animation (optional)."""
        ...

class ConsensusBlockBuilder:
    """Builder for creating consensus blocks with normalized interface."""

    def __init__(self, consensus_type: str, block_id: str):
        self.consensus_type = consensus_type
        self.block_id = block_id
        self.parents: List[str] = []
        self.metadata = {}

    def with_parents(self, parents: Union[str, List[str], None]) -> 'ConsensusBlockBuilder':
        """Add parents - automatically handles single vs multiple parent protocols."""
        if parents is None:
            self.parents = []
        elif isinstance(parents, str):
            self.parents = [parents]
        else:
            self.parents = parents or []
        return self

    def with_metadata(self, **kwargs) -> 'ConsensusBlockBuilder':
        """Add metadata to the block."""
        self.metadata.update(kwargs)
        return self

    def build(self) -> ConsensusBlock:
        """Create the consensus block using the factory."""
        from .block_factory import ConsensusBlockFactory
        return ConsensusBlockFactory.create_block(
            self.consensus_type,
            self.block_id,
            self.parents,
            **self.metadata
        )

    @classmethod
    def create(cls, consensus_type: str, block_id: str) -> 'ConsensusBlockBuilder':
        """Convenience method to start building a block."""
        return cls(consensus_type, block_id)

    # Type alias for cleaner signatures


BlockContext = Dict[str, ConsensusBlock]