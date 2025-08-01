# BlockAnimator/blockanimator/consensus/blocks/block_factory.py


from typing import List, Union, Optional
from .consensus_block import ConsensusBlock
import importlib


class ConsensusBlockFactory:
    """Factory for creating consensus blocks."""

    _BLOCK_TYPES = {
        "bitcoin": ("nakamoto_consensus.bitcoin_block", "BitcoinBlock"),
        "ghostdag": ("ghostdag.ghostdag_block", "GhostdagBlock"),
        "iota": ("iota_block", "IOTABlock"),
    }

    @classmethod
    def create_block(cls, consensus_type: str, block_id: str,
                     parents: List[str] = None, **kwargs) -> ConsensusBlock:
        """Create a consensus block of the specified type."""
        if consensus_type not in cls._BLOCK_TYPES:
            raise ValueError(f"Unsupported consensus type: {consensus_type}")

        module_name, class_name = cls._BLOCK_TYPES[consensus_type]
        full_module_name = f"blockanimator.consensus.blocks.{module_name}"
        module = importlib.import_module(full_module_name)
        block_class = getattr(module, class_name)

        # Let each block type handle its own parent requirements
        return block_class(block_id, parents or [], **kwargs)

    @classmethod
    def get_supported_types(cls) -> List[str]:
        return list(cls._BLOCK_TYPES.keys())


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
        """Create the consensus block."""
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