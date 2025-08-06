# BlockAnimator/examples/bitcoin_examples.py

from blockanimator import *

class BitcoinBasicDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=8)

    def construct(self):
        # Create a Bitcoin DAG
        bitcoin_dag = BitcoinDAG("bitcoin", scene=self)

        # Create genesis block
        genesis_animations = bitcoin_dag.add_bitcoin_block("Genesis", parent_id=None, label="Gen")
        bitcoin_dag.reveal_block("Genesis")
        self.play(genesis_animations)
        self.wait(1)

        # Create a chain of blocks
        previous_block = "Genesis"
        for i in range(1, 6):
            block_id = f"Block{i}"

            # Add block to the DAG (initially hidden)
            animations = bitcoin_dag.add_bitcoin_block(block_id, parent_id=previous_block, label=f"B{i}")

            # Reveal the block with automatic positioning
            reveal_animations = bitcoin_dag.reveal_block(block_id)
            self.play(reveal_animations)
            self.wait(0.5)

            previous_block = block_id

        self.wait(2)

class BitcoinLabelDemo(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=8)

    def construct(self):
        # Create a Bitcoin DAG
        bitcoin_dag = BitcoinDAG("bitcoin", scene=self)

        # Create genesis block
        genesis_animations = bitcoin_dag.add_bitcoin_block("Genesis", parent_id=None, label="Gen")
        bitcoin_dag.reveal_block("Genesis")
        self.play(genesis_animations)
        self.wait(1)

        # Example 1: Using animation-based label change (replaces direct setter)
        # Change Genesis label from "Gen" to "GEN" using animation
        genesis_logical_block = bitcoin_dag.logical_blocks["Genesis"]
        genesis_label_animation = genesis_logical_block.change_label("GEN", delay=0.0, duration=0.2)
        self.play(genesis_label_animation)
        self.wait(1)

        # Create a chain of blocks
        previous_block = "Genesis"
        for i in range(1, 6):
            block_id = f"Block{i}"

            # Add block to the DAG (initially hidden)
            animations = bitcoin_dag.add_bitcoin_block(block_id, parent_id=previous_block, label=f"B{i}")

            # Reveal the block with automatic positioning
            reveal_animations = bitcoin_dag.reveal_block(block_id)
            self.play(reveal_animations)
            self.wait(0.5)

            previous_block = block_id

            # Example 2: Using label change animation (timed update)
        # Change Block3's label using animation after a delay
        block3_logical = bitcoin_dag.logical_blocks["Block3"]
        label_change_animation = block3_logical.change_label("Middle", delay=1.0, duration=0.5)

        # Play the label change animation
        self.play(label_change_animation)
        self.wait(2)

        # Example 3: Multiple label changes with different timing
        # Change multiple block labels with staggered timing
        label_animations = []
        for i, new_label in enumerate(["First", "Second", "Changed", "Fourth", "Last"]):
            block_id = f"Block{i + 1}"
            if block_id in bitcoin_dag.logical_blocks:
                logical_block = bitcoin_dag.logical_blocks[block_id]
                label_anim = logical_block.change_label(new_label, delay=i * 0.3, duration=0.2)
                label_animations.append(label_anim)

                # Play all label changes simultaneously with staggered delays
        self.play(label_animations)
        self.wait(2)