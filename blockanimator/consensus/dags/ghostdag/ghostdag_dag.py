# BlockAnimator\blockanimator\consensus\dags\ghostdag\ghostdag_dag.py

from typing import Dict, List, Optional, Tuple, Any
from ..consensus_dags import ConsensusDAG
from ...blocks.consensus_block import ConsensusBlock, ConsensusBlockBuilder
from ...blocks.ghostdag.ghostdag_block import GhostdagBlock


class GhostdagDAG:
    """GHOSTDAG-specific DAG implementation with multi-parent support."""

    def __init__(self, consensus_type: str, k: int = 3, **kwargs):
        self.consensus_type = consensus_type
        self.k = k  # GHOSTDAG security parameter
        self.logical_blocks: Dict[str, ConsensusBlock] = {}
        self.creation_order: List[str] = []

        # GHOSTDAG-specific tracking
        self.blue_blocks: set = set()
        self.red_blocks: set = set()
        self.block_scores: Dict[str, int] = {}

        # Configuration
        self.config = kwargs

    def add_logical_block(self, block_id: str, parents: List[str] = None, **kwargs) -> ConsensusBlock:
        """Add a logical block to the GHOSTDAG."""
        if block_id in self.logical_blocks:
            raise ValueError(f"Block {block_id} already exists")

            # Create GHOSTDAG block using builder pattern
        block = (ConsensusBlockBuilder.create(self.consensus_type, block_id)
                 .with_parents(parents)
                 .with_metadata(**kwargs)
                 .build())

        # Validate parents exist
        if not block.validate_parents(self.logical_blocks):
            raise ValueError(f"Invalid parents for block {block_id}")

            # Set creation order
        block.creation_order = len(self.creation_order)

        # Store block
        self.logical_blocks[block_id] = block
        self.creation_order.append(block_id)

        # Calculate GHOSTDAG consensus data
        block.calculate_consensus_data(self.k, self.logical_blocks)

        # Update GHOSTDAG-specific tracking
        self._update_ghostdag_classification(block)

        return block

    def _update_ghostdag_classification(self, block: ConsensusBlock) -> None:
        """Update blue/red classification and scores."""
        if hasattr(block.consensus_data, 'blue_score'):
            self.block_scores[block.block_id] = block.consensus_data.blue_score

            # Classify as blue (for now, simplified - could be more complex)
            self.blue_blocks.add(block.block_id)
            if block.block_id in self.red_blocks:
                self.red_blocks.remove(block.block_id)

    def calculate_block_position(self, block: ConsensusBlock) -> Tuple[float, float]:
        """Calculate position based on GHOSTDAG data and topological layer."""
        if block.is_genesis():
            return (10.0, 25.0)

            # Calculate topological layer
        layer = self._calculate_topological_layer(block)

        # Position based on blue score and layer
        blue_score = getattr(block.consensus_data, 'blue_score', 0)

        # Base positioning
        x = 10.0 + (layer * 20.0)  # 20 units spacing between layers
        y = 25.0 + (blue_score * 3.0)  # Spread vertically by blue score

        # Add some variation for blocks in the same layer
        layer_blocks = self._get_blocks_in_layer(layer)
        if len(layer_blocks) > 1:
            block_index = sorted(layer_blocks).index(block.block_id)
            y += (block_index - len(layer_blocks) / 2) * 10.0

        return (x, y)

    def _calculate_topological_layer(self, block: ConsensusBlock) -> int:
        """Calculate topological layer for positioning."""
        if block.is_genesis():
            return 0

        max_parent_layer = -1
        for parent_id in block.parents:
            if parent_id in self.logical_blocks:
                parent_block = self.logical_blocks[parent_id]
                parent_layer = self._calculate_topological_layer(parent_block)
                max_parent_layer = max(max_parent_layer, parent_layer)

        return max_parent_layer + 1

    def _get_blocks_in_layer(self, layer: int) -> List[str]:
        """Get all blocks in a specific topological layer."""
        layer_blocks = []
        for block_id, block in self.logical_blocks.items():
            if self._calculate_topological_layer(block) == layer:
                layer_blocks.append(block_id)
        return layer_blocks

    def get_tips(self) -> List[str]:
        """Get current tip blocks (blocks with no children)."""
        tips = []
        for block_id in self.logical_blocks:
            has_children = False
            for other_id, other_block in self.logical_blocks.items():
                if other_id != block_id and block_id in other_block.parents:
                    has_children = True
                    break
            if not has_children:
                tips.append(block_id)
        return tips

    def get_tips_with_missed_blocks(self, missed_blocks: int = 0) -> List[str]:
        """Get tips considering missed blocks (for simulation)."""
        all_tips = self.get_tips()

        if missed_blocks == 0 or len(all_tips) <= missed_blocks:
            return all_tips

            # Return a subset of tips based on missed blocks
        # This simulates network delays where some recent blocks are missed
        creation_order_tips = []
        for block_id in reversed(self.creation_order):
            if block_id in all_tips:
                creation_order_tips.append(block_id)

                # Skip the most recent 'missed_blocks' tips
        return creation_order_tips[missed_blocks:] if len(creation_order_tips) > missed_blocks else creation_order_tips

    def validate_dag_integrity(self) -> bool:
        """Validate GHOSTDAG structure and consensus rules."""
        # Basic DAG validation
        for block_id, block in self.logical_blocks.items():
            if not block.validate_parents(self.logical_blocks):
                print(f"DAG integrity error: Block {block_id} has invalid parents")
                return False

                # GHOSTDAG-specific validation
        return self._validate_ghostdag_properties()

    def _validate_ghostdag_properties(self) -> bool:
        """Validate GHOSTDAG-specific properties."""
        for block_id, block in self.logical_blocks.items():
            if not hasattr(block.consensus_data, 'blue_score'):
                continue

                # Validate blue score calculation
            if not self._validate_blue_score(block):
                print(f"GHOSTDAG validation error: Invalid blue score for block {block_id}")
                return False

        return True

    def _validate_blue_score(self, block: ConsensusBlock) -> bool:
        """Validate that a block's blue score is correctly calculated."""
        if block.is_genesis():
            return block.consensus_data.blue_score == 0

            # For non-genesis blocks, blue score should be based on selected parent
        if hasattr(block.consensus_data, 'selected_parent') and block.consensus_data.selected_parent:
            parent_id = block.consensus_data.selected_parent
            if parent_id in self.logical_blocks:
                parent_block = self.logical_blocks[parent_id]
                expected_base_score = getattr(parent_block.consensus_data, 'blue_score', 0)
                mergeset_size = len(getattr(block.consensus_data, 'mergeset_blues', []))
                expected_score = expected_base_score + mergeset_size
                return block.consensus_data.blue_score == expected_score

        return True

    def get_highest_scoring_block(self) -> Optional[str]:
        """Get the block with the highest blue score."""
        if not self.block_scores:
            return None

        return max(self.block_scores.items(), key=lambda x: x[1])[0]

    def get_selected_parent_chain(self, from_block_id: str) -> List[str]:
        """Get the selected parent chain from a given block."""
        chain = []
        current = from_block_id

        while current and current in self.logical_blocks:
            chain.append(current)
            block = self.logical_blocks[current]

            if hasattr(block.consensus_data, 'selected_parent'):
                current = block.consensus_data.selected_parent
            else:
                break

        return chain

    def get_statistics(self) -> Dict[str, Any]:
        """Get GHOSTDAG statistics."""
        stats = {
            "total_blocks": len(self.logical_blocks),
            "consensus_type": self.consensus_type,
            "k_parameter": self.k,
            "tips": self.get_tips(),
            "blue_blocks": len(self.blue_blocks),
            "red_blocks": len(self.red_blocks),
            "highest_scoring_block": self.get_highest_scoring_block(),
        }

        if self.block_scores:
            stats.update({
                "max_blue_score": max(self.block_scores.values()),
                "avg_blue_score": sum(self.block_scores.values()) / len(self.block_scores),
            })

        return stats

        # Protocol compliance methods

    def get_block_count(self) -> int:
        """Get total number of blocks in the DAG."""
        return len(self.logical_blocks)

    def get_block(self, block_id: str) -> Optional[ConsensusBlock]:
        """Get a block by its ID."""
        return self.logical_blocks.get(block_id)

    def get_blocks_in_creation_order(self) -> List[ConsensusBlock]:
        """Get all blocks in the order they were created."""
        return [self.logical_blocks[block_id] for block_id in self.creation_order if block_id in self.logical_blocks]