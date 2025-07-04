# BlockAnimator\blockanimator\consensus\dags\__init__.py

"""
Consensus DAG implementations for blockchain visualization.

This package provides consensus-specific DAG implementations using a protocol-based
factory pattern. Each consensus type has its own subdirectory with DAG implementation.
"""

from .consensus_dags import ConsensusDAG, DAGContext
from .dag_factory import DAGFactory, DAGBuilder

# Import specific DAG implementations
from .nakamoto_consensus.bitcoin_dag import BitcoinDAG
from .ghostdag.ghostdag_dag import GhostdagDAG

__all__ = [
    # Core protocol and factory
    'ConsensusDAG',
    'DAGContext',
    'DAGFactory',
    'DAGBuilder',

    # Bitcoin implementation
    'BitcoinDAG',

    # GHOSTDAG implementation
    'GhostdagDAG',
]