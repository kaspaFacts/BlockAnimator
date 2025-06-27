from random import randint
from numpy.random import poisson as poi
from blockanimator import Scene, GhostDAG


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


if __name__ == "__main__":
    scene = AutoLayerDAGDemo()
    scene.construct()
    scene.render()