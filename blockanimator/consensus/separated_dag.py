from blockanimator.consensus.logical_block import LogicalBitcoinBlock, LogicalBlock
from blockanimator.consensus.visual_block import VisualBlock


class SeparatedDAG:
    """DAG with clean logical/visual separation"""

    def __init__(self, scene):
        self.scene = scene
        self.logical_blocks = {}  # block_id -> LogicalBlock
        self.visual_blocks = {}  # block_id -> VisualBlock
        self.creation_order = []  # Ordered list for rendering

    def add_logical_block(self, block_id, parents=None, consensus_type="basic"):
        """Phase 1: Create logical block"""
        if consensus_type == "bitcoin":
            logical_block = LogicalBitcoinBlock(block_id, parents[0] if parents else None)
        else:
            logical_block = LogicalBlock(block_id, parents, consensus_type)

        logical_block.creation_order = len(self.creation_order)
        self.logical_blocks[block_id] = logical_block
        self.creation_order.append(block_id)

        # Calculate consensus data
        if consensus_type == "ghostdag":
            logical_block.calculate_consensus_data(self.algorithm, self.logical_blocks)

        return logical_block

    def render_block(self, block_id, position, **visual_kwargs):
        """Phase 2: Create visual representation"""
        if block_id not in self.logical_blocks:
            raise ValueError(f"Logical block {block_id} not found")

        logical_block = self.logical_blocks[block_id]
        visual_block = VisualBlock(
            position[0], position[1],
            logical_block,
            self.scene.coords.grid_size,
            **visual_kwargs
        )

        self.visual_blocks[block_id] = visual_block
        self.scene.sprite_registry[block_id] = visual_block
        return visual_block

    def render_blocks_in_creation_order(self, start_position, spacing):
        """Render all logical blocks in creation order"""
        animations = []
        for i, block_id in enumerate(self.creation_order):
            if block_id not in self.visual_blocks:
                pos = (start_position[0] + i * spacing, start_position[1])
                visual_block = self.render_block(block_id, pos)
                animations.append(self.scene.fade_in(block_id, duration=0.5))
        return animations