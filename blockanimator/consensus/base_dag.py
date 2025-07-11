# BlockAnimator\blockanimator\consensus\base_dag.py

import pygame
from blockanimator.animation import FadeInAnimation, FadeToAnimation, MoveToAnimation, ColorChangeAnimation
from ..sprites.block import Block, GhostdagBlock, BitcoinBlock
from ..sprites.connection import Connection
from .dag_types import StyledParent
from .constants import LayerConstants, AnimationConstants

class BlockDAG:
    def __init__(self, scene, history_size=20):
        self.scene = scene
        self.blocks = {}
        self.history = []  # History of tip states
        self.history_size = history_size

        # Take over sprite management from scene
        self.sprite_registry = {}
        self.sprites = pygame.sprite.LayeredUpdates()

        self.CONNECTION_LAYER = LayerConstants.CONNECTION_LAYER
        self.SELECTED_CONNECTION_LAYER = LayerConstants.SELECTED_CONNECTION_LAYER
        self.BLOCK_LAYER = LayerConstants.BLOCK_LAYER

        # Store reference to block positions
        if not hasattr(scene, '_block_positions'):
            scene._block_positions = {}

            # Register this DAG with the scene
        scene.register_dag(self)

    def add_sprite(self, sprite_id, grid_x, grid_y, consensus_type="basic", **kwargs):
        """Add a sprite at grid coordinates with specified consensus type."""
        pixel_x, pixel_y = self.scene.coords.grid_to_pixel(grid_x, grid_y)
        text = kwargs.pop('text', sprite_id)
        parents = kwargs.pop('parents', None)

        # Block type factory moved from Scene
        block_types = {
            "basic": lambda: Block(pixel_x, pixel_y, sprite_id, self.scene.coords.grid_size, text, **kwargs),
            "ghostdag": lambda: GhostdagBlock(pixel_x, pixel_y, sprite_id, self.scene.coords.grid_size, text,
                                              parents=parents, **kwargs),
            "bitcoin": lambda: BitcoinBlock(pixel_x, pixel_y, sprite_id, self.scene.coords.grid_size, text,
                                            parent=parents[0] if parents else None, **kwargs)
        }

        if consensus_type not in block_types:
            raise ValueError(f"Unknown consensus type: {consensus_type}")

        sprite = block_types[consensus_type]()
        sprite.grid_x = grid_x
        sprite.grid_y = grid_y

        self.sprite_registry[sprite_id] = sprite
        self.sprites.add(sprite, layer=self.BLOCK_LAYER)
        return sprite

    def add_connection(self, connection_id, start_block_id, end_block_id, **kwargs):
        """Enhanced connection creation with GHOSTDAG awareness."""
        start_block = self.sprite_registry.get(start_block_id)
        end_block = self.sprite_registry.get(end_block_id)

        if not start_block or not end_block:
            return None

            # GHOSTDAG-aware connection logic
        if isinstance(end_block, GhostdagBlock):
            is_selected_parent = (start_block.sprite_id == end_block.ghostdag_data.selected_parent)
            is_blue_connection = self._is_blue_connection(start_block.sprite_id, end_block)

            if 'color' not in kwargs:
                if is_selected_parent:
                    kwargs['color'] = (0, 255, 0)  # Green for selected parent
                elif is_blue_connection:
                    kwargs['color'] = (0, 0, 255)  # Blue for blue blocks
                else:
                    kwargs['color'] = (255, 0, 0)  # Red for red blocks

            kwargs['selected_parent'] = is_selected_parent

        connection = Connection(start_block, end_block, sprite_id=connection_id, grid_size=self.scene.coords.grid_size,
                                **kwargs)
        start_block.alpha_observers.append(connection)
        self.sprite_registry[connection_id] = connection

        layer = self.SELECTED_CONNECTION_LAYER if kwargs.get('selected_parent', False) else self.CONNECTION_LAYER
        self.sprites.add(connection, layer=layer)
        return connection

    def _is_blue_connection(self, parent_id, child_block):
        """Helper method to determine if a connection represents a blue relationship"""
        if not hasattr(child_block, 'ghostdag_data') or not child_block.ghostdag_data.mergeset:
            return False

        k = getattr(child_block, 'ghostdag_k', 3)
        blue_boundary = min(k + 1, len(child_block.ghostdag_data.mergeset))
        return parent_id in child_block.ghostdag_data.mergeset[:blue_boundary]

    def add(self, block_id, grid_pos, label=None, parents=None, **kwargs):
        """Add a block at grid position with automatic parent connections."""
        grid_x, grid_y = grid_pos

        sprite = self.add_sprite(
            block_id, grid_x, grid_y,
            text=label or block_id,
            parents=parents,
            **kwargs
        )

        # Store the sprite FIRST
        self.blocks[block_id] = sprite

        # THEN set the grid_pos on the block object
        self.blocks[block_id].grid_pos = grid_pos

        # Store in scene for camera targeting
        self.scene._block_positions[block_id] = self.blocks[block_id].grid_pos

        # Create animations list - start with block fade-in
        animations = [FadeInAnimation(
            sprite_id=block_id,
            duration=1.0
        )]

        # Add parent connections that fade in simultaneously
        if parents:
            for parent in parents:
                parent_id = parent.parent_id if isinstance(parent, StyledParent) else parent
                if parent_id in self.blocks:
                    connection_id = f"{parent_id}_to_{block_id}"

                    # Create connection with custom properties
                    connection_kwargs = {}
                    if isinstance(parent, StyledParent):
                        if parent.color:
                            connection_kwargs['color'] = parent.color
                        if parent.selected_parent:
                            connection_kwargs['selected_parent'] = True

                            # Set color based on whether this is the selected parent
                    if (hasattr(sprite, 'ghostdag_data') and
                            sprite.ghostdag_data and
                            sprite.ghostdag_data.selected_parent == parent_id):
                        connection_kwargs['color'] = (0, 0, 255)  # Blue for selected parent
                    else:
                        # Only override color if not already set by Parent object
                        if 'color' not in connection_kwargs:
                            connection_kwargs['color'] = (255, 255, 255)  # White for other parents

                    self.add_connection(connection_id, block_id, parent_id, **connection_kwargs)

                    # Add connection fade-in animation
                    animations.append(FadeInAnimation(
                        sprite_id=connection_id
                    ))

                    # After successfully adding the block, update history
        self._update_history()

        return animations

        # Animation helper methods moved from Scene

    def create(self, block_id, grid_pos, label=None, parents=None, **kwargs):
        """Create a block and connections without any automatic animations."""
        grid_x, grid_y = grid_pos

        sprite = self.add_sprite(
            block_id, grid_x, grid_y,
            text=label or block_id,
            parents=parents,
            **kwargs
        )

        # Store the sprite
        self.blocks[block_id] = sprite
        self.blocks[block_id].grid_pos = grid_pos

        # Store in scene for camera targeting
        self.scene._block_positions[block_id] = self.blocks[block_id].grid_pos

        # Create parent connections WITHOUT fade-in animations
        if parents:
            for parent in parents:
                parent_id = parent.parent_id if isinstance(parent, StyledParent) else parent
                if parent_id in self.blocks:
                    connection_id = f"{parent_id}_to_{block_id}"

                    # Initialize connection_kwargs here
                    connection_kwargs = {}
                    if isinstance(parent, StyledParent):
                        if parent.color:
                            connection_kwargs['color'] = parent.color
                        if parent.selected_parent:
                            connection_kwargs['selected_parent'] = True

                            # Set color based on whether this is the selected parent (similar to add method)
                    if (hasattr(sprite, 'ghostdag_data') and
                            sprite.ghostdag_data and
                            sprite.ghostdag_data.selected_parent == parent_id):
                        connection_kwargs['color'] = (0, 0, 255)  # Blue for selected parent
                    else:
                        if 'color' not in connection_kwargs:
                            connection_kwargs['color'] = (255, 255, 255)  # White for other parents

                    self.add_connection(connection_id, block_id, parent_id, **connection_kwargs)
                    # Set connection to invisible initially
                    if connection_id in self.sprite_registry:
                        self.sprite_registry[connection_id].set_visible(False)

        self._update_history()
        return []

    def move_to(self, sprite_id, target_pos, duration=AnimationConstants.DEFAULT_DURATION):
        """Create movement animation using current sprite positions."""
        if sprite_id not in self.sprite_registry:
            return None

        target_x, target_y = target_pos
        return MoveToAnimation(sprite_id=sprite_id, target_grid_x=target_x, target_grid_y=target_y, duration=duration)

    def fade_to(self, sprite_id, target_alpha, duration=AnimationConstants.DEFAULT_DURATION):
        """Create opacity animation for a sprite."""
        if sprite_id not in self.sprite_registry:
            return None
        return FadeToAnimation(sprite_id=sprite_id, target_alpha=target_alpha, duration=duration)

    def change_color(self, sprite_id, target_color, duration=1.0):
        """Create color change animation for a sprite."""
        if sprite_id not in self.sprite_registry:
            return None
        return ColorChangeAnimation(sprite_id=sprite_id, target_color=target_color, duration=AnimationConstants.DEFAULT_DURATION)

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
            for other_id, other_block in self.blocks.items():
                if other_id != block_id:
                    if hasattr(other_block, 'parents') and other_block.parents:
                        parent_ids = [p.parent_id if isinstance(p, StyledParent) else p for p in other_block.parents]
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
        current_grid = block.grid_pos
        new_grid = (current_grid[0] + offset[0], current_grid[1] + offset[1])

        # Update tracking
        block.grid_pos = new_grid

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
            connection = self.add_connection(
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
