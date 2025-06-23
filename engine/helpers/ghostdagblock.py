from engine.sprites.block import Block

# In your GhostDAGBlock class
class GhostDAGBlock(Block):
    """Block that selects parent with highest weight (GHOST-DAG algorithm)"""
    DEFAULT_COLOR = (0, 0, 255)  # PURE_BLUE equivalent in RGB

    def __init__(self, name=None, DAG=None, parents=None, grid_pos=None, label=None, color=None, **kwargs):
        # Initialize blue_count BEFORE calling parent constructor
        self.blue_count = 0
        self.name = name if name is not None else str(id(self))
        self.DAG = DAG
        self.parents_data = parents or []  # Store parent data for later processing
        self.grid_pos = grid_pos
        self.label = label
        self.block_color = color if color is not None else self.DEFAULT_COLOR
        self.kwargs = kwargs  # Store additional kwargs for sprite creation

        # The actual sprite will be created by the BlockDAG.add method
        self.sprite = None  # Placeholder for the sprite object

        # GHOSTDAG specific data
        self.mergeset = set()
        self.mergeset_blues = []
        self.mergeset_reds = []
        self.blues_anticone_sizes = {}
        self.selected_parent = None  # Will be set after parents are processed

    def _initialize_visuals(self):
        """Initializes the visual sprite for the block."""
        # This method will be called by the BlockDAG.add method after the block object is created
        # and added to DAG.blocks.
        # It creates the sprite and handles parent connections.

        # Create the sprite using the DAG's scene
        self.sprite = self.DAG.scene.add_sprite(
            self.name, self.grid_pos[0], self.grid_pos[1],
            text=self.label or self.name,
            color=self.block_color,
            **self.kwargs
        )
        # Store reference to the sprite in the DAG's blocks dictionary
        self.DAG.blocks[self.name]['sprite'] = self.sprite

        # Process parents and create connections
        processed_parents = []
        for p_data in self.parents_data:
            parent_id = p_data.parent_id if isinstance(p_data, Parent) else p_data
            if parent_id in self.DAG.blocks:
                processed_parents.append(
                    self.DAG.blocks[parent_id]['block_obj'])  # Store reference to parent block object

                # Create connection animation
                connection_kwargs = {}
                if isinstance(p_data, Parent) and p_data.color:
                    connection_kwargs['color'] = p_data.color

                connection_id = f"{parent_id}_to_{self.name}"
                self.DAG.scene.add_connection(connection_id, parent_id, self.name, **connection_kwargs)
        self.parents = processed_parents  # Set the actual parent block objects

        # Each block type implements its own parent selection
        self.selected_parent = self._select_parent()

        # Handle genesis block case
        if not self.selected_parent and self.name != "Gen":  # Genesis is handled by BlockDAG.add directly
            self.mergeset = set()
            self.mergeset_blues = []
            self.mergeset_reds = []
            self.blues_anticone_sizes = {}
            # Genesis should have blue_count = 0, which is already set
            return

            # Now do GHOSTDAG calculations
        if self.name != "Gen":  # GHOSTDAG calculations only for non-genesis blocks
            self.mergeset = self._calculate_mergeset_proper()
            k = getattr(self.DAG, 'k_param', 3)
            self.mergeset_blues, self.mergeset_reds, self.blues_anticone_sizes = self._color_mergeset_blocks(
                self.mergeset, k
            )

            # Recalculate blue_count with proper GHOSTDAG data
            self.blue_count = self._calculate_blue_count()

            # Update the label
            self.sprite.set_text(str(self.blue_count))

class BlockDAG:
    # ... (existing __init__ and other methods) ...

    def add(self, block_id, grid_pos, label=None, parents=None, block_type=None, **kwargs):
        """Add a block at grid position with automatic parent connections."""
        grid_x, grid_y = grid_pos

        self._validate_new_block(block_id)

        # Determine the block type to use
        if block_type is None:
            block_type = self.block_type  # Use the default block_type set in BlockDAG __init__

        # Create the block object (e.g., GhostDAGBlock instance)
        # Pass parents as parents_data to the block's __init__
        block_obj = block_type(
            name=block_id,
            DAG=self,
            parents=parents,  # Pass raw parent data
            grid_pos=grid_pos,
            label=label,
            **kwargs
        )

        self.blocks[block_id] = {
            'grid_pos': (grid_x, grid_y),
            'block_obj': block_obj,  # Store the block object
            'parents': parents or []
        }

        # Store in scene for camera targeting
        self.scene._block_positions[block_id] = self.blocks[block_id]

        # Initialize the block's visual sprite and connections
        # This needs to happen AFTER the block_obj is added to self.blocks
        block_obj._initialize_visuals()

        # Create animations list - start with block fade-in
        animations = [{
            'type': 'fade_in',
            'sprite_id': block_id,
            'duration': 0.5  # Default duration
        }]

        # Add parent connection fade-in animations
        if parents:
            for parent_data in parents:
                parent_id = parent_data.parent_id if isinstance(parent_data, Parent) else parent_data
                connection_id = f"{parent_id}_to_{block_id}"
                if connection_id in self.scene.sprite_registry:  # Check if connection was added by _initialize_visuals
                    animations.append({
                        'type': 'fade_in',
                        'sprite_id': connection_id,
                        'duration': 0.5  # Default duration
                    })

        return animations

class GhostDAG(BlockDAG):
    def __init__(self, scene, k=18):
        super().__init__(scene)
        self.k = k  # GHOSTDAG security parameter
        self.blue_blocks = set()
        self.red_blocks = set()
        self.block_scores = {}  # blue_score for each block

    def add_with_ghostdag(self, block_id, grid_pos, parents=None, **kwargs):
        """Add block with GHOSTDAG coloring logic"""
        # Run GHOSTDAG algorithm to determine blue/red classification
        is_blue = self._check_blue_candidate(block_id, parents or [])

        # Set color based on classification
        color = (0, 100, 255) if is_blue else (255, 100, 0)  # Blue or red
        kwargs['color'] = color

        # Calculate and display blue score
        blue_score = self._calculate_blue_score(block_id, parents or [])
        kwargs['label'] = f"{kwargs.get('label', block_id)}\n({blue_score})"

        return super().add(block_id, grid_pos, parents=parents, **kwargs)
