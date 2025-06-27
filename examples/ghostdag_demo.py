# BlockAnimator\examples\ghostdag_demo.py
# Tested ok since adding cli interface like manim


from blockanimator import Scene, GhostDAG, StyledParent, BlockDAG


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