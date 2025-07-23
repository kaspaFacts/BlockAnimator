# blockanimator/consensus/dags/nakamoto_consensus/bitcoin_dag.py

from typing import Dict, List, Optional, Tuple, Any
from ..base_dag import BlockDAG
from ...blocks.consensus_block import ConsensusBlock
from ...blocks.block_factory import ConsensusBlockFactory

class ForkPositionManager:
    """Manages dynamic fork positioning and visualization for Bitcoin DAG"""

    def __init__(self, dag, genesis_y=25, fork_offset=8):
        self.dag = dag
        self.genesis_y = genesis_y
        self.fork_offset = fork_offset
        self.half_offset = fork_offset / 2
        self.visible_blocks = set()
        self.block_parents = {}
        self.block_children = {}

    def register_block(self, block_id, parent_id=None):
        """Register a block with its parent relationship"""
        self.block_parents[block_id] = parent_id

        # Track children relationships
        if parent_id:
            if parent_id not in self.block_children:
                self.block_children[parent_id] = []
            self.block_children[parent_id].append(block_id)

    def reveal_block(self, block_id):
        """Reveal a block and trigger automatic repositioning"""
        # Make block visible
        if block_id in self.dag.blocks:
            self.dag.blocks[block_id].set_visible(True)
            self.visible_blocks.add(block_id)

            # Make connection visible (but don't animate it)
        parent_id = self.block_parents.get(block_id)
        if parent_id:
            conn_id = f"{parent_id}_to_{block_id}"
            if conn_id in self.dag.sprite_registry:
                self.dag.sprite_registry[conn_id].set_visible(True)

                # Calculate new positions for all blocks
        repositioning_animations = self._recalculate_all_positions()

        # Create fade-in animations ONLY for blocks (not connections)
        fade_anims = []
        if block_id in self.dag.blocks:
            fade_anims.append(self.dag.blocks[block_id].animate.fade_in(duration=1.0))

            # Remove the connection animation line - connections will follow automatically
        # when the block's alpha changes through the observer pattern

        return fade_anims + repositioning_animations

    def _recalculate_all_positions(self):
        """Recalculate positions and colors for all blocks based on current chain state"""
        chains = self._build_chains_from_structure()
        animations = []

        if len(chains) <= 1:
            # Single chain - all blocks at genesis Y and blue
            target_y = self.genesis_y
            target_color = (0, 0, 255)  # Blue
            for chain in chains:
                for block_id in chain:
                    if block_id in self.visible_blocks:
                        animations.extend(self._move_block_and_children(block_id, target_y))
                        animations.extend(self._color_block_and_children(block_id, target_color))
        else:
            # Multiple chains - apply fork positioning and coloring logic
            chain_lengths = [len([b for b in chain if b in self.visible_blocks]) for chain in chains]
            max_length = max(chain_lengths) if chain_lengths else 0

            for i, chain in enumerate(chains):
                visible_chain_blocks = [b for b in chain if b in self.visible_blocks]
                if not visible_chain_blocks:
                    continue

                chain_length = len(visible_chain_blocks)

                if chain_length == max_length:
                    if chain_lengths.count(max_length) > 1:
                        # Equal length chains - half offset positioning, both blue
                        target_y = self.genesis_y + (self.half_offset if i == 0 else -self.half_offset)
                        target_color = (0, 0, 255)  # Blue for equal chains
                    else:
                        # Longest chain goes to genesis, blue color
                        target_y = self.genesis_y
                        target_color = (0, 0, 255)  # Blue for longest chain
                else:
                    # Shorter chain gets full offset, red color
                    target_y = self.genesis_y - self.fork_offset
                    target_color = (255, 0, 0)  # Red for shorter chain

                for block_id in visible_chain_blocks:
                    animations.extend(self._move_block_and_children(block_id, target_y))
                    animations.extend(self._color_block_and_children(block_id, target_color))

        return animations

    def _build_chains_from_structure(self):
        """Build chains based on parent-child structure, not just visible blocks"""
        # Find blocks that have multiple children (fork points)
        fork_points = []
        for block_id, children in self.block_children.items():
            if len(children) > 1:
                fork_points.append(block_id)

        if not fork_points:
            # No forks - single chain
            return [list(self.visible_blocks)]

            # Build separate chains from each fork point
        chains = []
        for fork_point in fork_points:
            children = self.block_children[fork_point]
            for child in children:
                chain = self._build_chain_from_block(child)
                if chain:
                    chains.append(chain)

        return chains

    def _build_chain_from_block(self, start_block):
        """Build a chain starting from a specific block"""
        chain = [start_block]
        current = start_block

        # Follow the chain through children
        while True:
            children = self.block_children.get(current, [])
            if len(children) == 1:
                current = children[0]
                chain.append(current)
            else:
                break  # Multiple children or no children - end of chain

        return chain

    def _move_block_and_children(self, block_id, target_y):
        """Move a block and all its children (including invisible ones) to target Y"""
        animations = []

        # Move the block itself if it exists
        if block_id in self.dag.blocks:
            block = self.dag.blocks[block_id]
            current_pos = block.grid_pos
            new_pos = (current_pos[0], target_y)

            # Use the new animation system properly
            move_anim = block.animate.move_to(new_pos, duration=2.0)
            # Extract the pending animations and set delay
            for anim in move_anim.pending_animations:
                anim.delay = 0.0
            animations.extend(move_anim.pending_animations)

            # Move all children recursively
        children = self.block_children.get(block_id, [])
        for child_id in children:
            animations.extend(self._move_block_and_children(child_id, target_y))

        return animations

    def _color_block_and_children(self, block_id, target_color):
        """Color a block and all its children (including invisible ones)"""
        animations = []

        # Color the block itself if it exists
        if block_id in self.dag.blocks:
            block = self.dag.blocks[block_id]

            # Use the new animation system properly
            color_anim = block.animate.change_color(target_color, duration=2.0)
            # Extract the pending animations and set delay
            for anim in color_anim.pending_animations:
                anim.delay = 0.0
            animations.extend(color_anim.pending_animations)

            # Color all children recursively
        children = self.block_children.get(block_id, [])
        for child_id in children:
            animations.extend(self._color_block_and_children(child_id, target_color))

        return animations


class BitcoinDAG(BlockDAG):
    """Unified Bitcoin DAG that handles both consensus logic and visual rendering with integrated ForkPositionManager."""

    def __init__(self, consensus_type: str, scene=None, spacing_multiplier=2, **kwargs):
        # Extract scene from kwargs if not provided as positional arg
        if scene is None:
            scene = kwargs.pop('scene', None)

        super().__init__(scene, **kwargs)
        self.consensus_type = consensus_type
        self.spacing_multiplier = spacing_multiplier
        self.genesis_pos = (10, 25)
        self.fork_vertical_offset = 8

        # Bitcoin-specific tracking
        self.chain_blocks: List[str] = []
        self.logical_blocks: Dict[str, ConsensusBlock] = {}
        self.creation_order: List[str] = []

        # Integrated fork position manager
        self.fork_position_manager = ForkPositionManager(
            dag=self,
            genesis_y=self.genesis_pos[1],
            fork_offset=self.fork_vertical_offset
        )

    def add_bitcoin_block(self, block_id: str, parent_id: str = None, label: str = None, **kwargs):
        """Add a Bitcoin block with automatic reorganization detection using ForkPositionManager."""
        # Phase 1: Create logical block
        parents = [parent_id] if parent_id else []
        logical_block = ConsensusBlockFactory.create_block(
            self.consensus_type, block_id, parents, **kwargs
        )

        # Store logical block
        logical_block.creation_order = len(self.creation_order)
        self.logical_blocks[block_id] = logical_block
        self.creation_order.append(block_id)

        # Register with fork position manager
        self.fork_position_manager.register_block(block_id, parent_id)

        # Calculate consensus data
        logical_block.calculate_consensus_data(0, self.logical_blocks)

        # Phase 2: Calculate visual position
        is_fork_block = parent_id and parent_id != self.get_chain_tip()

        if is_fork_block:
            # Fork blocks: position below genesis initially
            position = self.calculate_block_position(logical_block)
            position = (position[0], self.genesis_pos[1] - self.fork_vertical_offset)
        else:
            # Regular blocks: use standard positioning initially
            position = self.calculate_block_position(logical_block)

            # Phase 3: Create visual representation (initially hidden)
        kwargs['consensus_type'] = 'bitcoin'
        animations = super().add(block_id, position, label=label or block_id,
                                 parents=parents, **kwargs)

        # Hide block initially for dynamic reveal
        if block_id in self.blocks:
            self.blocks[block_id].set_alpha(0)
            self.blocks[block_id].set_visible(False)

            # Hide connections initially
        if parent_id:
            conn_id = f"{parent_id}_to_{block_id}"
            if conn_id in self.sprite_registry:
                self.sprite_registry[conn_id].set_alpha(0)
                self.sprite_registry[conn_id].set_visible(False)

                # Phase 4: Handle chain tracking
        if not is_fork_block:
            self._update_chain_tracking(logical_block)

        return animations

    def reveal_block(self, block_id: str):
        """Reveal a block using the integrated ForkPositionManager"""
        return self.fork_position_manager.reveal_block(block_id)

    def create_dynamic_block_race(self, race_length=5, fork_at_block=1):
        """Create a dynamic block race structure"""
        blocks_to_create = []
        blocks_to_reveal = []

        # Genesis and initial chain
        blocks_to_create.append(("Genesis", None, (10, 25)))
        blocks_to_reveal.append("Genesis")

        # Blocks before fork
        for i in range(1, fork_at_block + 1):
            block_id = f"Block{i}"
            parent_id = f"Block{i - 1}" if i > 1 else "Genesis"
            pos = (10 + i * 10, 25)
            blocks_to_create.append((block_id, parent_id, pos))
            blocks_to_reveal.append(block_id)

            # Racing blocks
        fork_parent = f"Block{fork_at_block}"
        for i in range(race_length):
            block_num = fork_at_block + i + 1

            # Chain A block
            block_a_id = f"Block{block_num}A"
            parent_a = f"Block{block_num - 1}A" if i > 0 else fork_parent
            pos_a = (10 + block_num * 10, 25)
            blocks_to_create.append((block_a_id, parent_a, pos_a))
            blocks_to_reveal.append(block_a_id)

            # Chain B block
            block_b_id = f"Block{block_num}B"
            parent_b = f"Block{block_num - 1}B" if i > 0 else fork_parent
            pos_b = (10 + block_num * 10, 25 - 8)
            blocks_to_create.append((block_b_id, parent_b, pos_b))
            blocks_to_reveal.append(block_b_id)

            # Winner block (extends chain A)
        winner_id = f"Block{fork_at_block + race_length + 1}A"
        winner_parent = f"Block{fork_at_block + race_length}A"
        winner_pos = (10 + (fork_at_block + race_length + 1) * 10, 25)
        blocks_to_create.append((winner_id, winner_parent, winner_pos))
        blocks_to_reveal.append(winner_id)

        # Create all blocks
        for block_id, parent_id, pos in blocks_to_create:
            self.add_bitcoin_block(block_id, parent_id)

        return blocks_to_reveal

        # Enhanced selfish mining support

    def create_hidden_fork_blocks(self, fork_point_id, num_blocks=3, opacity=127):
        """Create hidden fork blocks for selfish mining demonstrations"""
        if fork_point_id not in self.blocks:
            raise ValueError(f"Fork point {fork_point_id} not found")

        hidden_fork_blocks = []
        hidden_animations = []

        for i in range(1, num_blocks + 1):
            fork_block_id = f"SelfishFork_{i}"
            parent_id = fork_point_id if i == 1 else f"SelfishFork_{i - 1}"

            # Add block using our enhanced system
            animations = self.add_bitcoin_block(fork_block_id, parent_id, label=f"SF{i}")
            hidden_fork_blocks.append(fork_block_id)

            # Set to reduced opacity for hidden state
            if fork_block_id in self.blocks:
                self.blocks[fork_block_id].set_alpha(opacity)
                self.blocks[fork_block_id].set_visible(True)

        return hidden_fork_blocks, hidden_animations

    def reveal_selfish_mining_attack(self, hidden_fork_blocks):
        """Reveal selfish mining attack using ForkPositionManager"""
        reveal_animations = []

        # Reveal all hidden fork blocks sequentially
        for block_id in hidden_fork_blocks:
            # Make blocks fully visible and add to fork manager's visible set
            if block_id in self.blocks:
                self.blocks[block_id].set_alpha(255)
                self.fork_position_manager.visible_blocks.add(block_id)

                # Make connections visible
                parent_id = self.fork_position_manager.block_parents.get(block_id)
                if parent_id:
                    conn_id = f"{parent_id}_to_{block_id}"
                    if conn_id in self.sprite_registry:
                        self.sprite_registry[conn_id].set_visible(True)
                        self.sprite_registry[conn_id].set_alpha(255)

                        # Trigger repositioning using fork manager logic
        repositioning_animations = self.fork_position_manager._recalculate_all_positions()
        reveal_animations.extend(repositioning_animations)

        return reveal_animations

        # Keep all existing utility methods from original implementation

    def calculate_block_position(self, block: ConsensusBlock) -> Tuple[float, float]:
        """Calculate position based on Bitcoin chain height."""
        if block.is_genesis():
            return self.genesis_pos

        height = getattr(block.consensus_data, 'height', 0)
        x = self.genesis_pos[0] + (height * self._calculate_block_spacing())
        y = self.genesis_pos[1]
        return (x, y)

    def _calculate_block_spacing(self):
        """Calculate spacing based on block size."""
        block_size_in_grid_units = 4
        return block_size_in_grid_units * self.spacing_multiplier

    def _update_chain_tracking(self, block: ConsensusBlock):
        """Update Bitcoin chain tracking."""
        if block.is_genesis():
            self.chain_blocks = [block.block_id]
        else:
            self.chain_blocks.append(block.block_id)

    def get_chain_tip(self) -> Optional[str]:
        """Get the current tip of the Bitcoin chain."""
        return self.chain_blocks[-1] if self.chain_blocks else None

    def get_tips(self) -> List[str]:
        """Get current tip blocks (only one for Bitcoin)."""
        tip = self.get_chain_tip()
        return [tip] if tip else []

    def get_chain_length(self) -> int:
        """Get the length of the Bitcoin chain."""
        return len(self.chain_blocks)

    def get_block_height(self, block_id: str) -> Optional[int]:
        """Get the height of a specific block."""
        try:
            return self.chain_blocks.index(block_id)
        except ValueError:
            return None

    def get_chain_from_genesis(self) -> List[str]:
        """Get the complete chain from genesis to tip."""
        return self.chain_blocks.copy()

    def validate_dag_integrity(self) -> bool:
        """Validate Bitcoin chain structure and consensus rules."""
        for block_id, block in self.logical_blocks.items():
            if not block.validate_parents(self.logical_blocks):
                return False
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get Bitcoin chain statistics."""
        stats = {
            "total_blocks": len(self.logical_blocks),
            "consensus_type": self.consensus_type,
            "chain_length": self.get_chain_length(),
            "chain_tip": self.get_chain_tip(),
            "tips": self.get_tips(),
        }

        if self.chain_blocks:
            stats.update({
                "genesis_block": self.chain_blocks[0] if self.chain_blocks else None,
            })

        return stats

    def get_block_count(self) -> int:
        """Get total number of blocks in the DAG."""
        return len(self.logical_blocks)

    def get_block(self, block_id: str) -> Optional[ConsensusBlock]:
        """Get a block by its ID."""
        return self.logical_blocks.get(block_id)

    def get_blocks_in_creation_order(self) -> List[ConsensusBlock]:
        """Get all blocks in the order they were created."""
        return [self.logical_blocks[block_id] for block_id in self.creation_order if block_id in self.logical_blocks]

    def get_blocks_in_chain_order(self) -> List[ConsensusBlock]:
        """Get blocks in chain order (genesis to tip)."""
        return [self.logical_blocks[block_id] for block_id in self.chain_blocks if block_id in self.logical_blocks]