# BlockAnimator\blockanimator\consensus\ghostdag_dag.py

from blockanimator.consensus.dags.layer_dag import LayerDAG
from .dag_types import StyledParent
from .constants import AnimationConstants
from blockanimator.animation import MoveToAnimation, ColorChangeAnimation, FadeToAnimation

class GhostDAG(LayerDAG):
    def __init__(self, scene, k=3, **kwargs):
        super().__init__(scene, **kwargs)
        self.k = k

    def add_with_ghostdag(self, block_id, parents: list = None, **kwargs):
        """Add block with GHOSTDAG logic using two-phase construction"""
        parents = parents or []

        # Extract parent IDs for GhostdagBlock
        parent_ids = [p.parent_id if isinstance(p, StyledParent) else p for p in parents]
        # Phase 1: Create block without GHOSTDAG calculation
        kwargs['consensus_type'] = 'ghostdag'
        kwargs['parents'] = parent_ids

        # Add block to DAG first
        result = super().add_with_layers(block_id, parents, **kwargs)

        # Phase 2: Calculate GHOSTDAG data after block is in self.blocks
        if block_id in self.blocks:
            self.blocks[block_id].calculate_ghostdag_data(self.k, self.blocks)

        return result

    def create_final_ghostdag_animation(self):
        """Create final animation showing GHOSTDAG results using GhostdagData"""
        highest_score_block = None
        highest_score = -1

        # Access ghostdag_data directly from GhostdagBlock objects
        for block_id, sprite in self.blocks.items():
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
            sprite = self.blocks[current]  # Direct access to GhostdagBlock
            if sprite.ghostdag_data.selected_parent:
                current = sprite.ghostdag_data.selected_parent
            else:
                break

                # Store original positions
        original_positions = {}
        for block_id in self.blocks:
            original_positions[block_id] = self.blocks[block_id].grid_pos

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

            # Phase 3: Position mergeset blocks aligned with chain block's selected parent
        mergeset_blocks = []

        for chain_block_id in chain_blocks:
            chain_sprite = self.blocks[chain_block_id]  # Direct access to GhostdagBlock
            all_mergeset = chain_sprite.ghostdag_data.mergeset

            # Skip the selected parent (first in mergeset_blues)
            for mergeset_block_id in all_mergeset[1:]:  # Skip selected parent
                if (mergeset_block_id in self.blocks and
                        mergeset_block_id not in chain_blocks and
                        mergeset_block_id != 'Gen'):

                    # Avoid duplicates
                    if not any(mb[0] == mergeset_block_id for mb in mergeset_blocks):
                        mergeset_sprite = self.blocks[mergeset_block_id]  # Direct access
                        mergeset_blocks.append((
                            mergeset_block_id,
                            chain_block_id,  # The chain block that contains this in its mergeset
                            mergeset_sprite.ghostdag_data.blue_score
                        ))

                        # Position mergeset blocks aligned with their chain block's selected parent
        mergeset_base_offset_y = AnimationConstants.MERGESET_BASE_OFFSET_Y
        block_spacing = AnimationConstants.BLOCK_SPACING

        # Group mergeset blocks by their chain block
        chain_mergeset_groups = {}
        for block_id, chain_block_id, score in mergeset_blocks:
            if chain_block_id not in chain_mergeset_groups:
                chain_mergeset_groups[chain_block_id] = []
            chain_mergeset_groups[chain_block_id].append((block_id, score))

            # Position each group aligned with chain block's selected parent
        animation_delay = 0.5
        for chain_block_id, group_blocks in chain_mergeset_groups.items():
            chain_sprite = self.blocks[chain_block_id]  # Direct access

            if chain_sprite.ghostdag_data.mergeset_blues and chain_sprite.ghostdag_data.mergeset_blues[
                0] in original_positions:
                selected_parent_id = chain_sprite.ghostdag_data.mergeset_blues[0]
                selected_parent_pos = original_positions[selected_parent_id]

                # Sort blocks in this group by score
                group_blocks.sort(key=lambda x: x[1])

                for i, (block_id, score) in enumerate(group_blocks):
                    # Position at selected parent's X, offset vertically
                    y_offset = mergeset_base_offset_y + (i * block_spacing)
                    new_pos = (selected_parent_pos[0], target_chain_y + y_offset)

                    animations.append(MoveToAnimation(
                        sprite_id=block_id,
                        target_grid_x=new_pos[0],
                        target_grid_y=new_pos[1],
                        duration=1.0,
                        delay=animation_delay
                    ))

                    animation_delay += 0.1

                    # Phase 4: Color the main chain blue
        for i, block_id in enumerate(chain_blocks):
            animations.append(ColorChangeAnimation(
                sprite_id=block_id,
                target_color=(50, 150, 255),
                duration=0.3,
                delay=2.0 + i * 0.1
            ))

            # Phase 5: Color mergeset blocks using separate blues/reds lists
        for i, (block_id, chain_block_id, _) in enumerate(mergeset_blocks):
            sprite = self.blocks[block_id]  # Direct access
            parent_sprite = self.blocks[chain_block_id]  # Direct access

            is_blue = self._is_block_blue_in_mergeset(block_id, parent_sprite)
            color = (100, 200, 255) if is_blue else (255, 100, 50)

            animations.append(ColorChangeAnimation(
                sprite_id=block_id,
                target_color=color,
                duration=0.3,
                delay=2.5 + i * 0.1
            ))

            # Collect all animated blocks
        animated_blocks = set(chain_blocks)
        for block_id, _, _ in mergeset_blocks:
            animated_blocks.add(block_id)

            # Phase 6: Fade out all non-animated blocks
        fade_out_delay = AnimationConstants.FADE_OUT_DELAY
        for block_id, block_sprite in self.blocks.items():
            if block_id not in animated_blocks:
                animations.append(FadeToAnimation(
                    sprite_id=block_id,
                    target_alpha=10,
                    duration=1.0,
                    delay=fade_out_delay
                ))

        return animations

    @staticmethod
    def _is_block_blue_in_mergeset(block_id, parent_block):
        """Helper to determine if a block is blue in parent's mergeset"""
        return block_id in parent_block.ghostdag_data.mergeset_blues