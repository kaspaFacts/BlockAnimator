# BlockAnimator\blockanimator\consensus\dags\ghostdag\ghostdag_dag.py

from typing import Dict, List, Optional, Tuple, Any
from ..layer_dag import LayerDAG
from ...blocks.consensus_block import ConsensusBlock
from ...blocks.block_factory import ConsensusBlockFactory


class GhostdagDAG(LayerDAG):
    """GHOSTDAG-specific DAG implementation with Manim-like animation integration."""

    def __init__(self, scene, k: int = 3, **kwargs):
        super().__init__(scene, **kwargs)
        self.consensus_type = "ghostdag"
        self.k = k  # GHOSTDAG security parameter

        # Ensure required attributes are initialized
        if not hasattr(self, 'creation_order'):
            self.creation_order = []
        if not hasattr(self, 'logical_blocks'):
            self.logical_blocks = {}

            # GHOSTDAG-specific tracking
        self.blue_blocks: set = set()
        self.red_blocks: set = set()
        self.block_scores: Dict[str, int] = {}

    def add_ghostdag_block(self, block_id: str, parents: List[str] = None, **kwargs) -> List:
        """Add a GHOSTDAG block with automatic visual positioning and animations."""
        parents = parents or []

        # Ensure creation_order exists
        if not hasattr(self, 'creation_order'):
            self.creation_order = []
        if not hasattr(self, 'logical_blocks'):
            self.logical_blocks = {}

            # Create logical block for consensus tracking
        logical_block = ConsensusBlockFactory.create_block(
            self.consensus_type, block_id, parents, **kwargs
        )

        # Set creation order and store logical block
        logical_block.creation_order = len(self.creation_order)
        self.logical_blocks[block_id] = logical_block
        self.creation_order.append(block_id)

        # Calculate consensus data
        if hasattr(logical_block, 'calculate_consensus_data'):
            logical_block.calculate_consensus_data(self.k, self.logical_blocks)

            # Update GHOSTDAG-specific tracking
        self._update_ghostdag_classification(logical_block)

        # Use LayerDAG's add_with_layers method - this handles layer structure internally
        return super().add_with_layers(block_id, parents,
                                       consensus_type=self.consensus_type, **kwargs)

    def animate_blue_score_visualization(self, block_id: str) -> List:
        """Create animations to visualize blue score changes."""
        if block_id not in self.blocks:
            return []

        block = self.blocks[block_id]
        logical_block = self.logical_blocks.get(block_id)

        animations = []
        if logical_block and hasattr(logical_block, 'consensus_data'):
            blue_score = getattr(logical_block.consensus_data, 'blue_score', 0)

            # Use grid-based offsets for blue score visualization
            grid_offset_y = blue_score * 0.5  # Grid units, not pixels

            # Create proxy animations with grid offsets
            proxy = block.animate.shift((0, grid_offset_y))
            if block_id in self.blue_blocks:
                proxy = proxy.change_color((0, 0, 255))
            else:
                proxy = proxy.change_color((255, 0, 0))

                # Extract the actual animations from the proxy
            animations.extend(proxy.pending_animations)
            proxy.pending_animations.clear()  # Reset for next use

        return animations

    def animate_selected_parent_chain(self, from_block_id: str) -> List:
        """Animate the selected parent chain highlighting."""
        chain = self.get_selected_parent_chain(from_block_id)
        animations = []

        for i, block_id in enumerate(chain):
            if block_id in self.blocks:
                block = self.blocks[block_id]
                # Highlight with green color and slight grid movement
                animations.append(block.animate.change_color((0, 255, 0)))
                animations.append(block.animate.shift((0, -1)))  # Grid offset upward

        return animations

    def animate_mergeset_visualization(self, block_id: str) -> List:
        """Animate the visualization of a block's mergeset."""
        if block_id not in self.blocks or block_id not in self.logical_blocks:
            return []

        logical_block = self.logical_blocks[block_id]
        animations = []

        if hasattr(logical_block, 'consensus_data') and hasattr(logical_block.consensus_data, 'mergeset_blues'):
            mergeset = logical_block.consensus_data.mergeset_blues

            # Animate each block in the mergeset
            for i, mergeset_block_id in enumerate(mergeset):
                if mergeset_block_id in self.blocks:
                    block = self.blocks[mergeset_block_id]
                    # Pulse animation to show inclusion in mergeset
                    animations.append(block.animate.fade_to(200, duration=0.5))
                    animations.append(block.animate.fade_to(255, duration=0.5))

        return animations

    def create_ghostdag_visualization_sequence(self, block_ids: List[str]) -> List:
        """Create a complete GHOSTDAG visualization sequence using the new animation system."""
        all_animations = []

        # Step 1: Add all blocks
        for block_id in block_ids:
            parents = self._get_parents_for_block(block_id)
            block_anims = self.add_ghostdag_block(block_id, parents)
            all_animations.extend(block_anims)

            # Step 2: Animate consensus calculations
        for block_id in block_ids:
            if block_id in self.blocks:
                viz_anims = self.animate_blue_score_visualization(block_id)
                all_animations.extend(viz_anims)

        return all_animations

    def animate_final_ghostdag_result(self) -> List:
        """Create final animation showing GHOSTDAG results using deferred animation system."""
        highest_score_block = self.get_highest_scoring_block()
        if not highest_score_block:
            return []

        animations = []

        # Animate the selected parent chain
        chain_anims = self.animate_selected_parent_chain(highest_score_block)
        animations.extend(chain_anims)

        # Move chain blocks to target position using deferred animations with grid coordinates
        chain = self.get_selected_parent_chain(highest_score_block)
        target_grid_y = 5  # Grid coordinate, not pixel

        for i, block_id in enumerate(chain):
            if block_id in self.blocks:
                block = self.blocks[block_id]
                # Use deferred animation system - calculates offset at execution time
                # Access current grid position properly
                current_grid_y = block.grid_y
                grid_offset_y = target_grid_y - current_grid_y
                animations.append(block.animate.shift((0, grid_offset_y)))

        return animations

    def _update_ghostdag_classification(self, block: ConsensusBlock) -> None:
        """Update blue/red classification and scores."""
        if hasattr(block, 'consensus_data') and hasattr(block.consensus_data, 'blue_score'):
            self.block_scores[block.block_id] = block.consensus_data.blue_score

            # Classify as blue (simplified - could be more complex based on mergeset)
            self.blue_blocks.add(block.block_id)
            if block.block_id in self.red_blocks:
                self.red_blocks.remove(block.block_id)

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

            if (hasattr(block, 'consensus_data') and
                    hasattr(block.consensus_data, 'selected_parent') and
                    block.consensus_data.selected_parent):
                current = block.consensus_data.selected_parent
            else:
                break

        return chain

    def get_blue_blocks(self) -> List[str]:
        """Get all blocks classified as blue."""
        return list(self.blue_blocks)

    def get_red_blocks(self) -> List[str]:
        """Get all blocks classified as red."""
        return list(self.red_blocks)

    def _get_parents_for_block(self, block_id: str) -> List[str]:
        """Helper method to get parents for a block based on GHOSTDAG logic."""
        # Handle genesis block
        if block_id == "genesis":
            return []

            # Check if block already exists in logical_blocks
        if hasattr(self, 'logical_blocks') and block_id in self.logical_blocks:
            logical_block = self.logical_blocks[block_id]
            return logical_block.parents if hasattr(logical_block, 'parents') else []

            # For new blocks, implement your parent selection logic here
        # This is a placeholder - you should implement based on your GHOSTDAG requirements
        existing_blocks = list(self.logical_blocks.keys()) if hasattr(self, 'logical_blocks') else []
        if existing_blocks:
            # Simple example: use the last created block as parent
            return [existing_blocks[-1]]

        return []

    def validate_dag_integrity(self) -> bool:
        """Validate GHOSTDAG structure and consensus rules."""
        # First validate basic DAG integrity using parent's method
        if not super().validate_dag_integrity():
            return False

            # GHOSTDAG-specific validation
        return self._validate_ghostdag_properties()

    def _validate_ghostdag_properties(self) -> bool:
        """Validate GHOSTDAG-specific properties."""
        for block_id, block in self.logical_blocks.items():
            if not hasattr(block, 'consensus_data'):
                continue

            if hasattr(block.consensus_data, 'blue_score'):
                # Validate blue score calculation
                if not self._validate_blue_score(block):
                    return False

        return True

    def _validate_blue_score(self, block: ConsensusBlock) -> bool:
        """Validate that a block's blue score is correctly calculated."""
        if block.is_genesis():
            return block.consensus_data.blue_score == 0

            # For non-genesis blocks, validate based on selected parent and mergeset
        if (hasattr(block.consensus_data, 'selected_parent') and
                block.consensus_data.selected_parent):
            parent_id = block.consensus_data.selected_parent
            if parent_id in self.logical_blocks:
                parent_block = self.logical_blocks[parent_id]
                if hasattr(parent_block, 'consensus_data'):
                    expected_base_score = getattr(parent_block.consensus_data, 'blue_score', 0)
                    mergeset_size = len(getattr(block.consensus_data, 'mergeset_blues', []))
                    expected_score = expected_base_score + mergeset_size
                    return block.consensus_data.blue_score == expected_score

        return True

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
            "max_layer": self.get_max_layer() if hasattr(self, 'get_max_layer') else 0,
        }

        if self.block_scores:
            stats.update({
                "max_blue_score": max(self.block_scores.values()),
                "avg_blue_score": sum(self.block_scores.values()) / len(self.block_scores),
            })

        return stats