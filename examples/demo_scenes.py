# BlockAnimator\examples\demo_scenes.py

import math
from random import randint, choice
from numpy.random import poisson as poi

from blockanimator import *
from blockanimator.consensus import LogicalDAG
from blockanimator.consensus.dags import DAGFactory
from blockanimator.consensus.visual_block import VisualBlock
from blockanimator.rendering.consensus_scene_adapter import ConsensusSceneAdapter
from blockanimator.consensus.dags.ghostdag import GhostdagDAG
from blockanimator.rendering.visual_dag_renderer import VisualDAGRenderer
from blockanimator.consensus.dags.nakamoto_consensus.bitcoin_dag import BitcoinDAG
from blockanimator.animation import FadeInAnimation

# Stress Test with 50 blocks, multiple parents per block, movement, movement while color and opacity changes
# set Resolution and FPS to see how fast rendering is on your computer, mp4 output is 61 seconds.
# 240p, 480p, 720p, and 1080p can be selected, any FPS can be chosen.
class FiftyBlocksDemo(Scene):
    def __init__(self):
        super().__init__(resolution="240p", fps=8)

    def construct(self):
        BD = BlockDAG(self)

        # Calculate field dimensions
        aspect_ratio = self.width / self.height
        horizontal_field = 50 * aspect_ratio

        # Grid layout parameters
        start_x = 2
        start_y = 2
        grid_width = 10
        grid_height = 5

        available_width = horizontal_field - 4
        available_height = 50 - 4

        spacing_x = available_width / (grid_width - 1) if grid_width > 1 else 2
        spacing_y = available_height / (grid_height - 1) if grid_height > 1 else 2

        # Add 50 blocks using GhostdagBlock and store block objects
        block_objects = {}
        block_ids = []
        for i in range(50):
            row = i // 10
            col = i % 10
            x_pos = start_x + col * spacing_x
            y_pos = start_y + row * spacing_y

            block_id = f"Block_{i}"
            block_ids.append(block_id)

            # Create parent relationships - connect to previous block + skip every 2 blocks
            parents = []
            if i > 0:
                parent_id = f"Block_{i - 1}"
                parents.append(parent_id)

            skip_offset = 3
            connections_added = 1 if i > 0 else 0

            while connections_added < 10 and skip_offset <= i:
                parent_index = i - skip_offset
                if parent_index >= 0:
                    parent_id = f"Block_{parent_index}"
                    parents.append(parent_id)
                    connections_added += 1
                skip_offset += 3

            animations = BD.add(block_id, (x_pos, y_pos), label=f"{i}", parents=parents, consensus_type="ghostdag")
            if animations:
                self.play(animations)
            block_objects[block_id] = BD.blocks[block_id]  # Store block object

        self.wait(1)

        # Create circular movement animations using animate API
        move_animations = []
        center_x = horizontal_field / 2
        center_y = 25
        radius = min(horizontal_field, 50) * 0.50

        for i, block_id in enumerate(block_ids):
            angle = (i / 50) * 2 * math.pi
            new_x = center_x + radius * math.cos(angle)
            new_y = center_y + radius * math.sin(angle)

            move_animations.append(block_objects[block_id].animate.move_to((new_x, new_y), duration=3.0))

        self.play(*move_animations)
        self.wait(2)

        # Return to original positions with color changes using animate API
        return_animations = []
        for i, block_id in enumerate(block_ids):
            row = i // 10
            col = i % 10
            original_x = start_x + col * spacing_x
            original_y = start_y + row * spacing_y

            return_animations.append(block_objects[block_id].animate.move_to((original_x, original_y), duration=3.0))

            if i < 25:
                return_animations.append(block_objects[block_id].animate.change_color((0, 0, 255), duration=3.0))
                return_animations.append(block_objects[block_id].animate.fade_to(75, duration=3.0))
            else:
                return_animations.append(block_objects[block_id].animate.change_color((0, 255, 0), duration=3.0))

        self.play(*return_animations)
        self.wait(2)

class GhostDAGDemo(Scene):
    def __init__(self, resolution='480p', fps=15, **kwargs):  # Add resolution, fps, and **kwargs
        super().__init__(resolution=resolution, fps=fps, **kwargs)  # Pass them to super

    def construct(self):
        GD = GhostDAG(self, k=1)

        # Add blocks and store references
        gen_animations = GD.add("Genesis", (10, 25), label="G")
        self.play(gen_animations)
        genesis_block = GD.blocks["Genesis"]
        self.wait(1)

        a_animations = GD.add("A", (25, 25), parents=["Genesis"], label="A")
        self.play(a_animations)
        a_block = GD.blocks["A"]
        self.wait(1)

        b_animations = GD.add("B", (40, 25), parents=["A"], label="B")
        self.play(b_animations)
        b_block = GD.blocks["B"]
        self.wait(1)

        c_animations = GD.add("C", (55, 35), parents=["B"], label="C")
        self.play(c_animations)
        c_block = GD.blocks["C"]
        self.wait(1)

        d_animations = GD.add("D", (55, 15), parents=["B"], label="D")
        self.play(d_animations)
        d_block = GD.blocks["D"]
        self.wait(1)

        e_animations = GD.add("E", (70, 25),
                              parents=["C", StyledParent("D", color=(0, 255, 0))],
                              label="E")
        self.play(e_animations)
        e_block = GD.blocks["E"]
        self.wait(1)

        f_animations = GD.add("F", (85, 35), parents=["E"], label="F")
        self.play(f_animations)
        f_block = GD.blocks["F"]
        self.wait(1)

        g_animations = GD.add("G", (70, 40), parents=["C"], label="G")
        self.play(g_animations)
        g_block = GD.blocks["G"]
        self.wait(1)

        h_animations = GD.add("H", (85, 15),
                              parents=["D", "G", "F"],
                              label="H")
        self.play(h_animations)
        h_block = GD.blocks["H"]
        self.wait(2)

        # Show final state
        print("\nFinal GHOSTDAG State:")
        print(f"Blue blocks: {getattr(GD, 'blue_blocks', 'N/A')}")
        print(f"Red blocks: {getattr(GD, 'red_blocks', 'N/A')}")
        print(f"Block scores: {getattr(GD, 'block_scores', 'N/A')}")

class BlockCameraDemo(Scene):
    def construct(self):
        BD = BlockDAG(self)

        # Add blocks and store references to the block objects
        gen_block_animations = BD.add("Gen", (8, 25), label="G", consensus_type="bitcoin")
        self.play(gen_block_animations)
        gen_block = BD.blocks["Gen"]

        x_block_animations = BD.add("X", (30, 25), label="X", consensus_type="bitcoin")
        self.play(x_block_animations)
        x_block = BD.blocks["X"]

        y_block_animations = BD.add("Y", (45, 30), label=":)", consensus_type="bitcoin")
        self.play(y_block_animations)
        y_block = BD.blocks["Y"]

        # Animate camera movements to follow the blocks
        self.play(self.camera.animate_camera_to_sprite("X", duration=1.0))
        self.wait(1)

        self.play(self.camera.animate_camera_to_sprite("Y", duration=1.0))
        self.wait(1)

        # Move camera by relative offset
        self.play(self.camera.animate_camera_move(15, -13, duration=1.0))
        self.wait(1)

class AutoGhostDAGDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        AVG_AC = 4
        BLOCKS = 20
        MAX_BLOCKS_PER_BATCH = 3

        GD = GhostDAG(self, k=2)

        gen_animations = GD.add_with_ghostdag("Gen", label="G")
        self.play(gen_animations)

        blocks_remaining = BLOCKS - 1
        batch_number = 0

        while blocks_remaining > 0:
            batch_number += 1
            batch_size = min(randint(1, MAX_BLOCKS_PER_BATCH), blocks_remaining)
            blocks_remaining -= batch_size

            batch_animations = []
            for i in range(batch_size):
                block_id = f"L{batch_number}_{i + 1}"

                missed_blocks = poi(lam=AVG_AC)
                selected_parents = GD.get_tips(missed_blocks=missed_blocks)

                batch_animations.append(
                    GD.add_with_ghostdag(block_id, parents=selected_parents, label=f"{batch_number}.{i + 1}")
                )

            self.play(batch_animations)

            adjust_animations = GD.adjust_layers()
            if adjust_animations:
                self.play(adjust_animations)

        self.wait(2)
        final_animations = GD.create_final_ghostdag_animation()
        self.play(final_animations, run_time=5)

        self.wait(3)

class AutoLayerDAGDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        AVG_AC = 4
        BLOCKS = 20
        MAX_BLOCKS_PER_BATCH = 3
        GD_K = 2

        GD = GhostDAG(self, k=GD_K)

        gen_animations = GD.add_with_ghostdag("Gen", label="G")
        self.play(gen_animations)
        self.wait(0.5)

        adjust_animations = GD.adjust_layers()
        if adjust_animations:
            self.play(adjust_animations)

        blocks_remaining = BLOCKS - 1
        batch_number = 0

        while blocks_remaining > 0:
            batch_number += 1
            batch_size = min(randint(1, MAX_BLOCKS_PER_BATCH), blocks_remaining)
            blocks_remaining -= batch_size

            print(f"Batch {batch_number}: Adding {batch_size} blocks")

            current_tips = GD.get_tips()

            batch_animations = []
            for i in range(batch_size):
                block_id = f"L{batch_number}_{i + 1}"

                missed_blocks = poi(lam=AVG_AC)
                selected_parents = GD.get_tips(missed_blocks=missed_blocks)

                batch_animations.append(
                    GD.add_with_ghostdag(block_id, selected_parents, label=f"{batch_number}.{i + 1}")
                )

            self.play(batch_animations)
            self.wait(0.3)

            adjust_animations = GD.adjust_layers()
            if adjust_animations:
                self.play(adjust_animations)
                self.wait(0.2)

        self.wait(1)

        # Use animate API for color changes
        if hasattr(GD, 'blue_blocks') and GD.blue_blocks:
            blue_animations = [GD.blocks[block_id].animate.change_color((0, 100, 255))
                               for block_id in GD.blue_blocks if block_id in GD.blocks]
            self.play(blue_animations)
            self.wait(0.5)

        if hasattr(GD, 'red_blocks') and GD.red_blocks:
            red_animations = [GD.blocks[block_id].animate.change_color((255, 100, 100))
                              for block_id in GD.red_blocks if block_id in GD.blocks]
            self.play(red_animations)
            self.wait(0.5)

        final_adjust = GD.adjust_layers()
        if final_adjust:
            self.play(final_adjust)

        if hasattr(GD, 'create_tree_animation_fast'):
            print("Creating tree animations...")
            tree_animations = GD.create_tree_animation_fast()
            if tree_animations:
                print("Playing tree animations...")
                self.play(tree_animations, run_time=5.0)
                print("Tree animations complete")

        self.wait(3)

        print(f"\nFinal LayerDAG Statistics:")
        if hasattr(GD, 'blue_blocks'):
            print(f"Blue blocks: {len(GD.blue_blocks)}")
        if hasattr(GD, 'red_blocks'):
            print(f"Red blocks: {len(GD.red_blocks)}")
        if hasattr(GD, 'block_scores'):
            print(f"Block scores available: {len(GD.block_scores)}")

class BitcoinChainDemo(Scene):
    def __init__(self):
        super().__init__(resolution="720p", fps=30)

    def construct(self):
        # Create a BitcoinDAG instance
        BD = BitcoinDAG(self)

        # Add genesis block
        gen_animations = BD.add_bitcoin_block("Genesis", label="Genesis")
        self.play(gen_animations)
        self.wait(0.5)

        # Store block objects for animate API
        block_objects = {"Genesis": BD.blocks["Genesis"]}

        # Add a sequence of Bitcoin blocks, each extending the chain tip
        block_ids = ["Genesis"]
        for i in range(1, 8):
            parent = BD.get_chain_tip()
            block_id = f"Block_{i}"
            block_ids.append(block_id)

            # Add block with single parent (Bitcoin's linear chain rule)
            animations = BD.add_bitcoin_block(
                block_id,
                parent_id=parent,
                label=f"#{i}"
            )

            if animations:
                self.play(animations)
            self.wait(0.3)
            block_objects[block_id] = BD.blocks[block_id]  # Store block object

        # Validate chain integrity
        if BD.validate_chain_integrity():
            print("✓ Bitcoin chain integrity validated")

            # Show chain statistics
        print(f"Chain length: {BD.get_chain_length()}")
        print(f"Current tip: {BD.get_chain_tip()}")

        self.wait(1)

        # Highlight the entire chain with Bitcoin orange
        chain_highlight = BD.create_chain_animation(highlight_color=(255, 165, 0))
        if chain_highlight:
            self.play(chain_highlight)

        self.wait(1)

        # Demonstrate Bitcoin's single-parent constraint by trying to add an invalid block
        try:
            # This should fail because we're not extending the tip
            BD.add_bitcoin_block("Invalid", parent_id="Block_3", label="X")
        except ValueError as e:
            print(f"Expected error: {e}")

            # Move camera to follow the chain
        if len(block_ids) > 4:
            middle_block_id = block_ids[len(block_ids) // 2]
            camera_anim = self.camera.animate_camera_to_sprite(middle_block_id, duration=2.0)
            if camera_anim:
                self.play(camera_anim)

        self.wait(2)

        # Final animation: fade all blocks to show the linear structure using animate API
        fade_animations = []
        for block_id in block_ids:
            fade_animations.append(
                block_objects[block_id].animate.fade_to(150, duration=1.0)
            )

        self.play(*fade_animations)
        self.wait(1)

# working to separate blocks from visual representation, blocks and dags are getting too crowded
class BitcoinHiddenForkDemo(Scene):
    def __init__(self):
        super().__init__(resolution="720p", fps=30)

    def construct(self):
        # Phase 1: Create logical DAG with Bitcoin consensus
        logical_dag = LogicalDAG(consensus_type="bitcoin")

        # Create all logical blocks first (including hidden fork)
        # This separates consensus logic from visual rendering

        # Build main chain logically
        logical_dag.add_logical_block("Genesis")
        for i in range(1, 6):  # Blocks 1-5
            parent = "Genesis" if i == 1 else f"Block_{i - 1}"
            logical_dag.add_logical_block(f"Block_{i}", [parent])

            # Create hidden fork logically from Block_2
        fork_blocks = logical_dag.create_fork_from_point("Block_2", ["Fork_1", "Fork_2", "Fork_3"])

        # Validate logical structure
        if logical_dag.validate_dag_integrity():
            print("✓ Logical DAG integrity validated")

            # Phase 2: Visual rendering in creation order
        genesis_pos = (10, 25)
        block_spacing = 32  # 4 * 8 grid units

        # Render main chain blocks visually
        main_chain_blocks = ["Genesis", "Block_1", "Block_2", "Block_3", "Block_4", "Block_5"]
        visual_blocks = {}

        for i, block_id in enumerate(main_chain_blocks):
            logical_block = logical_dag.get_block(block_id)
            pos = (genesis_pos[0] + i * block_spacing, genesis_pos[1])

            # Create visual representation
            visual_block = VisualBlock(
                pos[0], pos[1],
                logical_block,
                self.coords.grid_size,
                color=(255, 165, 0)  # Bitcoin orange
            )

            visual_blocks[block_id] = visual_block
            self.sprite_registry[block_id] = visual_block
            self.sprites.add(visual_block, layer=self.BLOCK_LAYER)

            # Animate block appearance
            self.play(self.fade_to(block_id, 255, duration=0.5))
            self.wait(0.3)

            # Phase 3: Render hidden fork at 50% opacity
        hidden_animations = []

        for i, fork_block in enumerate(fork_blocks):
            logical_block = logical_dag.get_block(fork_block.block_id)
            # Position above main chain
            pos = (genesis_pos[0] + (i + 3) * block_spacing, genesis_pos[1] + 60)

            visual_block = VisualBlock(
                pos[0], pos[1],
                logical_block,
                self.coords.grid_size,
                color=(255, 165, 0)
            )

            visual_blocks[fork_block.block_id] = visual_block
            self.sprite_registry[fork_block.block_id] = visual_block
            self.sprites.add(visual_block, layer=self.BLOCK_LAYER)

            # Start hidden (50% opacity)
            hidden_animations.append(self.fade_to(fork_block.block_id, 127, duration=0.1))

        self.play(hidden_animations)
        self.wait(1)

        print(f"Main chain length: {logical_dag.get_chain_length()}")
        print(f"Current tip: {logical_dag.get_chain_tip()}")

        # Phase 4: Dramatic fork revelation and reorganization
        reveal_animations = []

        # Fade hidden fork to full opacity
        for fork_block in fork_blocks:
            reveal_animations.append(
                self.change_appearance(fork_block.block_id, target_alpha=255, duration=2.0)
            )

            # Move hidden fork to main chain position
        for i, fork_block in enumerate(fork_blocks):
            new_x = genesis_pos[0] + (i + 3) * block_spacing
            new_pos = (new_x, genesis_pos[1])
            reveal_animations.append(
                self.move_to(fork_block.block_id, new_pos, duration=2.0)
            )

            # Move orphaned honest blocks down
        orphaned_blocks = ["Block_3", "Block_4", "Block_5"]
        orphan_y = genesis_pos[1] - 60

        for block_id in orphaned_blocks:
            current_visual = visual_blocks[block_id]
            orphan_pos = (current_visual.x, orphan_y)
            reveal_animations.append(
                self.move_to(block_id, orphan_pos, duration=2.0)
            )
            # Fade to show orphaned status
            reveal_animations.append(
                self.change_appearance(block_id, target_alpha=128, target_color=(255, 100, 100), duration=2.0)
            )

            # Execute all reveal animations simultaneously
        self.play(reveal_animations)
        self.wait(2)

        # Phase 5: Update logical chain and highlight new main chain
        new_main_chain = ["Genesis", "Block_1", "Block_2", "Fork_1", "Fork_2", "Fork_3"]
        logical_dag.reorganize_chain(new_main_chain)

        # Highlight new main chain
        highlight_animations = []
        for block_id in new_main_chain:
            highlight_animations.append(
                self.change_appearance(block_id, target_color=(0, 255, 0), duration=1.0)
            )

        self.play(highlight_animations)
        self.wait(2)

        # Display final statistics
        stats = logical_dag.get_statistics()
        print(f"✓ Fork revealed! New main chain: {stats['chain_tip']}")
        print(f"✓ Chain length: {stats['chain_length']}")
        print(f"✗ Orphaned blocks: {orphaned_blocks}")

        self.wait(1)

# begin testing new abstracted blocks/dags
class NewConsensusDemo(Scene):
    def construct(self):
        # Test Bitcoin DAG
        bitcoin_dag = ConsensusSceneAdapter(self, "bitcoin")

        # Add some blocks
        genesis_anims = bitcoin_dag.add("Genesis", parents=None)
        self.play(genesis_anims)

        block_a_anims = bitcoin_dag.add("A", parents=["Genesis"])
        self.play(block_a_anims)

        self.wait(2)

# Testing new abstraction
class BitcoinChainTest(Scene):
    def construct(self):
        dag = ConsensusSceneAdapter(self, "bitcoin")

        genesis_anims = dag.add("Genesis", parents=None)
        self.play(genesis_anims)

        block_a_anims = dag.add("A", parents=["Genesis"])
        self.play(block_a_anims)

        block_b_anims = dag.add("B", parents=["A"])
        self.play(block_b_anims)

# Testing new abstraction
class GhostdagTest(Scene):
    def construct(self):
        dag = ConsensusSceneAdapter(self, "ghostdag", k=3)

        genesis_anims = dag.add("Genesis", parents=None)
        self.play(genesis_anims)

        # Multi-parent structure
        a_anims = dag.add("A", parents=["Genesis"])
        b_anims = dag.add("B", parents=["Genesis"])
        self.play(a_anims, b_anims)

        c_anims = dag.add("C", parents=["A", "B"])
        self.play(c_anims)

# Testing new abstraction
class ExtendedGhostdagDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        # Add 1 second wait before starting
        self.wait(1)

        # Create GHOSTDAG with k=3 parameter
        dag = ConsensusSceneAdapter(self, "ghostdag", k=3)

        # Genesis block
        genesis_anims = dag.add("Genesis", parents=None)
        self.play(genesis_anims)
        self.wait(0.5)

        # Layer 1: Two blocks from genesis
        a_anims = dag.add("A", parents=["Genesis"])
        b_anims = dag.add("B", parents=["Genesis"])
        self.play(a_anims)
        self.wait(0.3)
        self.play(b_anims)
        self.wait(0.5)

        # Layer 2: Multi-parent blocks
        c_anims = dag.add("C", parents=["A", "B"])  # Merge A and B
        self.play(c_anims)
        self.wait(0.3)

        d_anims = dag.add("D", parents=["A"])  # Single parent from A
        e_anims = dag.add("E", parents=["B"])  # Single parent from B
        self.play(d_anims)
        self.wait(0.2)
        self.play(e_anims)
        self.wait(0.5)

        # Layer 3: More complex relationships
        f_anims = dag.add("F", parents=["C", "D"])  # Multi-parent
        g_anims = dag.add("G", parents=["C", "E"])  # Multi-parent
        h_anims = dag.add("H", parents=["D", "E"])  # Multi-parent
        self.play(f_anims)
        self.wait(0.2)
        self.play(g_anims)
        self.wait(0.2)
        self.play(h_anims)
        self.wait(0.5)

        # Layer 4: Single and multi-parent mix
        i_anims = dag.add("I", parents=["F"])
        j_anims = dag.add("J", parents=["G", "H"])
        k_anims = dag.add("K", parents=["F", "G", "H"])  # Three parents
        self.play(i_anims)
        self.wait(0.2)
        self.play(j_anims)
        self.wait(0.2)
        self.play(k_anims)
        self.wait(0.5)

        # Layer 5: Testing layer adjustment with multiple blocks
        l_anims = dag.add("L", parents=["I", "J"])
        m_anims = dag.add("M", parents=["J", "K"])
        n_anims = dag.add("N", parents=["I", "K"])
        o_anims = dag.add("O", parents=["I"])  # Single parent
        self.play(l_anims)
        self.wait(0.2)
        self.play(m_anims)
        self.wait(0.2)
        self.play(n_anims)
        self.wait(0.2)
        self.play(o_anims)
        self.wait(0.5)

        # Layer 6: Final layer with complex merges
        p_anims = dag.add("P", parents=["L", "M", "N"])  # Three parents
        q_anims = dag.add("Q", parents=["M", "O"])
        r_anims = dag.add("R", parents=["N", "O"])
        s_anims = dag.add("S", parents=["L"])  # Single parent
        self.play(p_anims)
        self.wait(0.2)
        self.play(q_anims)
        self.wait(0.2)
        self.play(r_anims)
        self.wait(0.2)
        self.play(s_anims)
        self.wait(0.5)

        # Final tip blocks
        t_anims = dag.add("T", parents=["P", "Q", "R", "S"])  # Four parents - ultimate merge
        self.play(t_anims)
        self.wait(1)

        # Final pause to observe the complete DAG
        self.wait(3)

# Testing new abstraction with addition of layerdag
class GhostdagPoissonDemo(Scene):
    """Demonstrates GHOSTDAG with realistic network delays using Poisson distribution."""

    # Configuration constants
    AVG_NETWORK_DELAY = 3  # Average network delay (lambda for Poisson)
    TOTAL_BLOCKS = 25
    DAG_K_PARAMETER = 3
    MAX_BLOCKS_PER_BATCH = 3

    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        # Phase 1: Create logical DAG using new refactored system
        ghostdag = GhostdagDAG(k=self.DAG_K_PARAMETER, layer_spacing=15, chain_spacing=8)

        # Create visual renderer for the DAG
        renderer = VisualDAGRenderer(self, ghostdag)

        # Add genesis block - the renderer handles both logical and visual creation
        genesis_animations = renderer.add_visual_block("Genesis", parents=[])
        genesis_block = ghostdag.get_block("Genesis")
        print(f"Added Genesis block with blue score: {genesis_block.consensus_data.blue_score}")
        self.play(genesis_animations)

        # Create all logical blocks with network delay simulation
        blocks_remaining = self.TOTAL_BLOCKS
        batch_number = 0

        while blocks_remaining > 0:
            batch_number += 1
            batch_size = randint(1, min(self.MAX_BLOCKS_PER_BATCH, blocks_remaining))
            blocks_remaining -= batch_size

            print(f"\n--- Batch {batch_number}: Creating {batch_size} blocks ---")
            batch_animations = []

            # Create blocks in this batch
            for block_in_batch in range(batch_size):
                block_id = f"B{batch_number}_{block_in_batch}"

                # Simulate network delay with Poisson distribution
                network_delay = poi(lam=self.AVG_NETWORK_DELAY)

                # Get current tips (simplified - no history tracking in new system)
                current_tips = ghostdag.get_tips()

                # Simulate missed blocks by using a subset of tips
                if network_delay > 0 and len(current_tips) > network_delay:
                    # Simulate missing recent blocks by using older tips
                    available_tips = current_tips[:-network_delay] if network_delay < len(current_tips) else ["Genesis"]
                else:
                    available_tips = current_tips

                    # Select parents from available tips
                if len(available_tips) == 0:
                    parents = ["Genesis"]
                elif len(available_tips) == 1:
                    parents = available_tips
                else:
                    num_parents = randint(1, min(5, len(available_tips)))
                    parents = list(set(choice(available_tips) for _ in range(num_parents)))

                    # Use renderer to create both logical and visual block
                block_animations = renderer.add_visual_block(block_id, parents=parents)
                block = ghostdag.get_block(block_id)

                print(f"  Block {block_id}:")
                print(f"    Network delay: {network_delay} steps")
                print(f"    Parents: {parents}")
                print(f"    Selected parent: {block.consensus_data.selected_parent}")
                print(f"    Blue score: {block.consensus_data.blue_score}")
                print(f"    Mergeset blues: {block.consensus_data.mergeset_blues}")

                batch_animations.extend(block_animations)

                # Play all animations in this batch simultaneously
            if batch_animations:
                self.play(batch_animations)
                self.wait(0.5)  # Brief pause between batches

        # Phase 3: Final statistics and visual effects
        self._show_final_results(ghostdag)

    def _show_final_results(self, ghostdag):
        """Show final statistics and highlight the main chain."""
        stats = ghostdag.get_statistics()

        print(f"\n{'=' * 50}")
        print("FINAL GHOSTDAG STATISTICS")
        print(f"{'=' * 50}")
        print(f"Total blocks: {stats['total_blocks']}")
        print(f"K parameter: {stats['k_parameter']}")
        print(f"Current tips: {stats['tips']}")
        print(f"Blue blocks: {stats['blue_blocks']}")
        print(f"Red blocks: {stats['red_blocks']}")
        print(f"Max layer: {stats['max_layer']}")

        if stats.get('highest_scoring_block'):
            highest_block = stats['highest_scoring_block']
            print(f"Highest scoring block: {highest_block}")

            # Move camera to focus on the highest scoring block
            camera_anim = self.camera.animate_camera_to_sprite(highest_block)
            self.play(camera_anim)
            self.wait(1)

            # Get and highlight the selected parent chain
            chain = ghostdag.get_selected_parent_chain(highest_block)
            print(f"Selected parent chain: {' -> '.join(chain)}")

            # Show additional GHOSTDAG-specific information
            blue_blocks = ghostdag.get_blue_blocks()
            red_blocks = ghostdag.get_red_blocks()
            print(f"Blue blocks: {blue_blocks}")
            print(f"Red blocks: {red_blocks}")

            # Final wait before ending
        self.wait(1)

# Testing manim anim chaining
class TestManimLike(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        dag = BlockDAG(self)

        # Add a block
        block_anims = dag.add("test_block", (10, 25))
        self.wait(1)
        self.play(block_anims)

        # Get the block and use Manim-like syntax
        block = dag.blocks["test_block"]
        self.play(block.animate.moveX(10))
        self.wait(1)
        self.play(block.animate.shift((10, -10)))
        self.wait(1)


# Testing manim anim chaining with multiple blocks
class TestManimLikeWithMultiple(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        dag = BlockDAG(self)

        # Add first block
        block_anims = dag.add("test_block", (10, 25))
        self.wait(1)
        self.play(block_anims)

        # Add a second block with parent connection
        block2_anims = dag.add("block_2", (25, 25), parents=["test_block"])
        self.play(block2_anims)
        self.wait(1)

        # Add a third block
        block3_anims = dag.add("block_3", (10, 10))
        self.play(block3_anims)
        self.wait(1)

        # Get blocks and test individual movements
        block1 = dag.blocks["test_block"]
        block2 = dag.blocks["block_2"]
        block3 = dag.blocks["block_3"]

        # Test single block movement
        self.play(block1.animate.moveX(5))
        self.wait(1)

        # Test simultaneous movements of multiple blocks
        self.play(
            block1.animate.moveY(-5),
            block2.animate.shift((5, -5)),
            block3.animate.moveX(15)
        )
        self.wait(1)

        # Test chained movements on different blocks
        self.play(block1.animate.shift((10, -10)))
        self.wait(0.5)
        self.play(block2.animate.moveX(-10))
        self.wait(0.5)
        self.play(block3.animate.shift((-5, 10)))
        self.wait(1)

        # Test that connections follow blocks during movement
        self.play(
            block1.animate.shift((0, 15)),
            block2.animate.shift((0, 15))
        )
        self.wait(2)

# Testing for blanim like execution
class TestDAGChaining(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        dag = BlockDAG(self)

        # Create a method on the DAG that returns chained animations
        def create_chain_with_movement(dag, start_pos, chain_length=3):
            """Create a chain of blocks with automatic positioning and animations."""
            animations = []

            # Add genesis block
            genesis_anims = dag.add("genesis", start_pos)
            animations.extend(genesis_anims)

            # Add chain blocks with automatic spacing
            for i in range(1, chain_length + 1):
                block_id = f"block_{i}"
                parent_id = "genesis" if i == 1 else f"block_{i - 1}"

                # Position each block to the right of its parent
                pos = (start_pos[0] + i * 8, start_pos[1])
                block_anims = dag.add(block_id, pos, parents=[parent_id])
                animations.extend(block_anims)

            return animations

        def move_chain_in_formation(dag, block_ids, offset):
            """Move multiple blocks maintaining their relative positions."""
            animations = []
            for block_id in block_ids:
                if block_id in dag.blocks:
                    block = dag.blocks[block_id]
                    animations.append(block.animate.shift(offset))
            return animations

        def create_branching_structure(dag, root_id, branch_positions):
            """Create a branching structure from a root block."""
            animations = []
            for i, pos in enumerate(branch_positions):
                branch_id = f"{root_id}_branch_{i}"
                branch_anims = dag.add(branch_id, pos, parents=[root_id])
                animations.extend(branch_anims)
            return animations

            # Use the DAG methods to create complex animations

        # Step 1: Create initial chain
        chain_anims = create_chain_with_movement(dag, (10, 25), 3)
        self.play(chain_anims)
        self.wait(1)

        # Step 2: Move the entire chain as a unit
        chain_ids = ["genesis", "block_1", "block_2", "block_3"]
        formation_move = move_chain_in_formation(dag, chain_ids, (0, -10))
        self.play(formation_move)
        self.wait(1)

        # Step 3: Create branches from the middle block
        branch_positions = [(35, 10), (35, 30)]
        branch_anims = create_branching_structure(dag, "block_2", branch_positions)
        self.play(branch_anims)
        self.wait(1)

        # Step 4: Demonstrate individual block movements with deferred execution
        block_2 = dag.blocks["block_2"]
        branch_0 = dag.blocks["block_2_branch_0"]
        branch_1 = dag.blocks["block_2_branch_1"]

        # These movements will use the current animated positions
        self.play(
            block_2.animate.moveX(5),
            branch_0.animate.shift((10, 5)),
            branch_1.animate.shift((10, -5))
        )
        self.wait(1)

        # Step 5: Complex chained movement showing deferred execution
        self.play(block_2.animate.moveY(8))
        self.wait(0.5)

        # This will move from block_2's NEW position, not its original position
        self.play(
            branch_0.animate.shift((-5, 0)),
            branch_1.animate.shift((-5, 0))
        )
        self.wait(2)


# Example scene demonstrating the new Manim-like GHOSTDAG animation system
class GhostdagManimExample(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        # Create a GHOSTDAG with k=3 parameter
        ghostdag = GhostdagDAG(self, k=3)

        # Step 1: Add genesis block
        genesis_anims = ghostdag.add_ghostdag_block("genesis")
        self.play(genesis_anims)
        self.wait(1)

        # Step 2: Add first generation blocks with parents
        block_a_anims = ghostdag.add_ghostdag_block("A", parents=["genesis"])
        block_b_anims = ghostdag.add_ghostdag_block("B", parents=["genesis"])
        self.play(block_a_anims, block_b_anims)
        self.wait(1)

        # Step 3: Add second generation with multiple parents (GHOSTDAG feature)
        block_c_anims = ghostdag.add_ghostdag_block("C", parents=["A", "B"])
        self.play(block_c_anims)
        self.wait(1)

        # Step 4: Demonstrate individual block animation using new proxy system
        genesis = ghostdag.blocks["genesis"]
        block_a = ghostdag.blocks["A"]
        block_b = ghostdag.blocks["B"]
        block_c = ghostdag.blocks["C"]

        # Test deferred execution - these movements use current animated positions
        self.play(genesis.animate.moveX(5))
        self.wait(0.5)

        # This moveX will be relative to genesis's NEW position, not original
        self.play(genesis.animate.moveX(3))
        self.wait(1)

        # Step 5: Simultaneous multi-block animations with deferred execution
        self.play(
            block_a.animate.shift((5, -3)),
            block_b.animate.shift((5, 3)),
            block_c.animate.moveY(-5)
        )
        self.wait(1)

        # Step 6: Demonstrate GHOSTDAG-specific visualizations
        # Animate blue score visualization for all blocks
        blue_score_anims = []
        for block_id in ["genesis", "A", "B", "C"]:
            blue_score_anims.extend(ghostdag.animate_blue_score_visualization(block_id))

        self.play(blue_score_anims)
        self.wait(1)

        # Step 7: Animate the selected parent chain highlighting
        chain_anims = ghostdag.animate_selected_parent_chain("C")
        self.play(chain_anims)
        self.wait(1)

        # Step 8: Demonstrate mergeset visualization
        mergeset_anims = ghostdag.animate_mergeset_visualization("C")
        self.play(mergeset_anims)
        self.wait(1)

        # Step 9: Create a more complex DAG structure
        block_d_anims = ghostdag.add_ghostdag_block("D", parents=["A", "C"])
        block_e_anims = ghostdag.add_ghostdag_block("E", parents=["B", "C"])
        self.play(block_d_anims, block_e_anims)
        self.wait(1)

        # Step 10: Final GHOSTDAG result animation
        final_anims = ghostdag.animate_final_ghostdag_result()
        self.play(final_anims)
        self.wait(2)

        # Step 11: Demonstrate method chaining (Manim-like syntax)
        block_d = ghostdag.blocks["D"]
        block_e = ghostdag.blocks["E"]

        # Chain multiple animations together - each uses the result of the previous
        self.play(
            block_d.animate.shift((2, 0)).fade_to(200),
            block_e.animate.moveX(-3).change_color((255, 100, 100))
        )
        self.wait(1)

        # Step 12: Test that connections follow blocks during complex movements
        # Move all blocks in a coordinated pattern
        all_blocks = [ghostdag.blocks[bid] for bid in ghostdag.blocks.keys()]
        coordinated_anims = []

        for i, block in enumerate(all_blocks):
            # Create a circular movement pattern
            offset_x = 5 * (i % 3 - 1)  # -5, 0, 5 pattern
            offset_y = 3 * (i % 2)  # 0, 3 pattern
            coordinated_anims.append(block.animate.shift((offset_x, offset_y)))

        self.play(coordinated_anims)
        self.wait(2)

        # Step 13: Return to original positions using deferred execution
        reset_anims = []
        for block_id, block in ghostdag.blocks.items():
            # Each block moves back relative to its current position
            reset_anims.append(block.animate.shift((0, 0)))  # Or calculate return offset

        self.play(reset_anims)
        self.wait(1)

# Alternative example showing DAG-level animation methods
class GhostdagDAGMethodsExample(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        ghostdag = GhostdagDAG(self, k=3)

        # Add blocks individually instead of all at once
        block_sequence = ["genesis", "A", "B", "C", "D"]

        for block_id in block_sequence:
            parents = ghostdag._get_parents_for_block(block_id)
            block_anims = ghostdag.add_ghostdag_block(block_id, parents)
            self.play(block_anims)  # Play each block's animations individually
            self.wait(0.5)  # Optional pause between blocks

        self.wait(2)

        # Demonstrate the final result animation
        final_result = ghostdag.animate_final_ghostdag_result()
        self.play(final_result)
        self.wait(2)

# testing new manim like chaining
class ComprehensiveAnimationTest(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        dag = BlockDAG(self)

        # Test 1: Basic block creation and animation proxy access
        genesis_anims = dag.add("genesis", (10, 25))
        self.play(genesis_anims)
        self.wait(0.5)

        # Test 2: Simple method chaining (shift + fade_to)
        genesis = dag.blocks["genesis"]
        self.play(genesis.animate.shift((2, 0)).fade_to(200))
        self.wait(0.5)

        # Test 3: Multiple animation types in chain
        self.play(genesis.animate.moveX(3).change_color((255, 100, 100)).fade_to(255))
        self.wait(0.5)

        # Test 4: Deferred execution - movements relative to current position
        self.play(genesis.animate.moveY(-3))  # Move from current position
        self.wait(0.5)
        self.play(genesis.animate.moveY(2))  # Move from NEW position, not original
        self.wait(0.5)

        # Test 5: Multiple blocks with simultaneous chained animations
        block_a_anims = dag.add("block_a", (20, 20))
        block_b_anims = dag.add("block_b", (30, 30))
        self.play(block_a_anims, block_b_anims)
        self.wait(0.5)

        block_a = dag.blocks["block_a"]
        block_b = dag.blocks["block_b"]

        # Test 6: Simultaneous complex chaining on multiple blocks
        self.play(
            block_a.animate.shift((5, -5)).fade_to(150).change_color((0, 255, 0)),
            block_b.animate.moveX(-8).moveY(3).fade_to(180)
        )
        self.wait(0.5)

        # Test 7: Sequential chained animations to verify state persistence
        self.play(block_a.animate.moveX(2))
        self.play(block_a.animate.moveX(2))  # Should move from previous position
        self.play(block_a.animate.shift((0, -4)).fade_to(255))
        self.wait(0.5)

        # Test 8: Connection following during chained animations
        connected_anims = dag.add("connected", (35, 25), parents=["block_a"])
        self.play(connected_anims)
        self.wait(0.5)

        connected = dag.blocks["connected"]

        # Test 9: Verify connections follow during complex chained movements
        self.play(
            block_a.animate.shift((10, 10)).fade_to(200),
            connected.animate.shift((-5, 5)).change_color((0, 0, 255))
        )
        self.wait(1)

        # Test 10: Animation proxy reuse - verify pending_animations.clear() works
        self.play(genesis.animate.shift((0, 5)))
        self.wait(0.5)
        self.play(genesis.animate.moveX(-2))  # Should work without interference
        self.wait(0.5)

        # Test 11: Mixed animation types in single chain
        self.play(
            connected.animate
            .shift((2, -2))
            .fade_to(100)
            .change_color((255, 255, 0))
            .shift((1, 1))
            .fade_to(255)
        )
        self.wait(2)

class BlockDAGDemo(Scene):
    def construct(self):
        BD = BlockDAG(self)

        # Add blocks and store references to the block objects
        gen_block_animations = BD.add("Gen", (10, 25), label="G", consensus_type="ghostdag")
        self.play(gen_block_animations)
        gen_block = BD.blocks["Gen"]

        x_block_animations = BD.add("X", (25, 25), label="X", parents=["Gen"], consensus_type="ghostdag")
        self.play(x_block_animations)
        x_block = BD.blocks["X"]

        y_block_animations = BD.add("Y", (30, 35), label=":)",
                                    parents=["Gen", StyledParent("X", color=(0, 255, 0))],
                                    consensus_type="ghostdag")
        self.play(y_block_animations)
        y_block = BD.blocks["Y"]

        z_block_animations = BD.add("Z", (45, 25), label="Z", parents=["Y"], consensus_type="ghostdag")
        self.play(z_block_animations)
        z_block = BD.blocks["Z"]

        # Move blocks using the animate API
        new_y_pos = (35, 18)
        self.play(y_block.animate.move_to(new_y_pos, duration=2))

        self.wait(3)

class LayerDAGDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        LD = GhostDAG(self, k=3)

        # Add genesis block
        gen_animations = LD.add_with_ghostdag("Gen", label="G")
        self.play(gen_animations)
        gen_block = LD.blocks["Gen"]

        # Simultaneous animations (list)
        u_blocks = []
        u_animations = []
        for i in range(3):
            block_id = f"U{i}"
            anims = LD.add_with_ghostdag(block_id, ["Gen"], label=str(i))
            u_animations.extend(anims)
            u_blocks.append(LD.blocks[block_id])
        self.play(u_animations)

        # Sequential animations (list of lists)
        tips = LD.get_tips()
        w_blocks = []
        w_animations_group = []
        for i in range(5):
            block_id = f"W{i}"
            anims = LD.add_with_ghostdag(block_id, tips, label=f"W{i}")
            w_animations_group.extend(anims)
            w_blocks.append(LD.blocks[block_id])

        adjust_animations = LD.adjust_layers()

        self.play([w_animations_group, adjust_animations])

        # Use animate API for color changes
        color_changes = []
        for tip_id in tips:
            if tip_id in LD.blocks:  # Ensure block exists
                color_changes.append(LD.blocks[tip_id].animate.change_color((0, 255, 0)))
        self.play(color_changes)

        tips = LD.get_tips()
        color_changes = []
        for tip_id in tips:
            if tip_id in LD.blocks:  # Ensure block exists
                color_changes.append(LD.blocks[tip_id].animate.change_color((255, 0, 0)))
        self.play(color_changes)

        self.wait(2.0)

class SimultaneousVsSequentialDemo(Scene):
    def __init__(self):
        super().__init__(resolution='480p', fps=15)

    def construct(self):
        BD = BlockDAG(self)

        aspect_ratio = self.width / self.height
        field_width = 50 * aspect_ratio

        top_y = 50 - (50 / 3)
        bottom_y = 50 / 3

        spacing = field_width / 6
        x_positions = [spacing * (i + 1) for i in range(5)]

        # Create all blocks using the create() method
        top_block_objects = []
        bottom_block_objects = []

        for i in range(5):
            # Top row blocks
            top_block_id = f"top_block_{i + 1}"
            BD.create(
                top_block_id,
                (x_positions[i], top_y),
                label=f"T{i + 1}",
                color=(100, 150, 255)
            )
            top_block = BD.blocks[top_block_id]
            top_block_objects.append(top_block)

            # Bottom row blocks
            bottom_block_id = f"bottom_block_{i + 1}"
            BD.create(
                bottom_block_id,
                (x_positions[i], bottom_y),
                label=f"B{i + 1}",
                color=(255, 150, 100)
            )
            bottom_block = BD.blocks[bottom_block_id]
            bottom_block_objects.append(bottom_block)

        self.wait(1.0)

        # SIMULTANEOUS: Fade in all top blocks at once
        simultaneous_animations = [
            block.animate.fade_to(255, duration=1.5)
            for block in top_block_objects
        ]
        self.play(simultaneous(*simultaneous_animations))

        self.wait(2.0)

        # SEQUENTIAL: Fade in bottom blocks one after another
        sequential_animations = [
            [block.animate.fade_to(255, duration=0.8)]
            for block in bottom_block_objects
        ]
        self.play(sequential(*sequential_animations))

        self.wait(2.0)

# testing 95% refactoring
class BitcoinForkDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        # Use the visual BitcoinDAG directly, not the factory
        bitcoin_dag = BitcoinDAG(self)

        # Now this method exists
        self.play(bitcoin_dag.add_bitcoin_block("Genesis"))
        self.play(bitcoin_dag.add_bitcoin_block("Block1", "Genesis"))
        self.wait(1)

# testing 95% refactoring
class BitcoinForkDemo95(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        from blockanimator.consensus.dags import DAGFactory
        bitcoin_dag = DAGFactory.create_dag("bitcoin", scene=self)

        # Create initial chain
        self.play(bitcoin_dag.add_bitcoin_block("Genesis"))
        self.wait(0.5)

        self.play(bitcoin_dag.add_bitcoin_block("Block1", "Genesis"))
        self.wait(0.5)

        self.play(bitcoin_dag.add_bitcoin_block("Block2", "Block1"))
        self.wait(1)

        # Create fork blocks - reorganization happens automatically
        self.play(bitcoin_dag.add_bitcoin_block("Fork1", "Genesis"))
        self.wait(0.5)

        self.play(bitcoin_dag.add_bitcoin_block("Fork2", "Fork1"))
        self.wait(0.5)

        self.play(bitcoin_dag.add_bitcoin_block("Fork3", "Fork2"))
        self.wait(0.5)

        # This block makes the fork longer - automatic reorganization triggers
        self.play(bitcoin_dag.add_bitcoin_block("Fork4", "Fork3"))


class BitcoinBlockRaceDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        # Create the unified Bitcoin DAG
        from blockanimator.consensus.dags import DAGFactory
        bitcoin_dag = DAGFactory.create_dag("bitcoin", scene=self)

        # Phase 1: Build initial chain
        self.play(bitcoin_dag.add_bitcoin_block("Genesis"))
        self.wait(0.5)

        self.play(bitcoin_dag.add_bitcoin_block("Block1", "Genesis"))
        self.wait(0.5)

        self.play(bitcoin_dag.add_bitcoin_block("Block2", "Block1"))
        self.wait(1)

        # Phase 2: Start the race - two miners find blocks simultaneously
        # Miner A extends the main chain
        self.play(bitcoin_dag.add_bitcoin_block("Block3A", "Block2"))
        self.wait(0.3)

        # Miner B creates a competing fork from Block2
        self.play(bitcoin_dag.add_bitcoin_block("Block3B", "Block2"))
        self.wait(1)

        # Phase 3: The race continues - both sides add more blocks
        # Miner A adds another block (chain length = 4)
        self.play(bitcoin_dag.add_bitcoin_block("Block4A", "Block3A"))
        self.wait(0.5)

        # Miner B adds another block (chain length = 4, still tied)
        self.play(bitcoin_dag.add_bitcoin_block("Block4B", "Block3B"))
        self.wait(1)

        # Phase 4: The decisive moment - Miner B finds the next block first
        # This makes the B fork longer (5 blocks vs 4), triggering reorganization
        self.play(bitcoin_dag.add_bitcoin_block("Block5B", "Block4B"))
        self.wait(2)  # Allow time to see the reorganization

        # Phase 5: Show the final state with camera movement
        self.play(self.camera.animate_camera_to_sprite("Block5B"))
        self.wait(1)


class ZFirstTest(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        # Create basic DAG without Bitcoin-specific logic
        dag = BlockDAG(scene=self)

        # Define positioning constants
        genesis_y = 25
        fork_vertical_offset = 8
        half_offset = fork_vertical_offset / 2  # Half spacing for equal positioning

        # Genesis block
        genesis_anims = dag.add("Genesis", (10, genesis_y))
        self.play(genesis_anims)

        # Block1 extends Genesis
        block1_anims = dag.add("Block1", (20, genesis_y), parents=["Genesis"])
        self.play(block1_anims)

        # Create fork blocks with opacity 0 initially
        # Block2A (main chain) - starts at parent's Y position
        parent_y = dag.blocks["Block1"].grid_pos[1]
        block2a_anims = dag.create("Block2A", (30, parent_y), parents=["Block1"])
        dag.blocks["Block2A"].set_alpha(0)
        dag.blocks["Block2A"].set_visible(False)

        # Block2B (fork chain) - starts at offset below Block2A's position
        block2b_initial_y = parent_y - fork_vertical_offset
        block2b_anims = dag.create("Block2B", (30, block2b_initial_y), parents=["Block1"])
        dag.blocks["Block2B"].set_alpha(0)
        dag.blocks["Block2B"].set_visible(False)

        # Hide connections initially
        for sprite_id in ["Block1_to_Block2A", "Block1_to_Block2B"]:
            if sprite_id in dag.sprite_registry:
                dag.sprite_registry[sprite_id].set_alpha(0)
                dag.sprite_registry[sprite_id].set_visible(False)

                # Reveal Block2A
        dag.blocks["Block2A"].set_visible(True)
        dag.sprite_registry["Block1_to_Block2A"].set_visible(True)
        fade_2a = FadeInAnimation(sprite_id="Block2A", duration=1.0)
        conn_2a = FadeInAnimation(sprite_id="Block1_to_Block2A", duration=1.0)
        self.play([fade_2a, conn_2a])

        # Reveal Block2B and trigger equal-length positioning with both moving up
        dag.blocks["Block2B"].set_visible(True)
        dag.sprite_registry["Block1_to_Block2B"].set_visible(True)
        fade_2b = FadeInAnimation(sprite_id="Block2B", duration=1.0)
        conn_2b = FadeInAnimation(sprite_id="Block1_to_Block2B", duration=1.0)

        # Equal length positioning: both chains move to half offset positions (both moving up)
        move_2a_equal = dag.move_to("Block2A", (30, genesis_y + half_offset), duration=2.0)
        move_2b_equal = dag.move_to("Block2B", (30, genesis_y - half_offset), duration=2.0)

        # Play fade-in and movement simultaneously
        self.play([fade_2b, conn_2b, move_2a_equal, move_2b_equal])

        # NOW create Block3A at Block2A's CURRENT position (after it moved)
        block2a_current_y = genesis_y + half_offset  # Block2A's position after equal-length positioning
        block3a_anims = dag.create("Block3A", (40, block2a_current_y), parents=["Block2A"])
        dag.blocks["Block3A"].set_alpha(0)
        dag.blocks["Block3A"].set_visible(False)

        # Hide Block3A's connection initially
        if "Block2A_to_Block3A" in dag.sprite_registry:
            dag.sprite_registry["Block2A_to_Block3A"].set_alpha(0)
            dag.sprite_registry["Block2A_to_Block3A"].set_visible(False)

            # Reveal Block3A (makes main chain longer) - it fades in at its parent's current Y
        dag.blocks["Block3A"].set_visible(True)
        dag.sprite_registry["Block2A_to_Block3A"].set_visible(True)
        fade_3a = FadeInAnimation(sprite_id="Block3A", duration=1.0)
        conn_3a = FadeInAnimation(sprite_id="Block2A_to_Block3A", duration=1.0)

        # Fork reorganization: longer chain moves to genesis Y, shorter chain moves to full offset
        move_2a_reorg = dag.move_to("Block2A", (30, genesis_y), duration=2.0)
        move_3a_reorg = dag.move_to("Block3A", (40, genesis_y), duration=2.0)
        move_2b_reorg = dag.move_to("Block2B", (30, genesis_y - fork_vertical_offset), duration=2.0)

        # Add delay to reorganization animations
        move_2a_reorg.delay = 1.0
        move_3a_reorg.delay = 1.0
        move_2b_reorg.delay = 1.0

        self.play([fade_3a, conn_3a, move_2a_reorg, move_3a_reorg, move_2b_reorg])

        self.wait(2)


class ZWorking(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        # Create basic DAG without Bitcoin-specific logic
        dag = BlockDAG(scene=self)

        # Define positioning constants
        genesis_y = 25
        fork_vertical_offset = 8
        half_offset = fork_vertical_offset / 2  # Half spacing for equal positioning

        # Genesis block
        genesis_anims = dag.add("Genesis", (10, genesis_y))
        self.play(genesis_anims)

        # Block1 extends Genesis
        block1_anims = dag.add("Block1", (20, genesis_y), parents=["Genesis"])
        self.play(block1_anims)

        # Create initial fork blocks with opacity 0
        parent_y = dag.blocks["Block1"].grid_pos[1]

        # Block2A (main chain) - starts at parent's Y position
        block2a_anims = dag.create("Block2A", (30, parent_y), parents=["Block1"])
        dag.blocks["Block2A"].set_alpha(0)
        dag.blocks["Block2A"].set_visible(False)

        # Block2B (fork chain) - starts at offset below Block2A's position
        block2b_initial_y = parent_y - fork_vertical_offset
        block2b_anims = dag.create("Block2B", (30, block2b_initial_y), parents=["Block1"])
        dag.blocks["Block2B"].set_alpha(0)
        dag.blocks["Block2B"].set_visible(False)

        # Hide connections initially
        for sprite_id in ["Block1_to_Block2A", "Block1_to_Block2B"]:
            if sprite_id in dag.sprite_registry:
                dag.sprite_registry[sprite_id].set_alpha(0)
                dag.sprite_registry[sprite_id].set_visible(False)

                # Reveal Block2A
        dag.blocks["Block2A"].set_visible(True)
        dag.sprite_registry["Block1_to_Block2A"].set_visible(True)
        fade_2a = FadeInAnimation(sprite_id="Block2A", duration=1.0)
        conn_2a = FadeInAnimation(sprite_id="Block1_to_Block2A", duration=1.0)
        self.play([fade_2a, conn_2a])

        # Reveal Block2B and trigger equal-length positioning
        dag.blocks["Block2B"].set_visible(True)
        dag.sprite_registry["Block1_to_Block2B"].set_visible(True)
        fade_2b = FadeInAnimation(sprite_id="Block2B", duration=1.0)
        conn_2b = FadeInAnimation(sprite_id="Block1_to_Block2B", duration=1.0)

        # Equal length positioning: both chains move to half offset positions
        move_2a_equal = dag.move_to("Block2A", (30, genesis_y + half_offset), duration=2.0)
        move_2b_equal = dag.move_to("Block2B", (30, genesis_y - half_offset), duration=2.0)

        self.play([fade_2b, conn_2b, move_2a_equal, move_2b_equal])

        # Create Block3A at Block2A's current position
        block2a_current_y = genesis_y + half_offset
        block3a_anims = dag.create("Block3A", (40, block2a_current_y), parents=["Block2A"])
        dag.blocks["Block3A"].set_alpha(0)
        dag.blocks["Block3A"].set_visible(False)

        # Create Block3B at Block2B's current position (extending the race)
        block2b_current_y = genesis_y - half_offset
        block3b_anims = dag.create("Block3B", (40, block2b_current_y), parents=["Block2B"])
        dag.blocks["Block3B"].set_alpha(0)
        dag.blocks["Block3B"].set_visible(False)

        # Hide connections
        for sprite_id in ["Block2A_to_Block3A", "Block2B_to_Block3B"]:
            if sprite_id in dag.sprite_registry:
                dag.sprite_registry[sprite_id].set_alpha(0)
                dag.sprite_registry[sprite_id].set_visible(False)

                # Reveal Block3A (chains still equal length)
        dag.blocks["Block3A"].set_visible(True)
        dag.sprite_registry["Block2A_to_Block3A"].set_visible(True)
        fade_3a = FadeInAnimation(sprite_id="Block3A", duration=1.0)
        conn_3a = FadeInAnimation(sprite_id="Block2A_to_Block3A", duration=1.0)
        self.play([fade_3a, conn_3a])

        # Reveal Block3B (still equal length - race continues)
        dag.blocks["Block3B"].set_visible(True)
        dag.sprite_registry["Block2B_to_Block3B"].set_visible(True)
        fade_3b = FadeInAnimation(sprite_id="Block3B", duration=1.0)
        conn_3b = FadeInAnimation(sprite_id="Block2B_to_Block3B", duration=1.0)
        self.play([fade_3b, conn_3b])

        # Create Block4A and Block4B to continue the race
        block4a_anims = dag.create("Block4A", (50, block2a_current_y), parents=["Block3A"])
        dag.blocks["Block4A"].set_alpha(0)
        dag.blocks["Block4A"].set_visible(False)

        block4b_anims = dag.create("Block4B", (50, block2b_current_y), parents=["Block3B"])
        dag.blocks["Block4B"].set_alpha(0)
        dag.blocks["Block4B"].set_visible(False)

        # Hide connections
        for sprite_id in ["Block3A_to_Block4A", "Block3B_to_Block4B"]:
            if sprite_id in dag.sprite_registry:
                dag.sprite_registry[sprite_id].set_alpha(0)
                dag.sprite_registry[sprite_id].set_visible(False)

                # Reveal Block4A
        dag.blocks["Block4A"].set_visible(True)
        dag.sprite_registry["Block3A_to_Block4A"].set_visible(True)
        fade_4a = FadeInAnimation(sprite_id="Block4A", duration=1.0)
        conn_4a = FadeInAnimation(sprite_id="Block3A_to_Block4A", duration=1.0)
        self.play([fade_4a, conn_4a])

        # Reveal Block4B (still equal)
        dag.blocks["Block4B"].set_visible(True)
        dag.sprite_registry["Block3B_to_Block4B"].set_visible(True)
        fade_4b = FadeInAnimation(sprite_id="Block4B", duration=1.0)
        conn_4b = FadeInAnimation(sprite_id="Block3B_to_Block4B", duration=1.0)
        self.play([fade_4b, conn_4b])

        # Create Block5A to finally break the tie (main chain wins the race)
        block5a_anims = dag.create("Block5A", (60, block2a_current_y), parents=["Block4A"])
        dag.blocks["Block5A"].set_alpha(0)
        dag.blocks["Block5A"].set_visible(False)

        if "Block4A_to_Block5A" in dag.sprite_registry:
            dag.sprite_registry["Block4A_to_Block5A"].set_alpha(0)
            dag.sprite_registry["Block4A_to_Block5A"].set_visible(False)

            # Reveal Block5A (main chain becomes longer - race ends)
        dag.blocks["Block5A"].set_visible(True)
        dag.sprite_registry["Block4A_to_Block5A"].set_visible(True)
        fade_5a = FadeInAnimation(sprite_id="Block5A", duration=1.0)
        conn_5a = FadeInAnimation(sprite_id="Block4A_to_Block5A", duration=1.0)

        # Fork reorganization: main chain (longer) moves to genesis Y, fork chain moves to full offset
        move_2a_reorg = dag.move_to("Block2A", (30, genesis_y), duration=2.0)
        move_3a_reorg = dag.move_to("Block3A", (40, genesis_y), duration=2.0)
        move_4a_reorg = dag.move_to("Block4A", (50, genesis_y), duration=2.0)
        move_5a_reorg = dag.move_to("Block5A", (60, genesis_y), duration=2.0)

        move_2b_reorg = dag.move_to("Block2B", (30, genesis_y - fork_vertical_offset), duration=2.0)
        move_3b_reorg = dag.move_to("Block3B", (40, genesis_y - fork_vertical_offset), duration=2.0)
        move_4b_reorg = dag.move_to("Block4B", (50, genesis_y - fork_vertical_offset), duration=2.0)

        # Add delay to reorganization animations
        reorg_animations = [move_2a_reorg, move_3a_reorg, move_4a_reorg, move_5a_reorg,
                            move_2b_reorg, move_3b_reorg, move_4b_reorg]
        for anim in reorg_animations:
            anim.delay = 1.0

        self.play([fade_5a, conn_5a] + reorg_animations)

        self.wait(2)

class Z(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        # Create basic DAG and fork manager
        dag = BlockDAG(scene=self)
        fork_manager = ForkPositionManager(dag)

        # Pre-create all blocks with opacity 0
        self._create_all_blocks(dag, fork_manager)

        # Register all block relationships
        fork_manager.register_block("Genesis")
        fork_manager.register_block("Block1", "Genesis")
        fork_manager.register_block("Block2A", "Block1")
        fork_manager.register_block("Block2B", "Block1")
        fork_manager.register_block("Block3A", "Block2A")
        fork_manager.register_block("Block3B", "Block2B")
        fork_manager.register_block("Block4A", "Block3A")
        fork_manager.register_block("Block4B", "Block3B")
        fork_manager.register_block("Block5A", "Block4A")

        # Reveal blocks one by one - positioning happens automatically
        genesis_anims = fork_manager.reveal_block("Genesis")
        self.play(genesis_anims)

        block1_anims = fork_manager.reveal_block("Block1")
        self.play(block1_anims)

        block2a_anims = fork_manager.reveal_block("Block2A")
        self.play(block2a_anims)

        # Fork positioning happens automatically when Block2B is revealed
        block2b_anims = fork_manager.reveal_block("Block2B")
        self.play(block2b_anims)

        # Continue the race
        block3a_anims = fork_manager.reveal_block("Block3A")
        self.play(block3a_anims)

        block3b_anims = fork_manager.reveal_block("Block3B")
        self.play(block3b_anims)

        block4a_anims = fork_manager.reveal_block("Block4A")
        self.play(block4a_anims)

        block4b_anims = fork_manager.reveal_block("Block4B")
        self.play(block4b_anims)

        # Block5A breaks the tie - automatic reorganization
        block5a_anims = fork_manager.reveal_block("Block5A")
        self.play(block5a_anims)

        self.wait(2)

    def _create_all_blocks(self, dag, fork_manager):
        """Pre-create all blocks with proper positioning"""
        genesis_y = fork_manager.genesis_y
        fork_offset = fork_manager.fork_offset

        # Create all blocks initially hidden
        dag.create("Genesis", (10, genesis_y))
        dag.create("Block1", (20, genesis_y), parents=["Genesis"])
        dag.create("Block2A", (30, genesis_y), parents=["Block1"])
        dag.create("Block2B", (30, genesis_y - fork_offset), parents=["Block1"])
        dag.create("Block3A", (40, genesis_y), parents=["Block2A"])
        dag.create("Block3B", (40, genesis_y - fork_offset), parents=["Block2B"])
        dag.create("Block4A", (50, genesis_y), parents=["Block3A"])
        dag.create("Block4B", (50, genesis_y - fork_offset), parents=["Block3B"])
        dag.create("Block5A", (60, genesis_y), parents=["Block4A"])

        # Hide all blocks and connections initially
        all_blocks = ["Genesis", "Block1", "Block2A", "Block2B", "Block3A", "Block3B", "Block4A", "Block4B", "Block5A"]
        for block_id in all_blocks:
            if block_id in dag.blocks:
                dag.blocks[block_id].set_alpha(0)
                dag.blocks[block_id].set_visible(False)

                # Hide all connections
        connections = [
            "Genesis_to_Block1", "Block1_to_Block2A", "Block1_to_Block2B",
            "Block2A_to_Block3A", "Block2B_to_Block3B", "Block3A_to_Block4A",
            "Block3B_to_Block4B", "Block4A_to_Block5A"
        ]
        for conn_id in connections:
            if conn_id in dag.sprite_registry:
                dag.sprite_registry[conn_id].set_alpha(0)
                dag.sprite_registry[conn_id].set_visible(False)

class ForkPositionManager:
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

            # Make connection visible
        parent_id = self.block_parents.get(block_id)
        if parent_id:
            conn_id = f"{parent_id}_to_{block_id}"
            if conn_id in self.dag.sprite_registry:
                self.dag.sprite_registry[conn_id].set_visible(True)

                # Calculate new positions for all blocks
        repositioning_animations = self._recalculate_all_positions()

        # Create fade-in animations
        fade_anims = [FadeInAnimation(sprite_id=block_id, duration=1.0)]
        if parent_id:
            conn_id = f"{parent_id}_to_{block_id}"
            if conn_id in self.dag.sprite_registry:
                fade_anims.append(FadeInAnimation(sprite_id=conn_id, duration=1.0))

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
            current_pos = self.dag.blocks[block_id].grid_pos
            new_pos = (current_pos[0], target_y)
            move_anim = self.dag.move_to(block_id, new_pos, duration=2.0)
            if move_anim:
                move_anim.delay = 0.0  # Remove delay for consistent pacing
                animations.append(move_anim)

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
            color_anim = self.dag.change_color(block_id, target_color, duration=2.0)
            if color_anim:
                color_anim.delay = 0.0  # Remove delay for consistent pacing
                animations.append(color_anim)

                # Color all children recursively
        children = self.block_children.get(block_id, [])
        for child_id in children:
            animations.extend(self._color_block_and_children(child_id, target_color))

        return animations

def create_dynamic_block_race(scene, race_length=5, fork_at_block=1):
    """
    Create a dynamic block race of any length

    Args:
        scene: The scene to add the race to
        race_length: Number of blocks in each competing chain
        fork_at_block: Which block number to fork at (1 = fork after Block1)
    """
    dag = BlockDAG(scene=scene)
    fork_manager = ForkPositionManager(dag)

    # Generate block structure
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
        parents = [parent_id] if parent_id else []
        dag.create(block_id, pos, parents=parents)

        # Hide block
        if block_id in dag.blocks:
            dag.blocks[block_id].set_alpha(0)
            dag.blocks[block_id].set_visible(False)

            # Register with fork manager
        fork_manager.register_block(block_id, parent_id)

        # Hide connections
        if parent_id:
            conn_id = f"{parent_id}_to_{block_id}"
            if conn_id in dag.sprite_registry:
                dag.sprite_registry[conn_id].set_alpha(0)
                dag.sprite_registry[conn_id].set_visible(False)

    return dag, fork_manager, blocks_to_reveal


class DynamicBlockRaceScene(Scene):
    def __init__(self, race_length=5):
        super().__init__(resolution="1080p", fps=60)
        self.race_length = race_length

    def construct(self):
        dag, fork_manager, reveal_sequence = create_dynamic_block_race(
            self, race_length=self.race_length
        )

        # Reveal blocks in sequence
        for block_id in reveal_sequence:
            animations = fork_manager.reveal_block(block_id)
            self.play(animations)

        self.wait(2)