# BlockAnimator\blockanimator\consensus\dags\nakamoto_consensus\__init__.py

"""
Bitcoin/Nakamoto consensus DAG implementation.

This module provides the Bitcoin consensus algorithm DAG implementation
with single-parent chain structure and linear positioning.
"""

from .bitcoin_dag import BitcoinDAG

__all__ = [
    'BitcoinDAG',
]