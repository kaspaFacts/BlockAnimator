from blockanimator import Scene, BitcoinDAG


class BitcoinChainDemo(Scene):
    def __init__(self):
        super().__init__(resolution="720p", fps=30)

    def construct(self):
        # Create a BitcoinDAG instance
        BD = BitcoinDAG(self)

        # Add genesis block
        gen_animations = BD.add_bitcoin_block("Genesis", label="Genesis")
        self.play(gen_animations)
        self.wait(0.5)

        # Store block objects for animate API
        block_objects = {"Genesis": BD.blocks["Genesis"]}

        # Add a sequence of Bitcoin blocks, each extending the chain tip
        block_ids = ["Genesis"]
        for i in range(1, 8):
            parent = BD.get_chain_tip()
            block_id = f"Block_{i}"
            block_ids.append(block_id)

            # Add block with single parent (Bitcoin's linear chain rule)
            animations = BD.add_bitcoin_block(
                block_id,
                parent_id=parent,
                label=f"#{i}"
            )

            if animations:
                self.play(animations)
            self.wait(0.3)
            block_objects[block_id] = BD.blocks[block_id]  # Store block object

        # Validate chain integrity
        if BD.validate_chain_integrity():
            print("✓ Bitcoin chain integrity validated")

            # Show chain statistics
        print(f"Chain length: {BD.get_chain_length()}")
        print(f"Current tip: {BD.get_chain_tip()}")

        self.wait(1)

        # Highlight the entire chain with Bitcoin orange
        chain_highlight = BD.create_chain_animation(highlight_color=(255, 165, 0))
        if chain_highlight:
            self.play(chain_highlight)

        self.wait(1)

        # Demonstrate Bitcoin's single-parent constraint by trying to add an invalid block
        try:
            # This should fail because we're not extending the tip
            BD.add_bitcoin_block("Invalid", parent_id="Block_3", label="X")
        except ValueError as e:
            print(f"Expected error: {e}")

            # Move camera to follow the chain
        if len(block_ids) > 4:
            middle_block_id = block_ids[len(block_ids) // 2]
            camera_anim = self.camera.animate_camera_to_sprite(middle_block_id, duration=2.0)
            if camera_anim:
                self.play(camera_anim)

        self.wait(2)

        # Final animation: fade all blocks to show the linear structure using animate API
        fade_animations = []
        for block_id in block_ids:
            fade_animations.append(
                block_objects[block_id].animate.fade_to(150, duration=1.0)
            )

        self.play(*fade_animations)
        self.wait(1)


if __name__ == "__main__":
    scene = BitcoinChainDemo()
    scene.construct()
    scene.render()