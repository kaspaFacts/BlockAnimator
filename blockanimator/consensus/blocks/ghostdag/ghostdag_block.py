# BlockAnimator\blockanimator\consensus\blocks\ghostdag\ghostdag_block.py

from typing import List, Dict, Optional
from blockanimator.consensus.blocks.consensus_block import ConsensusBlock
from dataclasses import dataclass


@dataclass
class GhostdagData:
    """GHOSTDAG consensus data structure"""
    blue_score: int = 0
    blue_work: int = 0
    selected_parent: Optional[str] = None
    mergeset_blues: List[str] = None
    mergeset_reds: List[str] = None
    blues_anticone_sizes: Dict[str, int] = None
    hash: str = None

    def __post_init__(self):
        if self.mergeset_blues is None:
            self.mergeset_blues = []
        if self.mergeset_reds is None:
            self.mergeset_reds = []
        if self.blues_anticone_sizes is None:
            self.blues_anticone_sizes = {}


class GhostdagBlock:
    """GHOSTDAG consensus block implementation"""

    def __init__(self, block_id: str, parents: List[str] = None, **kwargs):
        self.block_id = block_id
        self.parents = parents or []
        self.consensus_type = "ghostdag"
        self.creation_order: Optional[int] = None
        self.consensus_data = GhostdagData(hash=block_id)
        self.metadata = kwargs

    def is_genesis(self) -> bool:
        return len(self.parents) == 0

    def calculate_consensus_data(self, k: int, dag_context: Dict[str, ConsensusBlock]) -> None:
        """Calculate GHOSTDAG consensus data"""
        # Find selected parent (highest blue score, hash as tiebreaker)
        selected_parent = self._find_selected_parent(dag_context)

        if not selected_parent:
            # Genesis block
            self.consensus_data.blue_score = 0
            return

            # Calculate mergeset and classify blue/red blocks
        mergeset_candidates = self._calculate_mergeset(selected_parent, dag_context)

        # Initialize with selected parent as first blue block
        mergeset_blues = [selected_parent]
        mergeset_reds = []

        # Process candidates using k-cluster validation
        for candidate_id in sorted(mergeset_candidates):
            if self._can_be_blue(candidate_id, mergeset_blues, k, dag_context):
                mergeset_blues.append(candidate_id)
            else:
                mergeset_reds.append(candidate_id)

                # Update consensus data
        self.consensus_data.selected_parent = selected_parent
        self.consensus_data.mergeset_blues = mergeset_blues
        self.consensus_data.mergeset_reds = mergeset_reds
        self.consensus_data.blue_score = self._calculate_blue_score(selected_parent, mergeset_blues, dag_context)

    def _find_selected_parent(self, dag_context: Dict[str, ConsensusBlock]) -> Optional[str]:
        """Find parent with highest blue score"""
        if not self.parents:
            return None

        best_parent = None
        best_score = -1
        best_hash = None

        for parent_id in self.parents:
            if parent_id in dag_context:
                parent_block = dag_context[parent_id]
                parent_score = parent_block.consensus_data.blue_score if parent_block.consensus_data else 0
                parent_hash = parent_block.block_id

                if (parent_score > best_score or
                        (parent_score == best_score and parent_hash < best_hash)):
                    best_score = parent_score
                    best_parent = parent_id
                    best_hash = parent_hash

        return best_parent or self.parents[0]

    def _calculate_mergeset(self, selected_parent: str, dag_context: Dict[str, ConsensusBlock]) -> set:
        """Calculate mergeset (anticone of selected parent)"""
        # Simplified implementation - in practice this would be more complex
        mergeset = set()

        # Add non-selected parents to mergeset
        for parent_id in self.parents:
            if parent_id != selected_parent:
                mergeset.add(parent_id)

        return mergeset

    def _can_be_blue(self, candidate_id: str, current_blues: List[str], k: int,
                     dag_context: Dict[str, ConsensusBlock]) -> bool:
        """Check if candidate can be classified as blue (k-cluster validation)"""
        # Rule 1: Cannot exceed k+1 total blues
        if len(current_blues) >= k + 1:
            return False

            # Rule 2: Anticone constraint (simplified)
        anticone_count = 0
        for blue_id in current_blues:
            if not self._is_ancestor(blue_id, candidate_id, dag_context) and not self._is_ancestor(candidate_id,
                                                                                                   blue_id,
                                                                                                   dag_context):
                anticone_count += 1

        return anticone_count <= k

    def _is_ancestor(self, ancestor_id: str, descendant_id: str, dag_context: Dict[str, ConsensusBlock]) -> bool:
        """Check if ancestor_id is an ancestor of descendant_id"""
        if ancestor_id == descendant_id:
            return True

        if descendant_id not in dag_context:
            return False

        descendant = dag_context[descendant_id]
        for parent_id in descendant.parents:
            if self._is_ancestor(ancestor_id, parent_id, dag_context):
                return True

        return False

    def _calculate_blue_score(self, selected_parent: str, mergeset_blues: List[str],
                              dag_context: Dict[str, ConsensusBlock]) -> int:
        """Calculate blue score using Kaspa's formula"""
        if selected_parent not in dag_context:
            return len(mergeset_blues)

        parent_block = dag_context[selected_parent]
        parent_score = parent_block.consensus_data.blue_score if parent_block.consensus_data else 0
        return parent_score + len(mergeset_blues)

    def validate_parents(self, dag_context: Dict[str, ConsensusBlock]) -> bool:
        """Validate that all parents exist in DAG context"""
        for parent_id in self.parents:
            if parent_id not in dag_context:
                return False
        return True

    def get_display_info(self) -> str:
        """Get display text for visual representation"""
        if self.consensus_data and hasattr(self.consensus_data, 'blue_score'):
            return f"{self.block_id}\nBS:{self.consensus_data.blue_score}"
        return self.block_id