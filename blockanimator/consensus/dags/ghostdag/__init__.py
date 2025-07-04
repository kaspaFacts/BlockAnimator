# BlockAnimator\blockanimator\consensus\dags\ghostdag\__init__.py

"""
GHOSTDAG consensus DAG implementation.

This module provides the GHOSTDAG consensus algorithm DAG implementation
with multi-parent support, blue/red classification, and topological positioning.
"""

from .ghostdag_dag import GhostdagDAG

__all__ = [
    'GhostdagDAG',
]