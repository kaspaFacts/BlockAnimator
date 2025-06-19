def create_ghostdag_step_by_step_animation(self, vertical_offset=0.5, horizontal_offset=1.25):
    """
    Create step-by-step GHOSTDAG animation showing the algorithm progression
    from genesis to the heaviest tip, highlighting what's being checked at each step.
    """
    best_tip = self._find_best_tip()
    if not best_tip:
        return []  # Return empty list of animations

    parent_chain = self._get_parent_chain(best_tip)

    # Start with everything faded
    self._fade_all_blocks()

    all_animations = []

    # Process each block in the parent chain from genesis to tip
    for i, current_block_name in enumerate(reversed(parent_chain)):  # Genesis first
        current_block_data = self.blocks[current_block_name]
        current_block_obj = current_block_data['block_obj']
        current_sprite = current_block_obj.sprite

        # Skip genesis (no GHOSTDAG calculation needed)
        if current_block_name == "Gen":
            # Just highlight genesis
            self.scene.play(self._highlight_block(current_block_name), duration=0.3)
            self.scene.wait(0.5)
            continue

            # Step 1: Highlight the current block being processed
        self.scene.play(self._highlight_block(current_block_name), duration=0.3)
        self.scene.wait(0.5)

        # Step 2: Show selected parent selection
        if current_block_obj.selected_parent:
            self.scene.play(self._highlight_selected_parent(current_block_obj), duration=0.5)
            self.scene.wait(0.5)

            # Step 3: Show mergeset calculation
        if hasattr(current_block_obj, 'mergeset') and current_block_obj.mergeset:
            self.scene.play(self._highlight_mergeset(current_block_obj), duration=0.5)
            self.scene.wait(0.5)

            # Step 4: Show blue/red coloring process and k-cluster checks
        if hasattr(current_block_obj, 'mergeset_blues') or hasattr(current_block_obj, 'mergeset_reds'):
            # Iterate through ordered mergeset to show individual coloring decisions
            ordered_mergeset = current_block_obj._topological_sort_mergeset(current_block_obj.mergeset)

            # Create a temporary GhostdagData to simulate the state as candidates are processed
            temp_new_block_data = type('GhostdagData', (), {
                'selected_parent': current_block_obj.selected_parent.name,
                'mergeset_blues': [current_block_obj.selected_parent.name],
                'mergeset_reds': [],
                'blues_anticone_sizes': {current_block_obj.selected_parent.name: 0}
            })()

            for candidate_name in ordered_mergeset:
                candidate_block_obj = self.blocks[candidate_name]['block_obj']

                # Highlight candidate and relevant blue blocks for k-cluster check
                self.scene.play(self._show_k_cluster_check(current_block_obj, candidate_name, temp_new_block_data),
                                duration=0.7)
                self.scene.wait(0.5)

                # Perform the actual coloring check
                coloring = current_block_obj._check_blue_candidate(temp_new_block_data, candidate_name, self.k_param)

                # Apply the color and update temp_new_block_data
                if coloring.state == ColoringState.BLUE:
                    self.scene.play(current_block_obj.sprite.animate.set_color(PURE_BLUE), duration=0.3)
                    temp_new_block_data.mergeset_blues.append(candidate_name)
                    temp_new_block_data.blues_anticone_sizes[candidate_name] = coloring.anticone_size
                    for blue_name, size in coloring.anticone_sizes.items():
                        temp_new_block_data.blues_anticone_sizes[blue_name] = size + 1
                else:
                    self.scene.play(current_block_obj.sprite.animate.set_color(PURE_RED), duration=0.3)
                    temp_new_block_data.mergeset_reds.append(candidate_name)

                self.scene.wait(0.3)  # Short pause after coloring

                # Reset colors of k-cluster check highlights
                self.scene.play(self._reset_k_cluster_highlights(current_block_obj, candidate_name), duration=0.3)
                self.scene.wait(0.2)

        self.scene.wait(0.5)  # Brief pause after all mergeset blocks are colored

    # Final positioning animation (if needed, this would be a separate scene.play call)
    # For this engine, movement animations are handled by BlockDAG.shift
    # You would call BlockDAG.shift for each block you want to move, and then scene.play()
    # For a "tree animation", you'd calculate new positions and then apply them.
    # This part is more complex as it involves moving multiple sprites simultaneously.
    # For simplicity, let's assume the layout is static for this step-by-step visualization.
    # If you need to animate the tree layout, you'd collect all move_to animations and play them together.

    # Example of final layout adjustment (if you want to move blocks to a "tree" layout at the end)
    new_positions = self._calculate_chain_tree_positions_ordered(parent_chain, vertical_offset, horizontal_offset)
    movement_animations = []
    for block_name, new_pos in new_positions.items():
        current_block_data = self.blocks[block_name]
        current_block_obj = current_block_data['block_obj']
        current_grid_pos = current_block_data['grid_pos']

        # Only move if position actually changes
        if (current_grid_pos[0] != new_pos[0] or current_grid_pos[1] != new_pos[1]):
            movement_animations.append(
                self.shift(block_name, (new_pos[0] - current_grid_pos[0], new_pos[1] - current_grid_pos[1]),
                           run_time=1.0))
            # Update the stored grid_pos in self.blocks
            self.blocks[block_name]['grid_pos'] = (new_pos[0], new_pos[1])

    if movement_animations:
        self.scene.play(movement_animations, duration=1.0)

    return all_animations  # This function now directly plays animations, so it returns the list for reference


def _fade_all_blocks(self):
    """Set all blocks and connections to low opacity initially"""
    animations = []
    for block_id, block_data in self.blocks.items():
        sprite = block_data['sprite']
        animations.append({
            'type': 'set_alpha',
            'sprite_id': block_id,
            'target_alpha': 51,  # 0.2 * 255
            'duration': 0.1
        })
        sprite.set_alpha(51)  # Set immediately for initial state
        sprite.set_visible(True)  # Ensure they are visible but faded

    for sprite_id, sprite in self.scene.sprite_registry.items():
        if isinstance(sprite, Connection):
            animations.append({
                'type': 'set_alpha',
                'sprite_id': sprite_id,
                'target_alpha': 51,
                'duration': 0.1
            })
            sprite.set_alpha(51)  # Set immediately for initial state
            sprite.set_visible(True)
    self.scene.play(animations, duration=0.1)  # Play all fade animations


def _highlight_block(self, block_id):
    """Highlight a specific block and its relevant incoming arrows"""
    animations = []

    # Highlight the block itself
    animations.append({
        'type': 'set_alpha',
        'sprite_id': block_id,
        'target_alpha': 255,  # Full opacity
        'duration': 0.1
    })
    animations.append({
        'type': 'color_change',
        'sprite_id': block_id,
        'to_color': YELLOW,
        'duration': 0.1
    })

    # Highlight incoming arrows (arrows pointing to this block)
    for other_block_id, other_block_data in self.blocks.items():
        # Check if this block is a parent of other_block_id
        if other_block_data['block_obj'].selected_parent and other_block_data[
            'block_obj'].selected_parent.name == block_id:
            connection_id = f"{block_id}_to_{other_block_id}"
            if connection_id in self.scene.sprite_registry:
                animations.append({
                    'type': 'set_alpha',
                    'sprite_id': connection_id,
                    'target_alpha': 255,
                    'duration': 0.1
                })
                # Also check for other parents
        for parent_data in other_block_data['parents']:
            parent_id = parent_data.parent_id if isinstance(parent_data, Parent) else parent_data
            if parent_id == block_id and parent_id != other_block_data['block_obj'].selected_parent.name:
                connection_id = f"{parent_id}_to_{other_block_id}"
                if connection_id in self.scene.sprite_registry:
                    animations.append({
                        'type': 'set_alpha',
                        'sprite_id': connection_id,
                        'target_alpha': 255,
                        'duration': 0.1
                    })

    return animations


def _highlight_selected_parent(self, current_block_obj):
    """Highlight the selected parent and show the selection process with arrows"""
    animations = []

    # Highlight all parents first (showing selection process)
    for parent_obj in current_block_obj.parents:
        parent_id = parent_obj.name
        animations.append({
            'type': 'color_change',
            'sprite_id': parent_id,
            'to_color': YELLOW,
            'duration': 0.3
        })
        animations.append({
            'type': 'set_alpha',
            'sprite_id': parent_id,
            'target_alpha': 255,
            'duration': 0.3
        })

        # Highlight arrows from current block to all parents
        connection_id = f"{parent_id}_to_{current_block_obj.name}"
        if connection_id in self.scene.sprite_registry:
            animations.append({
                'type': 'set_alpha',
                'sprite_id': connection_id,
                'target_alpha': 255,
                'duration': 0.3
            })
            animations.append({
                'type': 'color_change',
                'sprite_id': connection_id,
                'to_color': YELLOW,
                'duration': 0.3
            })

            # Then highlight the selected parent in blue
    if current_block_obj.selected_parent:
        selected_parent_id = current_block_obj.selected_parent.name
        animations.append({
            'type': 'color_change',
            'sprite_id': selected_parent_id,
            'to_color': PURE_BLUE,
            'duration': 0.3
        })

        # Highlight the arrow to selected parent with blue color
        connection_id = f"{selected_parent_id}_to_{current_block_obj.name}"
        if connection_id in self.scene.sprite_registry:
            animations.append({
                'type': 'color_change',
                'sprite_id': connection_id,
                'to_color': PURE_BLUE,
                'duration': 0.3
            })
            animations.append({
                'type': 'set_alpha',
                'sprite_id': connection_id,
                'target_alpha': 255,
                'duration': 0.3
            })

    return animations


def _highlight_mergeset(self, current_block_obj):
    """Highlight the mergeset blocks and their connecting arrows"""
    animations = []

    if hasattr(current_block_obj, 'mergeset'):
        for mergeset_block_name in current_block_obj.mergeset:
            if mergeset_block_name in self.blocks:
                mergeset_block_data = self.blocks[mergeset_block_name]
                mergeset_block_obj = mergeset_block_data['block_obj']

                animations.append({
                    'type': 'color_change',
                    'sprite_id': mergeset_block_name,
                    'to_color': ORANGE,
                    'duration': 0.3
                })
                animations.append({
                    'type': 'set_alpha',
                    'sprite_id': mergeset_block_name,
                    'target_alpha': 255,
                    'duration': 0.3
                })

                # Highlight arrows connecting mergeset blocks to the current block's parents
                # and arrows within the mergeset
                for parent_of_mergeset_block in mergeset_block_obj.parents:
                    connection_id = f"{parent_of_mergeset_block.name}_to_{mergeset_block_name}"
                    if connection_id in self.scene.sprite_registry:
                        animations.append({
                            'type': 'set_alpha',
                            'sprite_id': connection_id,
                            'target_alpha': 255,
                            'duration': 0.3
                        })
                        animations.append({
                            'type': 'color_change',
                            'sprite_id': connection_id,
                            'to_color': ORANGE,
                            'duration': 0.3
                        })

    return animations


def _show_coloring_process(self, current_block_obj):
    """Show the blue/red coloring process step by step (this is now handled within create_ghostdag_step_by_step_animation)"""
    # This function is now largely integrated into the main loop for step-by-step coloring
    # It will primarily handle the final color application after k-cluster checks
    animations = []

    # First show blue blocks with their arrows
    if hasattr(current_block_obj, 'mergeset_blues'):
        for blue_block_name in current_block_obj.mergeset_blues:
            if blue_block_name in self.blocks and blue_block_name != current_block_obj.selected_parent.name:
                blue_block_obj = self.blocks[blue_block_name]['block_obj']
                animations.append({
                    'type': 'color_change',
                    'sprite_id': blue_block_name,
                    'to_color': PURE_BLUE,
                    'duration': 0.3
                })
                animations.append({
                    'type': 'set_alpha',
                    'sprite_id': blue_block_name,
                    'target_alpha': 255,
                    'duration': 0.3
                })

                # Highlight arrows from blue blocks
                for parent_of_blue_block in blue_block_obj.parents:
                    connection_id = f"{parent_of_blue_block.name}_to_{blue_block_name}"
                    if connection_id in self.scene.sprite_registry:
                        animations.append({
                            'type': 'set_alpha',
                            'sprite_id': connection_id,
                            'target_alpha': 255,
                            'duration': 0.3
                        })
                        animations.append({
                            'type': 'color_change',
                            'sprite_id': connection_id,
                            'to_color': PURE_BLUE,
                            'duration': 0.3
                        })

                        # Then show red blocks with their arrows
    if hasattr(current_block_obj, 'mergeset_reds'):
        for red_block_name in current_block_obj.mergeset_reds:
            if red_block_name in self.blocks:
                red_block_obj = self.blocks[red_block_name]['block_obj']
                animations.append({
                    'type': 'color_change',
                    'sprite_id': red_block_name,
                    'to_color': PURE_RED,
                    'duration': 0.3
                })
                animations.append({
                    'type': 'set_alpha',
                    'sprite_id': red_block_name,
                    'target_alpha': 255,
                    'duration': 0.3
                })

                # Highlight arrows from red blocks with reduced opacity
                for parent_of_red_block in red_block_obj.parents:
                    connection_id = f"{parent_of_red_block.name}_to_{red_block_name}"
                    if connection_id in self.scene.sprite_registry:
                        animations.append({
                            'type': 'set_alpha',
                            'sprite_id': connection_id,
                            'target_alpha': 51,  # 0.2 opacity
                            'duration': 0.3
                        })
                        animations.append({
                            'type': 'color_change',
                            'sprite_id': connection_id,
                            'to_color': PURE_RED,
                            'duration': 0.3
                        })

    return animations


def _show_k_cluster_check(self, current_block_obj, candidate_block_name, temp_new_block_data):
    """Show the k-cluster validation process for a specific candidate with anticone arrows highlighted"""
    animations = []

    # Highlight the candidate being checked
    animations.append({
        'type': 'color_change',
        'sprite_id': candidate_block_name,
        'to_color': YELLOW,
        'duration': 0.1
    })
    animations.append({
        'type': 'set_alpha',
        'sprite_id': candidate_block_name,
        'target_alpha': 255,
        'duration': 0.1
    })

    # Iterate over blue blocks in the current temporary mergeset_blues
    # These are the "peers" that the candidate is checked against
    for peer_name in temp_new_block_data.mergeset_blues:
        if peer_name in self.blocks:
            peer_block_obj = self.blocks[peer_name]['block_obj']
            candidate_block_obj = self.blocks[candidate_block_name]['block_obj']

            # Check if this peer is in the anticone of the candidate
            # (i.e., neither is an ancestor of the other)
            if not (peer_block_obj._is_ancestor(peer_block_obj, candidate_block_obj) or
                    candidate_block_obj._is_ancestor(candidate_block_obj, peer_block_obj)):

                animations.append({
                    'type': 'color_change',
                    'sprite_id': peer_name,
                    'to_color': LIGHT_BLUE,  # Highlight anticone blue blocks
                    'duration': 0.1
                })
                animations.append({
                    'type': 'set_alpha',
                    'sprite_id': peer_name,
                    'target_alpha': 255,
                    'duration': 0.1
                })

                # Highlight arrows connecting these anticone blocks to their common ancestors
                # This is a conceptual highlight, as direct arrows between anticone blocks don't exist.
                # Instead, we highlight arrows from them to blocks in the selected parent chain.
                for parent_of_peer in peer_block_obj.parents:
                    connection_id = f"{parent_of_peer.name}_to_{peer_name}"
                    if connection_id in self.scene.sprite_registry:
                        animations.append({
                            'type': 'set_alpha',
                            'sprite_id': connection_id,
                            'target_alpha': 255,
                            'duration': 0.1
                        })
                        animations.append({
                            'type': 'color_change',
                            'sprite_id': connection_id,
                            'to_color': LIGHT_BLUE,
                            'duration': 0.1
                        })

    return animations


def _reset_k_cluster_highlights(self, current_block_obj, candidate_block_name):
    """Reset colors and opacities after a k-cluster check step."""
    animations = []

    # Reset candidate block color to its original state (or faded)
    animations.append({
        'type': 'color_change',
        'sprite_id': candidate_block_name,
        'to_color': self.blocks[candidate_block_name]['block_obj'].block_color,  # Original color
        'duration': 0.1
    })
    animations.append({
        'type': 'set_alpha',
        'sprite_id': candidate_block_name,
        'target_alpha': 51,  # Faded
        'duration': 0.1
    })

    # Reset colors and opacities of anticone blue blocks and their arrows
    temp_new_block_data = type('GhostdagData', (), {  # Recreate temp data for consistency
        'selected_parent': current_block_obj.selected_parent.name,
        'mergeset_blues': [current_block_obj.selected_parent.name],
        'mergeset_reds': [],
        'blues_anticone_sizes': {current_block_obj.selected_parent.name: 0}
    })()
    # This temp_new_block_data needs to reflect the state *before* the current candidate was processed
    # For a full reset, you might need to pass the state of mergeset_blues from before the check.
    # For simplicity here, we'll just iterate through all current blue blocks.

    for peer_name in temp_new_block_data.mergeset_blues:  # Iterate through currently blue blocks
        if peer_name in self.blocks:
            peer_block_obj = self.blocks[peer_name]['block_obj']
            candidate_block_obj = self.blocks[candidate_block_name]['block_obj']

            if not (peer_block_obj._is_ancestor(peer_block_obj, candidate_block_obj) or
                    candidate_block_obj._is_ancestor(candidate_block_obj, peer_block_obj)):

                animations.append({
                    'type': 'color_change',
                    'sprite_id': peer_name,
                    'to_color': PURE_BLUE,  # Reset to blue
                    'duration': 0.1
                })
                animations.append({
                    'type': 'set_alpha',
                    'sprite_id': peer_name,
                    'target_alpha': 51,  # Faded
                    'duration': 0.1
                })

                for parent_of_peer in peer_block_obj.parents:
                    connection_id = f"{parent_of_peer.name}_to_{peer_name}"
                    if connection_id in self.scene.sprite_registry:
                        animations.append({
                            'type': 'set_alpha',
                            'sprite_id': connection_id,
                            'target_alpha': 51,  # Faded
                            'duration': 0.1
                        })
                        animations.append({
                            'type': 'color_change',
                            'sprite_id': connection_id,
                            'to_color': WHITE,  # Reset to white
                            'duration': 0.1
                        })
    return animations