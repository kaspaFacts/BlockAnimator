from blockanimator import Scene, GhostDAG, StyledParent


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


if __name__ == "__main__":
    scene = GhostDAGDemo()
    scene.construct()
    scene.render()