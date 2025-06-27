from random import randint
from numpy.random import poisson as poi
from core.scene import Scene
from consensus.block_dag import *
from animation.groups import *

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
                                    parents=["Gen", Parent("X", color=(0, 255, 0))],
                                    consensus_type="ghostdag")
        self.play(y_block_animations)
        y_block = BD.blocks["Y"]

        z_block_animations = BD.add("Z", (45, 25), label="Z", parents=["Y"], consensus_type="ghostdag")
        self.play(z_block_animations)
        z_block = BD.blocks["Z"]

        # Move blocks using the new Manim-style animate API
        new_y_pos = (35, 18)
        self.play(y_block.animate.move_to(new_y_pos, duration=2))

        self.wait(3)

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

class FiftyBlocksDemo(Scene):
    def __init__(self):
        super().__init__(resolution="240p", fps=8)

    def construct(self):
        BD = BlockDAG(self)

        # Calculate field dimensions (same as before)
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
            import math
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

class GhostDAGDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

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
                              parents=["C", Parent("D", color=(0, 255, 0))],
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
        # Assuming GD has these attributes after add calls
        print(f"Blue blocks: {getattr(GD, 'blue_blocks', 'N/A')}")
        print(f"Red blocks: {getattr(GD, 'red_blocks', 'N/A')}")
        print(f"Block scores: {getattr(GD, 'block_scores', 'N/A')}")

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

        # Create all blocks using the new create() method
        top_block_objects = []
        bottom_block_objects = []

        for i in range(5):
            # Top row blocks
            top_block_id = f"top_block_{i + 1}"
            # Use BD.create() to create the block without automatic fade-in animations.
            # The block will be initialized with visible=False, alpha=0.
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
            # Use BD.create() to create the block without automatic fade-in animations.
            # The block will be initialized with visible=False, alpha=0.
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
        # The _handle_fade_in method in AnimationController will set visible=True and alpha=0
        # before starting the fade.
        simultaneous_animations = [
            block.animate.fade_to(255, duration=1.5)
            for block in top_block_objects
        ]
        self.play(simultaneous(*simultaneous_animations))

        self.wait(2.0)

        # SEQUENTIAL: Fade in bottom blocks one after another
        # The _handle_fade_in method in AnimationController will set visible=True and alpha=0
        # before starting the fade.
        sequential_animations = [
            [block.animate.fade_to(255, duration=0.8)]
            for block in bottom_block_objects
        ]
        self.play(sequential(*sequential_animations))

        self.wait(2.0)

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

if __name__ == "__main__":
    scene = BlockDAGDemo()
#    scene = BlockCameraDemo()
#    scene = BitcoinChainDemo()
#    scene = FiftyBlocksDemo()
#    scene = LayerDAGDemo()
#    scene = AutoLayerDAGDemo()
#    scene = GhostDAGDemo()
#    scene = SimultaneousVsSequentialDemo() # Currently does not work using new create method(trying to set visibility in animations)
#    scene = AutoGhostDAGDemo()
    scene.construct()
    scene.render()

# Ignore the additional labels for now, they have been used for debugging

# TODO there is a way to create a living package from a project to use the project as an import, but I was unable to
#      implement this successfully so far.