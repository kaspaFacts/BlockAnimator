# BlockAnimator\blockanimator\consensus\layer_dag.py

from blockanimator.consensus.dags.base_dag import BlockDAG
from blockanimator.consensus.dag_types import StyledParent

class LayerDAG(BlockDAG):
    def __init__(self, scene, layer_spacing=10, chain_spacing=6, width=4):
        super().__init__(scene)
        self.layers = []
        self.layer_spacing = layer_spacing
        self.chain_spacing = chain_spacing
        self.genesis_pos = (10, 25)
        self.width = width

        # Track each block's topological layer for proper ordering
        self.block_layers = {}

    def add_with_layers(self, block_id, parent_names=None, **kwargs):
        """Add block with proper topological layer calculation"""
        if parent_names is None:
            parent_names = []

            # Normalize parent names
        if isinstance(parent_names, str):
            parent_names = [parent_names]

            # Calculate proper topological layer
        if not parent_names:  # Genesis block
            layer = 0
            pos = self.genesis_pos
            if not self.layers:
                self.layers.append([])
        else:
            layer = self._calculate_topological_layer(parent_names)
            pos = self._calculate_layer_position(layer)

            # Convert parent names to Parent objects
        parents = [StyledParent(p) if isinstance(p, str) else p for p in parent_names]

        # Extract parameters that conflict with method signature
        label = kwargs.pop('label', None)
        kwargs.pop('parents', None)

        # Get fade-in animations - pass parameters explicitly
        fade_animations = super().add(block_id, pos, label=label, parents=parents, **kwargs)

        # Update layer tracking AFTER block is added to self.blocks
        self._update_layer_structure(layer, block_id)

        # Get adjustment animations
        adjustment_animations = self._auto_adjust_affected_layers(layer)

        # Return animations for manual scheduling instead of auto-scheduling
        all_animations = fade_animations[:]
        if adjustment_animations:
            all_animations.extend(adjustment_animations)

        return all_animations

    def _calculate_topological_layer(self, parent_names):
        """Calculate the correct topological layer ensuring all parents are in lower layers."""
        if not parent_names:
            return 0

            # Extract parent IDs from Parent objects
        parent_ids = []
        for parent in parent_names:
            if isinstance(parent, StyledParent):
                parent_ids.append(parent.parent_id)
            else:
                parent_ids.append(parent)

                # Find the maximum layer of ALL parents
        max_parent_layer = -1
        for parent_id in parent_ids:
            if parent_id in self.block_layers:
                parent_layer = self.block_layers[parent_id]
                max_parent_layer = max(max_parent_layer, parent_layer)
            else:
                # If parent doesn't exist, this is an error
                raise ValueError(f"Parent block '{parent_id}' not found in layer tracking")

                # Child must be in a layer strictly higher than ALL its parents
        return max_parent_layer + 1

    def _update_layer_structure(self, target_layer, block_id):
        """Update the layer structure to accommodate the new block."""
        # Extend layers list if necessary
        while len(self.layers) <= target_layer:
            self.layers.append([])

            # Add block to the target layer
        self.layers[target_layer].append(block_id)

        # Track the block's layer for future topological calculations
        self.block_layers[block_id] = target_layer

    def _calculate_layer_position(self, layer):
        """Calculate position for a block in the given layer"""
        x_pos = self.genesis_pos[0] + (layer * self.layer_spacing)

        # Stack blocks vertically within the layer
        if layer < len(self.layers) and self.layers[layer]:
            last_block = self.layers[layer][-1]
            # Access grid_pos directly from the block object, not as dictionary
            last_y = self.blocks[last_block].grid_pos[1]
            y_pos = last_y + self.chain_spacing
        else:
            y_pos = self.genesis_pos[1]

        return (x_pos, y_pos)

    def validate_topological_ordering(self):
        """Validate that all blocks respect topological ordering."""
        for block_id, layer in self.block_layers.items():
            if block_id in self.blocks:
                block = self.blocks[block_id]
                if hasattr(block, 'parents') and block.parents:  # Check if block has parents attribute
                    for parent_id in block.parents:  # Access parents directly
                        if parent_id in self.block_layers:
                            parent_layer = self.block_layers[parent_id]
                            if parent_layer >= layer:
                                print(f"Topological violation: {parent_id} (layer {parent_layer}) "
                                      f"should be before {block_id} (layer {layer})")
                                return False
        return True

    def _auto_adjust_affected_layers(self, affected_layer):
        """Automatically adjust positions when blocks are added"""
        animations = []

        # If this layer now has multiple blocks, we might need to center them
        if len(self.layers[affected_layer]) > 1:
            animations.extend(self._adjust_single_layer(affected_layer))

        return animations

    def _adjust_single_layer(self, layer_index):
        """Adjust positioning for a single layer"""
        if layer_index >= len(self.layers):
            return []

        layer_blocks = self.layers[layer_index]
        if len(layer_blocks) <= 1:
            return []

        animations = []

        # Calculate the base Y position for this layer
        base_y = self.genesis_pos[1]
        if layer_index > 0:
            # Position relative to previous layer
            prev_layer_blocks = self.layers[layer_index - 1]
            if prev_layer_blocks:
                # Find the middle Y of the previous layer - access grid_pos directly from block objects
                prev_ys = [self.blocks[bid].grid_pos[1] for bid in prev_layer_blocks]
                base_y = sum(prev_ys) / len(prev_ys)

                # Calculate X position for this layer
        x_pos = self.genesis_pos[0] + (layer_index * self.layer_spacing)

        # Distribute blocks evenly around the base Y position
        total_height = (len(layer_blocks) - 1) * self.chain_spacing
        start_y = base_y - (total_height / 2)

        for i, block_id in enumerate(layer_blocks):
            new_y = start_y + (i * self.chain_spacing)
            new_pos = (x_pos, new_y)
            current_pos = self.blocks[block_id].grid_pos

            if new_pos != current_pos:
                # Update our internal tracking
                self.blocks[block_id].grid_pos = new_pos
                # Create animation to move the block
                animations.append(self.move_to(block_id, new_pos, duration=0.5))

        return animations

    def adjust_layers(self):
        """Create animations to center blocks within their layers"""
        animations = []
        for layer_index in range(len(self.layers)):
            animations.extend(self._adjust_single_layer(layer_index))

        return animations  # Return for manual scheduling

    def rebalance_all_layers(self):
        """Manually trigger a full rebalancing of all layers"""
        animations = []
        for layer_index in range(len(self.layers)):
            animations.extend(self._adjust_single_layer(layer_index))
        return animations