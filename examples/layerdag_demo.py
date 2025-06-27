from blockanimator import Scene, GhostDAG


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


if __name__ == "__main__":
    scene = LayerDAGDemo()
    scene.construct()
    scene.render()