"""BlockDAG helper with grid coordinates."""


class BlockDAG:
    def __init__(self, scene):
        self.scene = scene
        self.blocks = {}
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

                    # Create connection with custom color if specified
                    connection_kwargs = {}
                    if isinstance(parent, Parent) and parent.color:
                        connection_kwargs['color'] = parent.color

                    connection = self.scene.add_connection(
                        connection_id, parent_id, block_id, **connection_kwargs
                    )

                    # Add connection fade-in animation
                    animations.append({
                        'type': 'fade_in',
                        'sprite_id': connection_id
                    })

        return animations

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

    def __init__(self, parent_id, color=None, width=2, **kwargs):
        self.parent_id = parent_id
        self.color = color
        self.width = width
        self.kwargs = kwargs

WHITE = (255, 255, 255)