# BlockAnimator\blockanimator\rendering\visual_dag_renderer.py

from typing import List, Dict, Any
import pygame
from ..animation import Animation, FadeToAnimation, MoveToAnimation
from ..sprites.block import Block, GhostdagBlock, BitcoinBlock
from ..sprites.connection import Connection
from ..consensus.dags.consensus_dags import ConsensusDAG
from ..consensus.constants import LayerConstants


class VisualDAGRenderer:
    """Renders logical consensus DAGs as visual sprites and animations."""

    def __init__(self, scene, logical_dag: ConsensusDAG):
        self.scene = scene
        self.logical_dag = logical_dag

        # Visual sprite management (replacing old BlockDAG functionality)
        self.sprite_registry: Dict[str, Any] = {}
        self.sprites = pygame.sprite.LayeredUpdates()

        # Layer constants
        self.CONNECTION_LAYER = LayerConstants.CONNECTION_LAYER
        self.SELECTED_CONNECTION_LAYER = LayerConstants.SELECTED_CONNECTION_LAYER
        self.BLOCK_LAYER = LayerConstants.BLOCK_LAYER

        # Store reference to block positions for camera targeting
        if not hasattr(scene, '_block_positions'):
            scene._block_positions = {}

            # Register with scene
        scene.register_dag(self)

    def add_visual_block(self, block_id: str, **kwargs) -> List[Animation]:
        """Add a logical block and create corresponding visual representation."""

        # 1. Add logical block to the consensus DAG
        logical_block = self.logical_dag.add_logical_block(block_id, **kwargs)

        # 2. Calculate visual position using consensus-specific positioning
        grid_pos = self.logical_dag.calculate_block_position(logical_block)

        # 3. Create visual sprite based on consensus type
        visual_sprite = self._create_visual_sprite(logical_block, grid_pos)

        # 4. Store sprite and position
        self.sprite_registry[block_id] = visual_sprite
        self.sprites.add(visual_sprite, layer=self.BLOCK_LAYER)
        self.scene._block_positions[block_id] = grid_pos

        # 5. Create animations starting with block fade-in using FadeToAnimation
        animations = [FadeToAnimation(sprite_id=block_id, target_alpha=255, duration=1.0)]

        # 6. Create parent connections but don't animate them
        if logical_block.parents:
            self._create_parent_connections(logical_block)  # Creates connections but returns no animations

        # 7. Add layer adjustment animations if this is a GHOSTDAG
        if hasattr(logical_block, 'metadata') and 'affected_layers' in logical_block.metadata:
            adjustment_animations = self.logical_dag._adjust_layer_positions(
                logical_block.metadata['affected_layers']
            )
            animations.extend(adjustment_animations)

        return animations

    def _create_layer_adjustment_animations(self, affected_layers: set) -> List[Animation]:
        """Create repositioning animations for affected layers."""
        animations = []

        for layer in affected_layers:
            layer_blocks = [bid for bid in self.logical_dag.creation_order
                            if bid in self.logical_dag.logical_blocks and
                            self.logical_dag._calculate_topological_layer(
                                self.logical_dag.logical_blocks[bid]) == layer]

            if len(layer_blocks) <= 1:
                continue

                # Use the same X positioning as the DAG
            from ..consensus.constants import AnimationConstants
            base_x = 10.0 + (layer * AnimationConstants.BLOCK_SPACING)
            genesis_y = 25.0

            # Calculate total height needed and center around genesis
            total_height = (len(layer_blocks) - 1) * AnimationConstants.VERTICAL_BLOCK_SPACING
            start_y = genesis_y - (total_height / 2)

            for i, block_id in enumerate(layer_blocks):
                if block_id in self.sprite_registry:
                    new_y = start_y + (i * AnimationConstants.VERTICAL_BLOCK_SPACING)

                    animations.append(MoveToAnimation(
                        sprite_id=block_id,
                        target_grid_x=base_x,
                        target_grid_y=new_y,
                        duration=1.0
                    ))

        return animations

    def _create_visual_sprite(self, logical_block, grid_pos):
        """Create appropriate visual sprite based on consensus type."""
        grid_x, grid_y = grid_pos
        pixel_x, pixel_y = self.scene.coords.grid_to_pixel(grid_x, grid_y)

        # Get display text from logical block
        text = logical_block.get_display_info()

        # Create consensus-specific visual block
        if logical_block.consensus_type == "bitcoin":
            sprite = BitcoinBlock(
                pixel_x, pixel_y, logical_block.block_id,
                self.scene.coords.grid_size, text,
                parent=logical_block.parents[0] if logical_block.parents else None
            )
        elif logical_block.consensus_type == "ghostdag":
            sprite = GhostdagBlock(
                pixel_x, pixel_y, logical_block.block_id,
                self.scene.coords.grid_size, text,
                parents=logical_block.parents
            )
        else:
            # Default to basic block
            sprite = Block(
                pixel_x, pixel_y, logical_block.block_id,
                self.scene.coords.grid_size, text
            )

        sprite.grid_x = grid_x
        sprite.grid_y = grid_y
        return sprite

    def _create_parent_connections(self, logical_block) -> List[Animation]:
        """Create visual connections to parent blocks."""
        animations = []

        for parent_id in logical_block.parents:
            if parent_id in self.sprite_registry:
                connection_id = f"{logical_block.block_id}_to_{parent_id}"

                # Create connection with consensus-specific styling
                connection_kwargs = self._get_connection_style(logical_block, parent_id)

                # Create the connection but don't animate it directly
                connection = self._create_connection(
                    connection_id, logical_block.block_id, parent_id, **connection_kwargs
                )

                # Remove the FadeToAnimation - connections will follow block alpha automatically
                # No animation needed here since connections use observer pattern

        return animations

    def _get_connection_style(self, logical_block, parent_id) -> Dict[str, Any]:
        """Get consensus-specific connection styling."""
        kwargs = {}

        if logical_block.consensus_type == "ghostdag":
            # GHOSTDAG-specific connection coloring
            if hasattr(logical_block.consensus_data, 'selected_parent'):
                is_selected_parent = (parent_id == logical_block.consensus_data.selected_parent)
                if is_selected_parent:
                    kwargs['color'] = (0, 255, 0)  # Green for selected parent
                    kwargs['selected_parent'] = True
                else:
                    # Check if it's a blue connection
                    if hasattr(logical_block.consensus_data, 'mergeset_blues'):
                        if parent_id in logical_block.consensus_data.mergeset_blues:
                            kwargs['color'] = (0, 0, 255)  # Blue for blue blocks
                        else:
                            kwargs['color'] = (255, 0, 0)  # Red for red blocks
        else:
            # Default connection color
            kwargs['color'] = (255, 255, 255)  # White

        return kwargs

    def _create_connection(self, connection_id: str, start_block_id: str,
                           end_block_id: str, **kwargs) -> Connection:
        """Create a visual connection between two blocks."""
        start_block = self.sprite_registry.get(start_block_id)
        end_block = self.sprite_registry.get(end_block_id)

        if not start_block or not end_block:
            return None

        connection = Connection(
            start_block, end_block,
            sprite_id=connection_id,
            grid_size=self.scene.coords.grid_size,
            **kwargs
        )

        # Add to sprite registry and layer
        start_block.alpha_observers.append(connection)
        self.sprite_registry[connection_id] = connection

        layer = (self.SELECTED_CONNECTION_LAYER if kwargs.get('selected_parent', False)
                 else self.CONNECTION_LAYER)
        self.sprites.add(connection, layer=layer)

        return connection