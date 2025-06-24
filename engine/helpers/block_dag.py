"""BlockDAG helper with grid coordinates."""
from engine.animations import FadeInAnimation, MoveToAnimation, ColorChangeAnimation

class BlockDAG:
    def __init__(self, scene, history_size=20):
        self.scene = scene
        self.blocks = {}
        self.history = []  # History of tip states
        self.history_size = history_size
        # Store reference to block positions in scene
        if not hasattr(scene, '_block_positions'):
            scene._block_positions = {}

    def add(self, block_id, grid_pos, label=None, parents=None, **kwargs):
        """Add a block at grid position with automatic parent connections."""
        grid_x, grid_y = grid_pos

        sprite = self.scene.add_sprite(
            block_id, grid_x, grid_y,
            text=label or block_id,
            **kwargs
        )

        # Store the block data
        self.blocks[block_id] = {
            'grid_pos': (grid_x, grid_y),
            'sprite': sprite,
            'parents': parents or []  # Store parent relationships
        }

        # Store in scene for camera targeting
        self.scene._block_positions[block_id] = self.blocks[block_id]

        # Create animations list - start with block fade-in
        animations = [FadeInAnimation(
            sprite_id=block_id,
            duration=1.0
        )]

        # Add parent connections that fade in simultaneously
        if parents:
            for parent in parents:
                parent_id = parent.parent_id if isinstance(parent, Parent) else parent
                if parent_id in self.blocks:
                    connection_id = f"{parent_id}_to_{block_id}"

                    # Create connection with custom properties
                    connection_kwargs = {}
                    if isinstance(parent, Parent):
                        if parent.color:
                            connection_kwargs['color'] = parent.color
                        if parent.selected_parent:
                            connection_kwargs['selected_parent'] = True

                            # NEW: Set color based on whether this is the selected parent
                    # Check if the sprite has GHOSTDAG data and if this parent is the selected parent
                    if (hasattr(sprite, 'ghostdag_data') and
                            sprite.ghostdag_data and
                            sprite.ghostdag_data.selected_parent == parent_id):
                        connection_kwargs['color'] = (0, 0, 255)  # Blue for selected parent
                    else:
                        # Only override color if not already set by Parent object
                        if 'color' not in connection_kwargs:
                            connection_kwargs['color'] = (255, 255, 255)  # White for other parents

                    self.scene.add_connection(connection_id, block_id, parent_id, **connection_kwargs)

                    # Add connection fade-in animation
                    animations.append(FadeInAnimation(
                        sprite_id=connection_id
                    ))

                    # After successfully adding the block, update history
        self._update_history()

        return animations

    def _update_history(self):
        """Update the history with current tips."""
        current_tips = self._get_current_tips()
        self.history.insert(0, current_tips)
        if len(self.history) > self.history_size:
            self.history.pop()

    def _get_current_tips(self):
        """Get current tip blocks (blocks with no children)."""
        tips = []
        for block_id in self.blocks:
            has_children = False
            for other_id, other_data in self.blocks.items():
                if other_id != block_id:
                    other_parents = other_data['parents']
                    parent_ids = [p.parent_id if isinstance(p, Parent) else p for p in other_parents]
                    if block_id in parent_ids:
                        has_children = True
                        break
            if not has_children:
                tips.append(block_id)
        return tips

    def get_tips(self, missed_blocks=0):
        """Get the tips from history at a specific point in time."""
        if not self.history:
            return []
        history_index = min(missed_blocks, len(self.history) - 1)
        return self.history[history_index]

    def shift(self, block_id, offset, run_time=1.0):
        """Move a block by grid offset."""
        if block_id not in self.blocks:
            return None

        block = self.blocks[block_id]
        current_grid = block['grid_pos']
        new_grid = (current_grid[0] + offset[0], current_grid[1] + offset[1])

        # Update tracking
        block['grid_pos'] = new_grid

        return MoveToAnimation(
            sprite_id=block_id,
            target_grid_x=new_grid[0],
            target_grid_y=new_grid[1],
            duration=run_time
        )

    def connect(self, from_block_id, to_block_id, connection_id=None, **kwargs):
        """Create a connection between two blocks."""
        if connection_id is None:
            connection_id = f"{from_block_id}_to_{to_block_id}"

        if from_block_id in self.blocks and to_block_id in self.blocks:
            connection = self.scene.add_connection(
                connection_id, from_block_id, to_block_id, **kwargs
            )

            # Return fade-in animation for the connection
            return FadeInAnimation(
                sprite_id=connection_id
            )
        return None

    def connect_many(self, from_block_id, to_block_ids, **kwargs):
        """Create connections from one block to many others."""
        connections = []
        for to_block_id in to_block_ids:
            connection_anim = self.connect(from_block_id, to_block_id, **kwargs)
            if connection_anim:
                connections.append(connection_anim)
        return connections

class Parent:
    """Helper for defining parent relationships with styling."""

    def __init__(self, parent_id, color=None, width=2, selected_parent=False, **kwargs):
        self.parent_id = parent_id
        self.color = color
        self.width = width
        self.selected_parent = selected_parent
        self.kwargs = kwargs

class LayerDAG(BlockDAG):
    def __init__(self, scene, layer_spacing=15, chain_spacing=8, width=4):
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
        parents = [Parent(p) if isinstance(p, str) else p for p in parent_names]

        # Extract parameters that conflict with method signature
        label = kwargs.pop('label', None)
        kwargs.pop('parents', None)

        # Get fade-in animations - pass parameters explicitly
        fade_animations = super().add(block_id, pos, label=label, parents=parents, **kwargs)

        # NOW update layer tracking AFTER block is added to self.blocks
        self._update_layer_structure(layer, block_id)

        # Get adjustment animations - now safe because block exists
        adjustment_animations = self._auto_adjust_affected_layers(layer)

        # Use sequential timing: fade first, then adjust
        animation_groups = [fade_animations]
        if adjustment_animations:
            animation_groups.append(adjustment_animations)

            # Schedule sequential animations using the enhanced controller
        end_frame = self.scene.animation_controller.play_sequential(animation_groups)

        # Update scene timing to account for the full sequence
        self.scene.current_frame = end_frame
        self.scene.scene_duration_frames = max(self.scene.scene_duration_frames, end_frame)

        return []  # Return empty since animations are already scheduled

    def _calculate_topological_layer(self, parent_names):
        """Calculate the correct topological layer ensuring all parents are in lower layers."""
        if not parent_names:
            return 0

            # Extract parent IDs from Parent objects
        parent_ids = []
        for parent in parent_names:
            if isinstance(parent, Parent):
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
            last_y = self.blocks[last_block]['grid_pos'][1]
            y_pos = last_y + self.chain_spacing
        else:
            y_pos = self.genesis_pos[1]

        return (x_pos, y_pos)

    def validate_topological_ordering(self):
        """Validate that all blocks respect topological ordering."""
        for block_id, layer in self.block_layers.items():
            if block_id in self.blocks:
                block_data = self.blocks[block_id]
                if 'parents' in block_data:
                    for parent_id in block_data['parents']:
                        if parent_id in self.block_layers:
                            parent_layer = self.block_layers[parent_id]
                            if parent_layer >= layer:
                                print(f"Topological violation: {parent_id} (layer {parent_layer}) "
                                      f"should be before {block_id} (layer {layer})")
                                return False
        return True

        # Keep your existing methods for adjustment and positioning

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
                # Find the middle Y of the previous layer
                prev_ys = [self.blocks[bid]['grid_pos'][1] for bid in prev_layer_blocks]
                base_y = sum(prev_ys) / len(prev_ys)

                # Calculate X position for this layer
        x_pos = self.genesis_pos[0] + (layer_index * self.layer_spacing)

        # Distribute blocks evenly around the base Y position
        total_height = (len(layer_blocks) - 1) * self.chain_spacing
        start_y = base_y - (total_height / 2)

        for i, block_id in enumerate(layer_blocks):
            new_y = start_y + (i * self.chain_spacing)
            new_pos = (x_pos, new_y)
            current_pos = self.blocks[block_id]['grid_pos']

            if new_pos != current_pos:
                # Update our internal tracking
                self.blocks[block_id]['grid_pos'] = new_pos
                # Create animation to move the block
                animations.append(self.scene.move_to(block_id, new_pos, duration=0.5))

        return animations

    def adjust_layers(self):
        """Create animations to center blocks within their layers"""
        animations = []
        for layer_index in range(len(self.layers)):
            animations.extend(self._adjust_single_layer(layer_index))

            # Use simultaneous timing for manual layer adjustments
        if animations:
            end_frame = self.scene.animation_controller.play_simultaneous(animations)
            self.scene.current_frame = end_frame
            self.scene.scene_duration_frames = max(self.scene.scene_duration_frames, end_frame)

        return []  # Return empty since animations are already scheduled

class GhostDAG(LayerDAG):
    def __init__(self, scene, k=3, **kwargs):
        super().__init__(scene, **kwargs)
        self.k = k

    def add_with_ghostdag(self, block_id, parent_names=None, **kwargs):
        """Add block with GHOSTDAG logic using internal block registry"""
        parent_names = parent_names or []

        # Convert to Parent objects for connection styling
        if isinstance(parent_names, str):
            parent_names = [parent_names]
        parents = [Parent(p) if isinstance(p, str) else p for p in parent_names]

        # Extract parent IDs for GhostdagBlock - THIS IS THE KEY FIX
        parent_ids = [p.parent_id if isinstance(p, Parent) else p for p in parents]

        # Pass GHOSTDAG-specific parameters with a different key name
        kwargs['consensus_type'] = 'ghostdag'
        kwargs['ghostdag_parents'] = parent_ids  # Use different key to avoid removal
        kwargs['ghostdag_k'] = self.k
        kwargs['scene_registry'] = self._get_ghostdag_registry()

        # Call the parent method
        result = super().add_with_layers(block_id, parents, **kwargs)
        return result

    def _get_ghostdag_registry(self):
        """Get current GhostdagBlocks from self.blocks"""
        registry = {}
        for block_id, block_data in self.blocks.items():
            sprite = block_data['sprite']
            if hasattr(sprite, 'ghostdag_data'):  # Only include GhostdagBlocks
                registry[block_id] = sprite
        return registry

    def create_final_ghostdag_animation(self):
        """Create final animation showing GHOSTDAG results using GhostdagData"""
        # Find block with highest blue score using GhostdagData
        highest_score_block = None
        highest_score = -1

        for block_id, block_data in self.blocks.items():
            sprite = block_data['sprite']
            if hasattr(sprite, 'ghostdag_data'):
                if sprite.ghostdag_data.blue_score > highest_score:
                    highest_score = sprite.ghostdag_data.blue_score
                    highest_score_block = block_id

        if not highest_score_block:
            return []

        animations = []

        # Phase 1: Trace the selected parent chain using GhostdagData
        current = highest_score_block
        chain_blocks = []

        while current and current in self.blocks:
            chain_blocks.append(current)
            sprite = self.blocks[current]['sprite']
            if hasattr(sprite, 'ghostdag_data') and sprite.ghostdag_data.selected_parent:
                current = sprite.ghostdag_data.selected_parent
            else:
                break

                # Store original positions
        original_positions = {}
        for block_id in self.blocks:
            original_positions[block_id] = self.blocks[block_id]['grid_pos']

            # Phase 2: Move parent chain to target Y position
        target_chain_y = 10

        for block_id in chain_blocks:
            current_pos = original_positions[block_id]
            new_pos = (current_pos[0], target_chain_y)

            animations.append(MoveToAnimation(
                sprite_id=block_id,
                target_grid_x=new_pos[0],
                target_grid_y=new_pos[1],
                duration=1.0
            ))

            # Phase 3: Position mergeset blocks using GhostdagData
        mergeset_blocks = []

        for block_id, block_data in self.blocks.items():
            if block_id not in chain_blocks and block_id != 'Gen':
                sprite = block_data['sprite']
                if hasattr(sprite, 'ghostdag_data'):
                    selected_parent = sprite.ghostdag_data.selected_parent
                    if selected_parent and selected_parent in chain_blocks:
                        mergeset_blocks.append((
                            block_id,
                            selected_parent,
                            sprite.ghostdag_data.blue_score
                        ))

                        # Sort mergeset blocks by blue score
        mergeset_blocks.sort(key=lambda x: x[2])

        # Position mergeset blocks above their selected parents
        mergeset_base_offset_y = 8
        parent_mergeset_stack_count = {}

        for i, (block_id, selected_parent_id, score) in enumerate(mergeset_blocks):
            stack_index = parent_mergeset_stack_count.get(selected_parent_id, 0)
            parent_mergeset_stack_count[selected_parent_id] = stack_index + 1

            parent_pos = original_positions[selected_parent_id]
            current_pos = original_positions[block_id]

            x_diff = current_pos[0] - parent_pos[0]
            x_offset = x_diff * 0.2
            if abs(x_offset) < 0.5:
                x_offset = 0.5 if x_diff >= 0 else -0.5

            y_offset = mergeset_base_offset_y + (stack_index * 2.0)
            new_pos = (parent_pos[0] + x_offset, target_chain_y + y_offset)

            animations.append(MoveToAnimation(
                sprite_id=block_id,
                target_grid_x=new_pos[0],
                target_grid_y=new_pos[1],
                duration=1.0,
                delay=0.5 + i * 0.1
            ))

            # Phase 4: Color the main chain blue
        for i, block_id in enumerate(chain_blocks):
            animations.append(ColorChangeAnimation(
                sprite_id=block_id,
                target_color=(50, 150, 255),
                duration=0.3,
                delay=2.0 + i * 0.1
            ))

            # Phase 5: Color mergeset blocks using GhostdagData
        for i, (block_id, selected_parent_id, _) in enumerate(mergeset_blocks):
            sprite = self.blocks[block_id]['sprite']

            # Check if block is in the mergeset_blues of its selected parent
            if hasattr(sprite, 'ghostdag_data'):
                parent_sprite = self.blocks[selected_parent_id]['sprite']
                if (hasattr(parent_sprite, 'ghostdag_data') and
                        block_id in parent_sprite.ghostdag_data.mergeset_blues):
                    color = (100, 200, 255)  # Light blue for blue mergeset blocks
                else:
                    color = (255, 100, 50)  # Red for red mergeset blocks
            else:
                color = (128, 128, 128)  # Gray fallback

            animations.append(ColorChangeAnimation(
                sprite_id=block_id,
                target_color=color,
                duration=0.3,
                delay=2.5 + i * 0.1
            ))

        return animations

    def rebalance_all_layers(self):
        """Manually trigger a full rebalancing of all layers"""
        animations = []
        for layer_index in range(len(self.layers)):
            animations.extend(self._adjust_single_layer(layer_index))
        return animations

WHITE = (255, 255, 255)

#   TODO fix ghostdag, after adding ghostdag dataclass, all blocks are created with BS:0 and lines are red