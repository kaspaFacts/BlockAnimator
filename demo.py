# demo.py
from random import randint
from numpy.random import poisson as poi
from engine.scene import Scene, simultaneous, sequential
from engine.helpers.block_dag import *


class BlockDAGDemo(Scene):
    def construct(self):
        BD = BlockDAG(self)

        # Genesis block near bottom-left with margin
        self.play(BD.add("Gen", (10, 25), label="G", consensus_type="ghostdag"))

        # Block with single parent - space horizontally
        self.play(BD.add("X", (25, 25), label="X", parents=["Gen"], consensus_type="ghostdag"))

        # Block with multiple parents - position higher and to the right
        self.play(BD.add("Y", (30, 35), label=":)",
                         parents=["Gen", Parent("X", color=(0, 255, 0))],
                         consensus_type="ghostdag"))

        # Block with single parent - further right and middle height
        self.play(BD.add("Z", (45, 25), label="Z", parents=["Y"], consensus_type="ghostdag"))

        # Move blocks using absolute positioning instead of shift
        # Move Y block to a new absolute position
        new_y_pos = (35, 18)
        self.play(self.move_to("Y", new_y_pos, duration=2))

        self.wait(3)

class BlockCameraDemo(Scene):
    def construct(self):
        BD = BlockDAG(self)

        # Place blocks across the field to demonstrate camera movement
        self.play(BD.add("Gen", (8, 25), label="G", consensus_type="bitcoin"))
        self.play(BD.add("X", (30, 25), label="X", consensus_type="bitcoin"))
        self.play(BD.add("Y", (45, 30), label=":)", consensus_type="bitcoin"))

        # Animate camera movements to follow the blocks
        self.play(self.animate_camera_to_sprite("X", duration=1.0))
        self.wait(1)

        self.play(self.animate_camera_to_sprite("Y", duration=1.0))
        self.wait(1)

        # Move camera by relative offset
        self.play(self.animate_camera_move(15, -13, duration=1.0))
        self.wait(1)


class BitcoinChainDemo(Scene):
    def __init__(self):
        super().__init__(resolution="720p", fps=30)

    def construct(self):
        # Create a BitcoinDAG instance
        BD = BitcoinDAG(self)

        # Add genesis block
        self.play(BD.add_bitcoin_block("Genesis", label="Genesis"))
        self.wait(0.5)

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
            middle_block = block_ids[len(block_ids) // 2]
            camera_anim = self.animate_camera_to_sprite(middle_block, duration=2.0)
            if camera_anim:
                self.play(camera_anim)

        self.wait(2)

        # Final animation: fade all blocks to show the linear structure
        fade_animations = []
        for i, block_id in enumerate(block_ids):
            fade_animations.append(
                self.fade_to(block_id, 150, duration=1.0)
            )

        self.play(*fade_animations)
        self.wait(1)

class FiftyBlocksDemo(Scene):
    """
    Stress test for seeing how long it takes to animate many objects (more than 500) simultaneously without breaking
    Set your resolution and FPS, set as scene(at the bottom), and run demo.py
    Each block has an outline, multiple labels, and 9 connections (except for the first blocks who do not have that history)
    Each block is also changing color and opacity while moving from circle to original positions
    Currently video output is 61 seconds long
    Time to render the output will depend on your computer
    """
    def __init__(self):
        super().__init__(resolution="240p", fps=8)

    def construct(self):
        # Use the basic BlockDAG for this demo
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

        # Add 50 blocks using GhostdagBlock
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

            # Always connect to immediate previous block (if it exists)
            if i > 0:
                parent_id = f"Block_{i - 1}"
                parents.append(parent_id)

                # Add 9 more connections, skipping every 2 blocks
            skip_offset = 3  # Start with offset 3 (skip 2 blocks from previous)
            connections_added = 1 if i > 0 else 0  # Count the immediate previous connection

            while connections_added < 10 and skip_offset <= i:
                parent_index = i - skip_offset
                if parent_index >= 0:
                    parent_id = f"Block_{parent_index}"
                    parents.append(parent_id)
                    connections_added += 1
                skip_offset += 3  # Skip 2 blocks (so add 3 to offset)

            # Use consensus_type="ghostdag" to create GhostdagBlock instances
            animations = BD.add(block_id, (x_pos, y_pos), label=f"{i}", parents=parents, consensus_type="ghostdag")

            # Use Scene's play method which handles the animation controller properly
            if animations:
                self.play(animations)

                # Wait for all blocks to appear
        self.wait(1)

        # Create circular movement animations using Scene methods
        move_animations = []
        center_x = horizontal_field / 2
        center_y = 25
        radius = min(horizontal_field, 50) * 0.50

        for i, block_id in enumerate(block_ids):
            import math
            angle = (i / 50) * 2 * math.pi
            new_x = center_x + radius * math.cos(angle)
            new_y = center_y + radius * math.sin(angle)

            # Use Scene's move_to method which creates proper MoveToAnimation objects
            move_animations.append(self.move_to(block_id, (new_x, new_y), duration=3.0))

            # Play all movements simultaneously using Scene's play method
        self.play(*move_animations)
        self.wait(2)

        # Return to original positions with color changes
        return_animations = []
        for i, block_id in enumerate(block_ids):
            # Recalculate original positions
            row = i // 10
            col = i % 10
            original_x = start_x + col * spacing_x
            original_y = start_y + row * spacing_y

            # Use Scene's animation methods
            return_animations.append(self.move_to(block_id, (original_x, original_y), duration=3.0))

            # Color and alpha changes
            if i < 25:
                return_animations.append(self.change_color(block_id, (0, 0, 255), duration=3.0))
                return_animations.append(self.fade_to(block_id, 75, duration=3.0))
            else:
                return_animations.append(self.change_color(block_id, (0, 255, 0), duration=3.0))

                # Play all return animations simultaneously
        self.play(*return_animations)
        self.wait(2)

class LayerDAGDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        LD = GhostDAG(self, k=3)

        # Single animation
        self.play(LD.add_with_ghostdag("Gen", label="G"))

        # Simultaneous animations (list)
        u_animations = [LD.add_with_ghostdag(f"U{i}", ["Gen"], label=str(i)) for i in range(3)]
        self.play(u_animations)

        # Sequential animations (list of lists)
        tips = LD.get_tips() # get tips to add as parents
        w_animations = [LD.add_with_ghostdag(f"W{i}", tips, label=f"W{i}") for i in range(5)]
        adjust_animations = LD.adjust_layers()

        self.play([w_animations, adjust_animations])  # Sequential: fade all W, then adjust

        color_changes = [self.change_color(tip, (0, 255, 0)) for tip in tips]
        self.play(color_changes)

        tips = LD.get_tips() # get current DAG tips to color red
        color_changes = [self.change_color(tip, (255, 0, 0)) for tip in tips]
        self.play(color_changes)

        self.wait(2.0)

class GhostDAGDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        GD = GhostDAG(self, k=1)  # Use k=3 for better visualization

        # Genesis block
        self.play(GD.add("Genesis", (10, 25), label="G"))
        self.wait(1)

        # Linear chain first
        self.play(GD.add("A", (25, 25), parents=["Genesis"], label="A"))
        self.wait(1)

        self.play(GD.add("B", (40, 25), parents=["A"], label="B"))
        self.wait(1)

        # Create a fork - two blocks with same parent
        self.play(GD.add("C", (55, 35), parents=["B"], label="C"))
        self.wait(1)

        self.play(GD.add("D", (55, 15), parents=["B"], label="D"))
        self.wait(1)

        # Merge the fork - this will test GHOSTDAG algorithm
        self.play(GD.add("E", (70, 25),
                                       parents=["C", Parent("D", color=(0, 255, 0))],
                                       label="E"))
        self.wait(1)

        # Add more blocks to see k-cluster constraints
        self.play(GD.add("F", (85, 35), parents=["E"], label="F"))
        self.wait(1)

        # Create another parallel block to test k limits
        self.play(GD.add("G", (70, 40), parents=["C"], label="G"))
        self.wait(1)

        # This should trigger red classification due to k-cluster violation
        self.play(GD.add("H", (85, 15),
                                       parents=["D", "G", "F"],
                                       label="H"))
        self.wait(2)

        # Show final state
        print("\nFinal GHOSTDAG State:")
        print(f"Blue blocks: {GD.blue_blocks}")
        print(f"Red blocks: {GD.red_blocks}")
        print(f"Block scores: {GD.block_scores}")


class SimultaneousVsSequentialDemo(Scene):
    def __init__(self):
        super().__init__(resolution='480p', fps=15)

    def construct(self):
        # Calculate positions for 5 blocks evenly spaced horizontally
        aspect_ratio = self.width / self.height
        field_width = 50 * aspect_ratio  # Approximate field width

        # Top row positions (1/3 from top)
        top_y = 50 - (50 / 3)
        # Bottom row positions (1/3 from bottom)
        bottom_y = 50 / 3

        # Calculate x positions for 5 blocks evenly spaced
        spacing = field_width / 6  # 6 gaps for 5 blocks
        x_positions = [spacing * (i + 1) for i in range(5)]

        # Create all blocks (initially invisible)
        top_blocks = []
        bottom_blocks = []

        for i in range(5):
            # Top row blocks
            top_block_id = f"top_block_{i + 1}"
            top_block = self.add_sprite(
                top_block_id,
                x_positions[i],
                top_y,
                text=f"T{i + 1}",
                color=(100, 150, 255)  # Light blue
            )
            top_block.set_visible(True)  # Make visible
            top_block.set_alpha(0)  # But start transparent
            top_blocks.append(top_block_id)

            # Bottom row blocks
            bottom_block_id = f"bottom_block_{i + 1}"
            bottom_block = self.add_sprite(
                bottom_block_id,
                x_positions[i],
                bottom_y,
                text=f"B{i + 1}",
                color=(255, 150, 100)  # Light orange
            )
            bottom_block.set_visible(True)  # Make visible
            bottom_block.set_alpha(0)  # But start transparent
            bottom_blocks.append(bottom_block_id)

            # Wait a moment before starting
        self.wait(1.0)

        # SIMULTANEOUS: Fade in all top blocks at once
        simultaneous_animations = [
            self.fade_to(block_id, 255, duration=1.5)
            for block_id in top_blocks
        ]
        self.play(simultaneous(*simultaneous_animations))

        # Wait between demonstrations
        self.wait(2.0)

        # SEQUENTIAL: Fade in bottom blocks one after another
        sequential_animations = [
            [self.fade_to(block_id, 255, duration=0.8)]
            for block_id in bottom_blocks
        ]
        self.play(sequential(*sequential_animations))

        # Final wait to see the result
        self.wait(2.0)

class AutoLayerDAGDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        # Configuration similar to GHOSTDAGScene
        AVG_AC = 4  # Average anticone size
        BLOCKS = 20  # Total blocks to generate
        MAX_BLOCKS_PER_BATCH = 3  # Max blocks per batch
        GD_K = 2  # k parameter for GhostDAG

        # Initialize GhostDAG with automatic layering
        GD = GhostDAG(self, k=GD_K)

        # Genesis block (automatic positioning)
        self.play(GD.add_with_ghostdag("Gen", label="G"))
        self.wait(0.5)

        # Adjust layers after genesis
        adjust_animations = GD.adjust_layers()
        if adjust_animations:
            self.play(adjust_animations)

        blocks_remaining = BLOCKS - 1  # Subtract genesis block
        batch_number = 0

        # Generate blocks in batches
        while blocks_remaining > 0:
            batch_number += 1
            batch_size = min(randint(1, MAX_BLOCKS_PER_BATCH), blocks_remaining)
            blocks_remaining -= batch_size

            print(f"Batch {batch_number}: Adding {batch_size} blocks")

            # Get current tips for parent selection
            current_tips = GD.get_tips()

            # Create batch of blocks
            batch_animations = []
            for i in range(batch_size):
                block_id = f"L{batch_number}_{i + 1}"

                # Select parents using Poisson distribution for anticone size
                missed_blocks = poi(lam=AVG_AC)
                selected_parents = GD.get_tips(missed_blocks=missed_blocks)

                # Add block with GhostDAG algorithm
                batch_animations.append(
                    GD.add_with_ghostdag(block_id, selected_parents, label=f"{batch_number}.{i + 1}")
                )

                # Play batch animations simultaneously
            self.play(batch_animations)
            self.wait(0.3)

            # Adjust layers after each batch
            adjust_animations = GD.adjust_layers()
            if adjust_animations:
                self.play(adjust_animations)
                self.wait(0.2)

                # Color coding based on GhostDAG classification
        self.wait(1)

        # Color blue blocks (main chain)
        if hasattr(GD, 'blue_blocks') and GD.blue_blocks:
            blue_animations = [self.change_color(block_id, (0, 100, 255))
                               for block_id in GD.blue_blocks]
            self.play(blue_animations)
            self.wait(0.5)

            # Color red blocks (off main chain)
        if hasattr(GD, 'red_blocks') and GD.red_blocks:
            red_animations = [self.change_color(block_id, (255, 100, 100))
                              for block_id in GD.red_blocks]
            self.play(red_animations)
            self.wait(0.5)

            # Final layer adjustment and tree animation
        final_adjust = GD.adjust_layers()
        if final_adjust:
            self.play(final_adjust)

            # Create tree animation if available
        if hasattr(GD, 'create_tree_animation_fast'):
            print("Creating tree animations...")
            tree_animations = GD.create_tree_animation_fast()
            if tree_animations:
                print("Playing tree animations...")
                self.play(tree_animations, run_time=5.0)
                print("Tree animations complete")

        self.wait(3)

        # Print final statistics
        print(f"\nFinal LayerDAG Statistics:")
        if hasattr(GD, 'blue_blocks'):
            print(f"Blue blocks: {len(GD.blue_blocks)}")
        if hasattr(GD, 'red_blocks'):
            print(f"Red blocks: {len(GD.red_blocks)}")
        if hasattr(GD, 'block_scores'):
            print(f"Block scores available: {len(GD.block_scores)}")

class AutoGhostDAGDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

    def construct(self):
        AVG_AC = 4  # Average anticone size
        BLOCKS = 20
        MAX_BLOCKS_PER_BATCH = 3

        GD = GhostDAG(self, k=2)

        # Genesis block
        self.play(GD.add_with_ghostdag("Gen", label="G"))

        blocks_remaining = BLOCKS - 1
        batch_number = 0

        while blocks_remaining > 0:
            batch_number += 1
            batch_size = min(randint(1, MAX_BLOCKS_PER_BATCH), blocks_remaining)
            blocks_remaining -= batch_size

            batch_animations = []
            for i in range(batch_size):
                block_id = f"L{batch_number}_{i + 1}"

                # Use Poisson distribution for missed_blocks
                missed_blocks = poi(lam=AVG_AC)
                selected_parents = GD.get_tips(missed_blocks=missed_blocks)

                batch_animations.append(
                    GD.add_with_ghostdag(block_id, parents = selected_parents, label=f"{batch_number}.{i + 1}")
                )

            self.play(batch_animations)

            # Adjust layers after each batch
            adjust_animations = GD.adjust_layers()
            if adjust_animations:
                self.play(adjust_animations)

        self.wait(2)
        # After all blocks are added, create final GHOSTDAG visualization
        final_animations = GD.create_final_ghostdag_animation()
        self.play(final_animations, run_time=5)

        self.wait(3)

if __name__ == "__main__":
    scene = BlockCameraDemo()
#    scene = BlockDAGDemo() # tested since refactoring
#    scene = BitcoinChainDemo() # tested since refactoring
#    scene = FiftyBlocksDemo() # tested since refactoring
#    scene = GhostDAGDemo()
#    scene = LayerDAGDemo()
#    scene = AutoLayerDAGDemo()
#    scene = SimultaneousVsSequentialDemo() # tested since refactoring
#    scene = AutoGhostDAGDemo() # tested since refactoring
    scene.construct()
    scene.render()

# TODO there is a way to create a living package from a project to use the project as an import, but I was unable to
#      implement this successfully so far.