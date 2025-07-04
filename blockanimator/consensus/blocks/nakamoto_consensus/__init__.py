# BlockAnimator\blockanimator\consensus\blocks\nakamoto_consensus\__init__.py

"""
Bitcoin/Nakamoto consensus block implementation.

This module provides the Bitcoin consensus algorithm implementation
with single-parent chain structure and height-based ordering.
"""

from .bitcoin_block import BitcoinBlock, BitcoinData

__all__ = [
    'BitcoinBlock',
    'BitcoinData',
]