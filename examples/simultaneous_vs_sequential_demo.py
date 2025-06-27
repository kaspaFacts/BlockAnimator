from blockanimator import Scene, BlockDAG, simultaneous, sequential


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


if __name__ == "__main__":
    scene = SimultaneousVsSequentialDemo()
    scene.construct()
    scene.render()