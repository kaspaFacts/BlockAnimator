import math
from blockanimator import Scene, BlockDAG


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


if __name__ == "__main__":
    scene = FiftyBlocksDemo()
    scene.construct()
    scene.render()