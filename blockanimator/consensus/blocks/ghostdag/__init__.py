# BlockAnimator/blockanimator/consensus/blocks/ghostdag/__init__.py

"""
GHOSTDAG consensus block implementation.

This module provides the GHOSTDAG consensus algorithm implementation
with multi-parent DAG support and blue/red block classification.
"""

from .ghostdag_block import GhostdagBlock, GhostdagData

__all__ = [
    'GhostdagBlock',
    'GhostdagData',
]