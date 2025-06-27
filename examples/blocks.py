from blockanimator import Scene, BlockDAG, StyledParent

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


if __name__ == "__main__":
    scene = BlockDAGDemo()
    scene.construct()
    scene.render()