# BlockAnimator\examples\demo_scenes.py

import math
from random import randint
from numpy.random import poisson as poi

from blockanimator import *
from blockanimator.consensus import LogicalDAG
from blockanimator.consensus.visual_block import VisualBlock
from blockanimator.rendering.consensus_scene_adapter import ConsensusSceneAdapter


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
