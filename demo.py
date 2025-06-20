# demo.py
from engine.scene import Scene
from engine.helpers.block_dag import BlockDAG, Parent


class BlockDAGDemo(Scene):
    def construct(self):
        BD = BlockDAG(self)

        # Genesis block (no parents)
        self.play(BD.add("Gen", (0, 0), label="G"))

        # Block with single parent
        self.play(BD.add("X", (2, 0), label="X", parents=["Gen"]))

        # Block with multiple parents, including styled connection
        self.play(BD.add("Y", (3, 2), label=":)",
                         parents=["Gen", Parent("X", color=(0, 255, 0))]))

        # Block with single parent
        self.play(BD.add("Z", (6, 1), label="Z", parents=["Y"]))

        # Move blocks - connections automatically follow
        self.play(BD.shift("Y", (1, -3), run_time=2))

        self.wait(3)

class BlockCameraDemo(Scene):
    def construct(self):
        BD = BlockDAG(self)

        self.play(BD.add("Gen", (0, 0), label="G"))
        self.play(BD.add("X", (5, 0), label="X"))
        self.play(BD.add("Y", (10, 3), label=":)"))

        # Animate camera movements
        self.play(self.animate_camera_to_sprite("X", duration=1.0))
        self.wait(1)

        self.play(self.animate_camera_to_sprite("Y", duration=1.0))
        self.wait(1)

        self.play(self.animate_camera_move(2, -1, duration=1.0))
        self.wait(1)


class FiftyBlocksDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=15)

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

            # Display the coordinates where the block will be placed
            print(f"Block {i} will be placed at coordinates: ({x_pos:.2f}, {y_pos:.2f})")

            block_id = f"Block_{i}"
            block_ids.append(block_id)
            self.play(BD.add(block_id, (x_pos, y_pos), label=f"{i}"), duration=0.5)

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
                self.move_sprite_to(block_id, (new_x, new_y), run_time=2.0)
            )

            # Play all move animations simultaneously
        self.play(*move_animations)

        self.wait(2)

if __name__ == "__main__":
#    scene = BlockCameraDemo()
#    scene = BlockDAGDemo()
    scene = FiftyBlocksDemo()
    scene.construct()
    scene.render()

# TODO there is a way to create a living package from a project to use the project as an import, but I was unable to
#      implement this successfully so far.