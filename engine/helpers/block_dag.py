"""BlockDAG helper with grid coordinates."""
import random


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

        self.blocks[block_id] = {
            'grid_pos': (grid_x, grid_y),
            'sprite': sprite,
            'parents': parents or []  # Store parent relationships
        }

        # Store in scene for camera targeting
        self.scene._block_positions[block_id] = self.blocks[block_id]

        # Create animations list - start with block fade-in
        animations = [{
            'type': 'fade_in',
            'sprite_id': block_id,
            'duration': 1.0  # or whatever duration you prefer
        }]

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

                    self.scene.add_connection(connection_id, block_id, parent_id, **connection_kwargs)

                    # Add connection fade-in animation
                    animations.append({
                        'type': 'fade_in',
                        'sprite_id': connection_id
                    })

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

        return {
            'type': 'move_to',
            'sprite_id': block_id,
            'start_grid_x': current_grid[0],
            'start_grid_y': current_grid[1],
            'target_grid_x': new_grid[0],
            'target_grid_y': new_grid[1]
        }

    # Add to BlockDAG class
    def connect(self, from_block_id, to_block_id, connection_id=None, **kwargs):
        """Create a connection between two blocks."""
        if connection_id is None:
            connection_id = f"{from_block_id}_to_{to_block_id}"

        if from_block_id in self.blocks and to_block_id in self.blocks:
            connection = self.scene.add_connection(
                connection_id, from_block_id, to_block_id, **kwargs
            )

            # Return fade-in animation for the connection
            return {
                'type': 'fade_in',
                'sprite_id': connection_id
           }
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

    def add_with_layers(self, block_id, parent_names=None, **kwargs):
        """Add block with automatic sequential animation using timing functions"""
        if parent_names is None:
            parent_names = []

            # Normalize parent names
        if isinstance(parent_names, str):
            parent_names = [parent_names]

            # Find appropriate layer and position
        if not parent_names:  # Genesis block
            layer = 0
            pos = self.genesis_pos
            if not self.layers:
                self.layers.append([])
        else:
            top_parent_layer = self._find_top_parent_layer(parent_names)
            layer = self._find_available_layer(top_parent_layer)
            pos = self._calculate_layer_position(layer)

            # Add to layer tracking BEFORE calling parent add
        if layer >= len(self.layers):
            self.layers.append([])
        self.layers[layer].append(block_id)

        # Convert parent names to Parent objects
        parents = [Parent(p) if isinstance(p, str) else p for p in parent_names]

        # Get fade-in animations
        fade_animations = super().add(block_id, pos, parents=parents, **kwargs)

        # Get adjustment animations
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

    def _find_top_parent_layer(self, parent_names):
        """Find the topmost layer containing any parent block"""
        # Extract parent IDs from Parent objects
        parent_ids = []
        for parent in parent_names:
            if isinstance(parent, Parent):
                parent_ids.append(parent.parent_id)
            else:
                parent_ids.append(parent)

        top_layer = 0
        for i, layer_blocks in enumerate(self.layers):
            if any(parent_id in layer_blocks for parent_id in parent_ids):
                top_layer = i
        return top_layer

    def _find_available_layer(self, top_parent_layer):
        """Find next available layer for block placement"""
        # Start from the layer AFTER the topmost parent layer
        min_layer = top_parent_layer + 1

        # Check existing layers for space, but only layers after all parents
        for i in range(min_layer, len(self.layers)):
            if len(self.layers[i]) < self.width:
                return i

                # All layers full or no suitable layers exist, create new one
        return len(self.layers)

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

    def get_tips(self, missed_blocks=0):
        """Get tip blocks, optionally from history."""
        return super().get_tips(missed_blocks)

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
        self.blue_blocks = set()
        self.red_blocks = set()
        self.block_scores = {}
        self.block_work = {}

    def add_with_ghostdag(self, block_id, parent_names=None, **kwargs):
        """Add block with both layer positioning and GHOSTDAG logic"""
        parent_names = parent_names or []

        # Assign random work for demo
        self.block_work[block_id] = random.randint(100, 1000)

        # Convert to Parent objects for GHOSTDAG processing
        if isinstance(parent_names, str):
            parent_names = [parent_names]
        parents = [Parent(p) if isinstance(p, str) else p for p in parent_names]

        # Run GHOSTDAG algorithm
        is_blue = self._check_blue_candidate(block_id, parents)

        # Update block sets
        if is_blue:
            self.blue_blocks.add(block_id)
            color = (50, 150, 255)  # Blue for honest blocks
        else:
            self.red_blocks.add(block_id)
            color = (255, 100, 50)  # Red for potentially dishonest blocks

        # Calculate blue score
        blue_score = self._calculate_blue_score(block_id, parents)
        self.block_scores[block_id] = blue_score

        # Set visual properties
        kwargs['label'] = str(blue_score)  # Only show blue score

        # Highlight selected parent connection
        if parents:
            selected_parent = self._find_selected_parent(parents)
            for i, parent in enumerate(parents):
                parent_id = parent.parent_id if isinstance(parent, Parent) else parent
                if parent_id == selected_parent:
                    if isinstance(parent, Parent):
                        parent.color = (0, 100, 255)  # Blue color
                        parent.width = 4
                        parent.selected_parent = True  # Mark as selected parent
                    else:
                        parents[i] = Parent(parent_id, color=(0, 100, 255), width=4, selected_parent=True)

        return super().add_with_layers(block_id, parents, **kwargs)

    def create_final_ghostdag_animation(self):
        """Create final animation showing GHOSTDAG results with proper positioning"""
        # Find block with highest blue score
        highest_score_block = max(self.block_scores.items(), key=lambda x: x[1])
        highest_block_id = highest_score_block[0]

        animations = []

        # Phase 1: Trace the selected parent chain
        current = highest_block_id
        chain_blocks = []

        while current and current in self.blocks:
            chain_blocks.append(current)
            parents = self.blocks[current]['parents']
            if parents:
                selected_parent = self._find_selected_parent(parents)
                current = selected_parent
            else:
                break

                # Store original positions before any modifications
        original_positions = {}
        for block_id in self.blocks:
            original_positions[block_id] = self.blocks[block_id]['grid_pos']

            # Phase 2: Move parent chain to grid Y position 10 (same Y for all)
        target_chain_y = 10  # Lower value to move toward bottom in your coordinate system

        for block_id in chain_blocks:
            current_pos = original_positions[block_id]
            new_pos = (current_pos[0], target_chain_y)  # Same Y for all chain blocks

            animations.append({
                'type': 'move_to',
                'sprite_id': block_id,
                'target_grid_x': new_pos[0],
                'target_grid_y': new_pos[1],
                'duration': 1.0
            })

            # Phase 3: Position mergeset blocks above the parent chain
        mergeset_blocks = []
        for block_id in self.blocks:
            if block_id not in chain_blocks and block_id != 'Gen':
                parents = self.blocks[block_id]['parents']
                if parents:
                    selected_parent = self._find_selected_parent(parents)
                    if selected_parent in chain_blocks:
                        mergeset_blocks.append((block_id, selected_parent, self.block_scores.get(block_id, 0)))

                        # Sort mergeset blocks by blue score (ascending order like GHOSTDAG)
        mergeset_blocks.sort(key=lambda x: x[2])

        # Position mergeset blocks above their selected parents
        # In your coordinate system, "above" means higher Y values
        mergeset_base_offset_y = 8  # Consistent vertical offset from the parent chain's final Y

        # Dictionary to track how many mergeset blocks are stacked above each parent
        parent_mergeset_stack_count = {}

        for i, (block_id, selected_parent_id, score) in enumerate(mergeset_blocks):
            # Get the current stack count for this parent
            stack_index = parent_mergeset_stack_count.get(selected_parent_id, 0)
            parent_mergeset_stack_count[selected_parent_id] = stack_index + 1

            parent_pos = original_positions[selected_parent_id]
            current_pos = original_positions[block_id]

            # Calculate horizontal offset: proportional to original difference, or a small fixed value
            # This makes the block offset slightly towards its original X relative to its parent
            x_diff = current_pos[0] - parent_pos[0]
            x_offset = x_diff * 0.2  # Adjust multiplier (e.g., 0.1 to 0.5) for desired "pull"
            if abs(x_offset) < 0.5:  # Ensure a minimum offset if difference is too small
                x_offset = 0.5 if x_diff >= 0 else -0.5

                # Calculate vertical offset: base offset + stack index * spacing
            y_offset = mergeset_base_offset_y + (stack_index * 2.0)  # 2.0 is spacing between stacked mergeset blocks

            new_pos = (parent_pos[0] + x_offset, target_chain_y + y_offset)

            animations.append({
                'type': 'move_to',
                'sprite_id': block_id,
                'target_grid_x': new_pos[0],
                'target_grid_y': new_pos[1],
                'duration': 1.0,
                'delay': 0.5 + i * 0.1
            })

            # Phase 4: Color the main chain blue
        for i, block_id in enumerate(chain_blocks):
            animations.append({
                'type': 'color_change',
                'sprite_id': block_id,
                'target_color': (50, 150, 255),  # Blue for main chain
                'duration': 0.3,
                'delay': 2.0 + i * 0.1  # After movement completes
            })

            # Phase 5: Color mergeset blocks
        for i, (block_id, _, _) in enumerate(mergeset_blocks):
            if block_id in self.blue_blocks:
                color = (100, 200, 255)  # Lighter blue for honest mergeset blocks
            else:
                color = (255, 100, 50)  # Red for dishonest blocks

            animations.append({
                'type': 'color_change',
                'sprite_id': block_id,
                'target_color': color,
                'duration': 0.3,
                'delay': 2.5 + i * 0.1
            })

        return animations

    def _check_blue_candidate(self, block_id, parents):
        # Your existing implementation
        current_blues = len([p for p in parents if (p.parent_id if isinstance(p, Parent) else p) in self.blue_blocks])
        if current_blues >= self.k + 1:
            return False

        selected_parent = self._find_selected_parent(parents)
        if not selected_parent:
            return True

        anticone_size = self._calculate_anticone_size(block_id, parents)
        return anticone_size <= self.k

    def _find_selected_parent(self, parents):
        if not parents:
            return None
        parent_ids = [p.parent_id if isinstance(p, Parent) else p for p in parents]
        return max(parent_ids, key=lambda p: self.block_scores.get(p, 0))  # Use blue_scores instead of block_work

    def _calculate_blue_score(self, block_id, parents):
        # Your existing implementation
        if not parents:
            return 0
        selected_parent = self._find_selected_parent(parents)
        if not selected_parent:
            return 0
        parent_score = self.block_scores.get(selected_parent, 0)
        blue_parent_count = len(
            [p for p in parents if (p.parent_id if isinstance(p, Parent) else p) in self.blue_blocks])
        return parent_score + blue_parent_count

    def _calculate_anticone_size(self, block_id, parents):
        # Your existing implementation
        anticone_count = 0
        parent_ids = [p.parent_id if isinstance(p, Parent) else p for p in parents]

        for existing_block in self.blue_blocks:
            if existing_block not in parent_ids and not self._is_ancestor(existing_block, parent_ids):
                anticone_count += 1

        return anticone_count

    def _is_ancestor(self, block_id, potential_descendants):
        # Your existing implementation
        for desc in potential_descendants:
            if desc in self.blocks:
                desc_parents = self.blocks[desc]['parents']
                parent_ids = [p.parent_id if isinstance(p, Parent) else p for p in desc_parents]
                if block_id in parent_ids:
                    return True
        return False

    def rebalance_all_layers(self):
        """Manually trigger a full rebalancing of all layers"""
        animations = []
        for layer_index in range(len(self.layers)):
            animations.extend(self._adjust_single_layer(layer_index))
        return animations

WHITE = (255, 255, 255)