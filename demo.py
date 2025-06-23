# demo.py
from engine.scene import Scene
from engine.helpers.block_dag import BlockDAG, GhostDAG, Parent


class BlockDAGDemo(Scene):
    def construct(self):
        BD = BlockDAG(self)

        # Genesis block near bottom-left with margin
        self.play(BD.add("Gen", (10,25), label="G"))

        # Block with single parent - space horizontally
        self.play(BD.add("X", (25, 25), label="X", parents=["Gen"]))

        # Block with multiple parents - position higher and to the right
        self.play(BD.add("Y", (30, 35), label=":)",
                         parents=["Gen", Parent("X", color=(0, 255, 0))]))

        # Block with single parent - further right and middle height
        self.play(BD.add("Z", (45, 25), label="Z", parents=["Y"]))

        # Move blocks using absolute positioning instead of shift
        # Move Y block to a new absolute position
        new_y_pos = (35, 18)
        self.play(self.move_to("Y", new_y_pos, duration=2))

        self.wait(3)

class BlockCameraDemo(Scene):
    def construct(self):
        BD = BlockDAG(self)

        # Place blocks across the field to demonstrate camera movement
        self.play(BD.add("Gen", (8, 25), label="G"))
        self.play(BD.add("X", (30, 25), label="X"))
        self.play(BD.add("Y", (45, 30), label=":)"))

        # Animate camera movements to follow the blocks
        self.play(self.animate_camera_to_sprite("X", duration=1.0))
        self.wait(1)

        self.play(self.animate_camera_to_sprite("Y", duration=1.0))
        self.wait(1)

        # Move camera by relative offset
        self.play(self.animate_camera_move(15, -13, duration=1.0))
        self.wait(1)

class FiftyBlocksDemo(Scene):
    def __init__(self):
        super().__init__(resolution="240p", fps=15)

    def construct(self):
        BD = BlockDAG(self)

        # With the corrected coordinate system, we now have exactly 50 units vertically
        # Calculate horizontal field based on aspect ratio
        aspect_ratio = self.width / self.height  # 426/240 ≈ 1.775 for 240p
        horizontal_field = 50 * aspect_ratio  # ~88.75 units horizontally

        # Start placing blocks with better spacing for the fixed field
        start_x = 2  # Start 2 units from left edge
        start_y = 2  # Start 2 units from bottom edge

        # Calculate spacing to fit blocks nicely in the field
        grid_width = 10  # 10 columns
        grid_height = 5  # 5 rows

        # Use available space more efficiently
        available_width = horizontal_field - 4  # Leave 2 units margin on each side
        available_height = 50 - 4  # Leave 2 units margin top and bottom

        spacing_x = available_width / (grid_width - 1) if grid_width > 1 else 2
        spacing_y = available_height / (grid_height - 1) if grid_height > 1 else 2

        # Add 50 blocks spaced evenly in a grid pattern starting from bottom-left
        block_ids = []
        for i in range(50):
            row = i // 10  # 5 rows of 10 blocks each
            col = i % 10
            x_pos = start_x + col * spacing_x
            y_pos = start_y + row * spacing_y

            print(f"Block {i} will be placed at coordinates: ({x_pos:.2f}, {y_pos:.2f})")

            block_id = f"Block_{i}"
            block_ids.append(block_id)

            # Determine parent for this block (previous block in sequence)
            parents = []
            if i > 0:  # All blocks except the first have the previous block as parent
                parent_id = f"Block_{i - 1}"
                parents = [parent_id]

                # Add block with parent connection
            self.play(BD.add(block_id, (x_pos, y_pos), label=f"{i}", parents=parents), duration=0.5)

        self.wait(1)  # Pause to show the initial grid

        # Move all blocks simultaneously using Scene's move_to method
        move_animations = []

        # Center the circular arrangement in the middle of the screen
        center_x = horizontal_field / 2  # ~44.4 units for 480p
        center_y = 25  # Middle of 50-unit height (25 units up from bottom)
        radius = min(horizontal_field, 50) * 0.50  # Smaller radius to ensure visibility

        for i, block_id in enumerate(block_ids):
            # Calculate new positions (circular arrangement)
            import math
            angle = (i / 50) * 2 * math.pi
            new_x = center_x + radius * math.cos(angle)
            new_y = center_y + radius * math.sin(angle)

            print(f"Block {i} will be moved to coordinates: ({new_x:.2f}, {new_y:.2f})")

            # Use Scene's move_to method instead of BD.shift()
            move_animations.append(
                self.move_to(block_id, (new_x, new_y), duration=3.0)
            )

            # Play all move animations simultaneously
        self.play(*move_animations)

        self.wait(2)
        # Create animations to move all blocks back to original positions with alpha changes
        return_animations = []
        for i, block_id in enumerate(block_ids):
            # Recalculate original position using same logic as initial placement
            row = i // 10
            col = i % 10
            original_x = start_x + col * spacing_x
            original_y = start_y + row * spacing_y

            # Add movement animation for all blocks
            return_animations.append(
                self.move_to(block_id, (original_x, original_y), duration=3.0)
            )

            # Add alpha change for first half of blocks (blocks 0-24)
            if i < 25:
                return_animations.append(
                    self.change_appearance(block_id, target_color=(0,0,255), target_alpha=75, duration=3.0)
                )
                # Second half keeps original alpha (blocks 25-49)
            else:
                return_animations.append(
                    self.change_appearance(block_id, target_color=(0,255,0), duration=3.0)
                )

                # Play all return animations simultaneously
        self.play(*return_animations)
        self.wait(2)  # Final pause to show the restored grid

class LayerDAGDemo(Scene):
    def __init__(self):
        super().__init__(resolution="240p", fps=15)

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
        super().__init__(resolution="240p", fps=15)

    def construct(self):
        GD = GhostDAG(self, k=3)  # Use k=3 for better visualization

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

class ComplexGhostDAGDemo(Scene):
    """More complex demo showing k-cluster constraints"""

    def construct(self):
        GD = GhostDAG(self, k=2)  # Stricter k for more red blocks

        # Create a more complex DAG structure
        positions = {
            "G": (10, 25),
            "A": (25, 25), "B": (25, 35), "C": (25, 15),
            "D": (40, 30), "E": (40, 20),
            "F": (55, 35), "H": (55, 15),
            "I": (70, 25)
        }

        # Build DAG step by step
        self.play(GD.add("G", positions["G"], label="G"))
        self.wait(0.5)

        # Three children of genesis
        self.play(GD.add("A", positions["A"], parents=["G"], label="A"))
        self.wait(0.5)
        self.play(GD.add("B", positions["B"], parents=["G"], label="B"))
        self.wait(0.5)
        self.play(GD.add("C", positions["C"], parents=["G"], label="C"))
        self.wait(0.5)

        # Merge some of them
        self.play(GD.add("D", positions["D"], parents=["A", "B"], label="D"))
        self.wait(0.5)
        self.play(GD.add("E", positions["E"], parents=["A", "C"], label="E"))
        self.wait(0.5)

        # More complex merges that should trigger red classification
        self.play(GD.add("F", positions["F"], parents=["B", "D"], label="F"))
        self.wait(0.5)
        self.play(GD.add("H", positions["H"], parents=["C", "E"], label="H"))
        self.wait(0.5)

        # Final merge - this should definitely be red due to k=2 constraint
        self.play(GD.add("I", positions["I"], parents=["D", "E", "F", "H"], label="I"))
        self.wait(3)

if __name__ == "__main__":
#    scene = BlockCameraDemo()
#    scene = BlockDAGDemo()
#    scene = FiftyBlocksDemo()
#    scene = GhostDAGDemo()
    scene = LayerDAGDemo()
#    scene = ComplexGhostDAGDemo()
    scene.construct()
    scene.render()

# TODO there is a way to create a living package from a project to use the project as an import, but I was unable to
#      implement this successfully so far.