# BlockAnimator\blockanimator\consensus\blocks\nakamoto_consensus/bitcoin_block.py

from typing import List, Dict, Optional
from blockanimator.consensus.blocks.consensus_block import ConsensusBlock
from dataclasses import dataclass


@dataclass
class BitcoinData:
    """Bitcoin consensus data structure"""
    height: int = 0
    parent: Optional[str] = None
    difficulty: int = 1  # Simplified difficulty
    cumulative_work: int = 0

    def __post_init__(self):
        if self.parent is None:
            self.height = 0  # Genesis block


class BitcoinBlock:
    """Bitcoin consensus block implementation"""

    def __init__(self, block_id: str, parents: List[str] = None, **kwargs):
        self.block_id = block_id
        self.parents = parents or []
        self.consensus_type = "bitcoin"
        self.creation_order: Optional[int] = None

        # Bitcoin only allows single parent (except genesis)
        parent = self.parents[0] if self.parents else None
        self.consensus_data = BitcoinData(parent=parent)
        self.metadata = kwargs

    def is_genesis(self) -> bool:
        return len(self.parents) == 0

    def calculate_consensus_data(self, k: int, dag_context: Dict[str, ConsensusBlock]) -> None:
        """Calculate Bitcoin consensus data (height and cumulative work)"""
        if not self.parents:
            # Genesis block
            self.consensus_data.height = 0
            self.consensus_data.cumulative_work = 1
            return

        parent_id = self.parents[0]
        if parent_id in dag_context:
            parent_block = dag_context[parent_id]
            if parent_block.consensus_data:
                self.consensus_data.height = parent_block.consensus_data.height + 1
                self.consensus_data.cumulative_work = parent_block.consensus_data.cumulative_work + self.consensus_data.difficulty

    def validate_parents(self, dag_context: Dict[str, ConsensusBlock]) -> bool:
        """Validate Bitcoin parent relationships (single parent only)"""
        # Bitcoin blocks can only have one parent (except genesis)
        if len(self.parents) > 1:
            return False

            # If has parent, ensure it exists in DAG
        if self.parents and self.parents[0] not in dag_context:
            return False

        return True

    def get_display_info(self) -> str:
        """Get display text for visual representation"""
        if self.consensus_data:
            if self.consensus_data.parent:
                return f"{self.block_id}\nH:{self.consensus_data.height}\nParent: {self.consensus_data.parent[:6]}..."
            else:
                return f"{self.block_id}\nH:{self.consensus_data.height}\n(Genesis)"
        return self.block_id

    def get_chain_tip(self) -> str:
        """Get the tip of this block's chain"""
        return self.block_id

    def is_ancestor_of(self, other_block: 'BitcoinBlock', dag_context: Dict[str, ConsensusBlock]) -> bool:
        """Check if this block is an ancestor of another block"""
        if not other_block.parents:
            return False

        parent_id = other_block.parents[0]
        if parent_id == self.block_id:
            return True

        if parent_id in dag_context:
            parent_block = dag_context[parent_id]
            if isinstance(parent_block, BitcoinBlock):
                return self.is_ancestor_of(parent_block, dag_context)

        return False