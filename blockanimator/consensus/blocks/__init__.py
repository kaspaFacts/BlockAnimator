# BlockAnimator/blockanimator/consensus/blocks/__init__.py

"""
Consensus block implementations for blockchain visualization.

This package provides consensus-specific block implementations using a protocol-based
factory pattern. Each consensus type has its own subdirectory with block implementation.
"""

from .consensus_block import ConsensusBlock, ConsensusBlockBuilder, BlockContext
from .block_factory import ConsensusBlockFactory

# Import specific block implementations
from .nakamoto_consensus.bitcoin_block import BitcoinBlock, BitcoinData
from .ghostdag.ghostdag_block import GhostdagBlock, GhostdagData

__all__ = [
    # Core protocol and factory
    'ConsensusBlock',
    'ConsensusBlockBuilder',
    'ConsensusBlockFactory',
    'BlockContext',

    # Bitcoin implementation
    'BitcoinBlock',
    'BitcoinData',

    # GHOSTDAG implementation
    'GhostdagBlock',
    'GhostdagData',
]