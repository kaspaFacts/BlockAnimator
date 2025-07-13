# BlockAnimator\blockanimator\consensus\__init__.py
"""
Consensus algorithms and DAG management for blockchain visualization.

This package provides different consensus mechanism implementations:
- BlockDAG: Base DAG functionality
- BitcoinDAG: Linear chain consensus
- LayerDAG: Topological layer-based DAG
- GhostDAG: GHOSTDAG consensus algorithm
"""

from .dag_types import StyledParent
from blockanimator.consensus.dags.base_dag import BlockDAG
from .bitcoin_dag import BitcoinDAG
from blockanimator.consensus.dags.layer_dag import LayerDAG
from .ghostdag_dag import GhostDAG
from .manager import ConsensusManager
from .constants import LayerConstants, AnimationConstants
from .logical_block import LogicalBlock, LogicalBitcoinBlock, LogicalDAG, LogicalGhostdagBlock, GhostdagAlgorithm, GhostdagData

__all__ = [
    # Core DAG classes
    'BlockDAG',
    'BitcoinDAG',
    'LayerDAG',
    'GhostDAG',

    # Supporting classes
    'StyledParent',
    'ConsensusManager',

    # Constants
    'LayerConstants',
    'AnimationConstants',

    # New Abstractions
    'LogicalBlock',
    'LogicalBitcoinBlock',
    'LogicalDAG',
    'LogicalGhostdagBlock',
    'GhostdagAlgorithm',
    'GhostdagData'
]