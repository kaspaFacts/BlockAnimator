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
        self.play(BD.add("Z", (5, 1), label="Z", parents=["Y"]))

        # Move blocks - connections automatically follow
        self.play(BD.shift("Y", (1, -2), run_time=2))


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

if __name__ == "__main__":
#    scene = BlockCameraDemo()
    scene = BlockDAGDemo()
    scene.construct()
    scene.render()