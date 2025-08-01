# BlockAnimator/blockanimator/consensus/__init__.py

"""
Consensus algorithms and DAG management for blockchain visualization.

This package provides different consensus mechanism implementations:
- BlockDAG: Base DAG functionality
- BitcoinDAG: Linear chain consensus
- LayerDAG: Topological layer-based DAG
- GhostdagDAG: GHOSTDAG consensus algorithm
"""

from .dag_types import StyledParent
from .dags.base_dag import BlockDAG
from .dags.nakamoto_consensus.bitcoin_dag import BitcoinDAG
from .dags.layer_dag import LayerDAG
from .dags.ghostdag.ghostdag_dag import GhostdagDAG
from .dags import ConsensusDAG, DAGContext, DAGFactory, DAGBuilder
from .blocks import ConsensusBlock, ConsensusBlockFactory, BlockContext
from .manager import ConsensusManager
from .constants import LayerConstants, AnimationConstants

__all__ = [
    # Core DAG classes
    'BlockDAG',
    'BitcoinDAG',
    'LayerDAG',
    'GhostdagDAG',  # Updated name

    # Factory system
    'ConsensusDAG',
    'DAGFactory',
    'DAGBuilder',
    'DAGContext',

    # Block system
    'ConsensusBlock',
    'ConsensusBlockFactory',
    'BlockContext',

    # Supporting classes
    'StyledParent',
    'ConsensusManager',

    # Constants
    'LayerConstants',
    'AnimationConstants'
]