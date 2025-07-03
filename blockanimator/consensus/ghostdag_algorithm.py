# blockanimator/consensus/ghostdag_algorithm.py

from dataclasses import dataclass
from typing import List, Dict, Optional, Set


@dataclass
class GhostdagData:
    """Pure GHOSTDAG consensus data - no visual dependencies"""
    blue_score: int = 0
    blue_work: int = 0  # For future implementation
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
        if self.hash is None:
            self.hash = ""

    @property
    def mergeset(self):
        """Combined mergeset for backward compatibility - returns consensus ordered"""
        return self.consensus_ordered_mergeset

    @property
    def consensus_ordered_mergeset(self):
        """Returns mergeset in consensus order: selected parent first, then blues, then reds"""
        if not self.selected_parent:
            return self.mergeset_blues + self.mergeset_reds
        return [self.selected_parent] + self.mergeset_blues[1:] + self.mergeset_reds

    @property
    def consensus_ordered_mergeset_without_selected_parent(self):
        """Returns mergeset without selected parent in consensus order"""
        return self.mergeset_blues[1:] + self.mergeset_reds

    @property
    def unordered_mergeset(self):
        """Returns all mergeset blocks including selected parent"""
        return self.mergeset_blues + self.mergeset_reds

    @property
    def unordered_mergeset_without_selected_parent(self):
        """Returns all mergeset blocks except selected parent (no specific order)"""
        return self.mergeset_blues[1:] + self.mergeset_reds

    @property
    def mergeset_size(self):
        """Returns total size of mergeset"""
        return len(self.mergeset_blues) + len(self.mergeset_reds)


class GhostdagAlgorithm:
    """Pure GHOSTDAG algorithm implementation - no sprite dependencies"""

    @staticmethod
    def run_ghostdag_algorithm(block_id: str, parents: List[str], ghostdag_k: int,
                               dag_blocks: Dict[str, any]) -> GhostdagData:
        """
        Run complete GHOSTDAG algorithm for a block

        Args:
            block_id: ID of the block being processed
            parents: List of parent block IDs
            ghostdag_k: GHOSTDAG security parameter
            dag_blocks: Dictionary of existing blocks in the DAG

        Returns:
            GhostdagData containing all consensus results
        """
        selected_parent = GhostdagAlgorithm.find_selected_parent(parents, dag_blocks)
        print(f"DEBUG: Block {block_id} selected parent: {selected_parent}")

        ghostdag_data = GhostdagData(selected_parent=selected_parent, hash=block_id)

        if dag_blocks and parents:
            # Extract parent IDs consistently
            parent_ids = [str(p) for p in parents]

            mergeset_candidates = GhostdagAlgorithm._calculate_mergeset(
                selected_parent, parent_ids, dag_blocks
            )

            # Ensure all candidates are strings
            mergeset_candidates = {str(candidate) for candidate in mergeset_candidates}

            # Initialize with selected parent as first blue block
            mergeset_blues = [selected_parent] if selected_parent else []
            mergeset_reds = []
            blues_anticone_sizes = {selected_parent: 0} if selected_parent else {}

            # Process candidates using k-cluster check
            for candidate_id in sorted(mergeset_candidates):
                if GhostdagAlgorithm._can_be_blue(
                        candidate_id, mergeset_blues, ghostdag_k, dag_blocks
                ):
                    mergeset_blues.append(candidate_id)
                    blues_anticone_sizes[candidate_id] = 0
                else:
                    mergeset_reds.append(candidate_id)

                    # Update ghostdag data and calculate blue score
            ghostdag_data.mergeset_blues = mergeset_blues
            ghostdag_data.mergeset_reds = mergeset_reds
            ghostdag_data.blues_anticone_sizes = blues_anticone_sizes
            ghostdag_data.blue_score = GhostdagAlgorithm._calculate_blue_score(
                selected_parent, mergeset_blues, dag_blocks
            )
        else:
            # Genesis block case
            ghostdag_data.blue_score = 0

        print(f"DEBUG: Final blue score for {block_id}: {ghostdag_data.blue_score}")
        print(f"DEBUG: Mergeset blues: {ghostdag_data.mergeset_blues}")
        print(f"DEBUG: Mergeset reds: {ghostdag_data.mergeset_reds}")

        return ghostdag_data

    @staticmethod
    def find_selected_parent(parents: List[str], dag_blocks: Dict[str, any]) -> Optional[str]:
        """
        Find parent with highest blue score, using hash as tiebreaker

        Args:
            parents: List of parent block IDs
            dag_blocks: Dictionary of existing blocks in the DAG

        Returns:
            ID of selected parent, or None for genesis block
        """
        # Genesis block has no parents
        if not parents:
            return None

            # If no DAG blocks available, return first parent ID as fallback
        if not dag_blocks:
            return str(parents[0])

        best_parent = None
        best_blue_score = -1
        best_hash = None

        for parent in parents:
            parent_id = str(parent)

            if parent_id in dag_blocks:
                parent_block = dag_blocks[parent_id]

                # Access GHOSTDAG data from the block
                if hasattr(parent_block, 'ghostdag_data'):
                    parent_blue_score = parent_block.ghostdag_data.blue_score
                    parent_hash = parent_block.ghostdag_data.hash
                elif hasattr(parent_block, 'consensus_data'):
                    parent_blue_score = parent_block.consensus_data.blue_score
                    parent_hash = parent_block.consensus_data.hash
                else:
                    # Fallback for blocks without consensus data
                    parent_blue_score = 0
                    parent_hash = parent_id

                if (parent_blue_score > best_blue_score or
                        (parent_blue_score == best_blue_score and parent_hash < best_hash)):
                    best_blue_score = parent_blue_score
                    best_parent = parent_id
                    best_hash = parent_hash

                    # Return best parent found, or first parent ID as fallback
        return best_parent if best_parent is not None else str(parents[0])

    @staticmethod
    def _calculate_mergeset(selected_parent_id: str, parent_ids: List[str],
                            dag_blocks: Dict[str, any]) -> Set[str]:
        """
        Calculate the mergeset - all blocks in anticone of selected parent

        Args:
            selected_parent_id: ID of the selected parent
            parent_ids: List of all parent IDs
            dag_blocks: Dictionary of existing blocks in the DAG

        Returns:
            Set of block IDs in the mergeset
        """
        if not dag_blocks or not selected_parent_id:
            return set()

            # Start with all parents except the selected parent
        queue = [pid for pid in parent_ids if pid != selected_parent_id]
        mergeset = set(queue)
        past_of_selected = set()

        while queue:
            current = queue.pop(0)
            if current not in dag_blocks:
                continue

            current_block = dag_blocks[current]

            # Extract parent IDs from the current block
            current_parent_ids = GhostdagAlgorithm._extract_parent_ids(current_block)

            # For each parent of the current block
            for parent_id in current_parent_ids:
                # Skip if already processed
                if parent_id in mergeset or parent_id in past_of_selected:
                    continue

                    # Check if parent_id is in the past of selected_parent_id
                if GhostdagAlgorithm._is_ancestor(parent_id, selected_parent_id, dag_blocks):
                    past_of_selected.add(parent_id)
                    continue

                    # Otherwise, add to mergeset and queue for further processing
                mergeset.add(parent_id)
                queue.append(parent_id)

        return mergeset

    @staticmethod
    def _extract_parent_ids(block) -> List[str]:
        """Extract parent IDs from a block object, handling different formats"""
        if hasattr(block, 'parents'):
            parent_ids = []
            for p in block.parents:
                if hasattr(p, 'parent_id'):
                    parent_ids.append(p.parent_id)
                else:
                    parent_ids.append(str(p))
            return parent_ids
        return []

    @staticmethod
    def _is_ancestor(ancestor_id: str, descendant_id: str,
                     dag_blocks: Dict[str, any]) -> bool:
        """
        Check if ancestor_id is in the past of descendant_id

        Args:
            ancestor_id: ID of potential ancestor block
            descendant_id: ID of potential descendant block
            dag_blocks: Dictionary of existing blocks in the DAG

        Returns:
            True if ancestor_id can be reached from descendant_id
        """
        if not dag_blocks or ancestor_id == descendant_id:
            return ancestor_id == descendant_id

        visited = set()
        queue = [descendant_id]

        while queue:
            current = queue.pop(0)
            if current == ancestor_id:
                return True
            if current in visited:
                continue
            visited.add(current)

            if current in dag_blocks:
                current_block = dag_blocks[current]
                parent_ids = GhostdagAlgorithm._extract_parent_ids(current_block)

                for parent_id in parent_ids:
                    if parent_id not in visited:
                        queue.append(parent_id)

        return False

    @staticmethod
    def _can_be_blue(candidate_id: str, current_blues: List[str],
                     ghostdag_k: int, dag_blocks: Dict[str, any]) -> bool:
        """
        Simplified k-cluster check for blue block classification

        Args:
            candidate_id: ID of candidate block
            current_blues: List of currently classified blue blocks
            ghostdag_k: GHOSTDAG security parameter
            dag_blocks: Dictionary of existing blocks in the DAG

        Returns:
            True if candidate can be classified as blue
        """
        # Rule 1: Can't exceed k+1 total blues
        if len(current_blues) >= ghostdag_k + 1:
            return False

            # Rule 2: Simplified anticone check
        anticone_count = sum(
            1 for blue_id in current_blues
            if blue_id != candidate_id
            and not GhostdagAlgorithm._is_ancestor(blue_id, candidate_id, dag_blocks)
            and not GhostdagAlgorithm._is_ancestor(candidate_id, blue_id, dag_blocks)
        )

        return anticone_count <= ghostdag_k

    @staticmethod
    def _calculate_blue_score(selected_parent_id: str, mergeset_blues: List[str],
                              dag_blocks: Dict[str, any]) -> int:
        """
        Calculate blue score using Kaspa's formula

        Args:
            selected_parent_id: ID of selected parent
            mergeset_blues: List of blue blocks in mergeset
            dag_blocks: Dictionary of existing blocks in the DAG

        Returns:
            Calculated blue score
        """
        # Genesis block case - no selected parent
        if not selected_parent_id:
            return 0

        if selected_parent_id not in dag_blocks:
            return len(mergeset_blues)

        parent_block = dag_blocks[selected_parent_id]

        # Get parent's blue score
        if hasattr(parent_block, 'ghostdag_data'):
            parent_blue_score = parent_block.ghostdag_data.blue_score
        elif hasattr(parent_block, 'consensus_data'):
            parent_blue_score = parent_block.consensus_data.blue_score
        else:
            parent_blue_score = 0

            # Use Kaspa's exact formula: parent_blue_score + mergeset_blues.len()
        return parent_blue_score + len(mergeset_blues)

    @staticmethod
    def calculate_blue_work(block_id: str) -> int:
        """
        Calculate blue work for GHOSTDAG blocks using hash difficulty

        Args:
            block_id: ID of the block

        Returns:
            Blue work value based on leading zeros in hash

        Note: This is a placeholder implementation for future use
        """
        # TODO: Implement using a fast hash of the id that outputs binary
        # Every hash will be difficulty 0 (sufficient difficulty)
        # Leading zeros will increase difficulty

        # Simple placeholder: count leading zeros in block_id hash
        import hashlib
        hash_bytes = hashlib.sha256(block_id.encode()).digest()
        leading_zeros = 0

        for byte in hash_bytes:
            if byte == 0:
                leading_zeros += 8
            else:
                # Count leading zeros in this byte
                leading_zeros += (8 - byte.bit_length())
                break

        return leading_zeros