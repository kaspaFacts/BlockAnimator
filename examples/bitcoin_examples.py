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

# first attempt at selfishmining in bitcoin on blockanimator
# TODO need to autoregister sprites for rendering (currently appears to be handled within DAG)
class AutoRegisterBlock(Block):
    """Independent block sprite that auto-registers with scene on creation."""

    def __init__(self, x, y, sprite_id, grid_size, scene, color=(0, 0, 255), **kwargs):
        # Initialize the base Block first
        super().__init__(x, y, sprite_id, grid_size, color)

        # Auto-register with scene during creation
        self._register_with_scene(scene)

    def _register_with_scene(self, scene):
        """Automatically register this sprite with the scene's rendering system."""
        # Ensure scene has a DAG for sprite management
        if not hasattr(scene, 'dag_manager') or not scene.dag_manager.has_dag():
            # Create minimal DAG for sprite management
            minimal_dag = BlockDAG(scene=scene)
        else:
            minimal_dag = scene.dag_manager.dag_instance

            # Register in DAG's sprite management systems
        minimal_dag.sprite_registry[self.sprite_id] = self
        minimal_dag.sprites.add(self, layer=minimal_dag.BLOCK_LAYER)

        # Store position for camera targeting if grid position is set
        if hasattr(self, 'grid_x') and hasattr(self, 'grid_y'):
            scene._block_positions[self.sprite_id] = (self.grid_x, self.grid_y)

class SelfishMiningBitcoin(Scene):
    def __init__(self):
        super().__init__(resolution="480p", fps=8)
        self.blocks = {}
        self.connections = {}

        self.selfish_blocks = 0
        self.honest_blocks = 0
        self.selfish_block_chain = []
        self.honest_block_chain = []

    def construct(self):
        self._create_blocks()
        self.wait(1)
        self._fade_in_all_blocks()
        self.wait(1)
        self._fade_out_except_genesis()
        self.wait(1)
        self.play(self.reveal_next_honest_block())
        self.wait(1)
        self.play(self.animate_state_0_to_state_0())
        self.wait(3)

    def _create_blocks(self):
        """Create all blocks initially invisible with auto-registration."""
        from blockanimator.consensus.constants import AnimationConstants

        # Calculate offset to center blocks properly
        center_offset = 5

        # Calculate true center of visible grid space
        center_grid_x = self.field_width / 2
        center_grid_y = self.field_height / 2

        # Create genesis block at vertical center (blue blocks reference level)
        genesis_grid_x = center_grid_x - (2 * AnimationConstants.BLOCK_SPACING)
        genesis_grid_y = center_grid_y  # Blue blocks at center level
        genesis_grid_pos = self.coords.grid_to_pixel(genesis_grid_x, genesis_grid_y)
        genesis_pos = (genesis_grid_pos[0] - center_offset, genesis_grid_pos[1] - center_offset)

        genesis_block = AutoRegisterBlock(
            genesis_pos[0], genesis_pos[1],
            "Genesis",
            self.coords.grid_size,
            scene=self,
            color=(0, 0, 255)
        )
        genesis_block.grid_x = genesis_grid_x
        genesis_block.grid_y = genesis_grid_y
        genesis_block.set_alpha(0)
        self.blocks["Genesis"] = genesis_block

        # Create selfish chain blocks offset lower than blue blocks
        for i in range(1, 5):
            block_id = f"Selfish_{i}"
            # Selfish_2 (i=2) will be at calculated center_grid_x
            grid_x = center_grid_x + ((i - 2) * AnimationConstants.BLOCK_SPACING)
            grid_y = center_grid_y - 6  # Offset selfish blocks lower than blue blocks

            pixel_pos = self.coords.grid_to_pixel(grid_x, grid_y)
            centered_pos = (pixel_pos[0] - center_offset, pixel_pos[1] - center_offset)

            block = AutoRegisterBlock(
                centered_pos[0], centered_pos[1],
                block_id,
                self.coords.grid_size,
                scene=self,
                color=(255, 0, 0)
            )
            block.grid_x = grid_x
            block.grid_y = grid_y
            block.set_alpha(0)
            self.blocks[block_id] = block

            # CREATE CONNECTIONS FOR SELFISH CHAIN
            if i == 1:
                # Connect Selfish_1 to Genesis
                connection_id = f"Genesis_to_Selfish_1"
                connection = Connection(
                    block,  # start_block (child)
                    self.blocks["Genesis"],  # end_block (parent)
                    connection_id,
                    self.coords.grid_size,
                    color=(255, 255, 255)
                )
                connection.set_alpha(0)
                self.connections[connection_id] = connection
                self._register_connection_with_scene(connection)
            else:
                # Connect current selfish block to previous selfish block
                parent_id = f"Selfish_{i - 1}"
                connection_id = f"{parent_id}_to_{block_id}"
                connection = Connection(
                    block,  # start_block (child)
                    self.blocks[parent_id],  # end_block (parent)
                    connection_id,
                    self.coords.grid_size,
                    color=(255, 255, 255)
                )
                connection.set_alpha(0)
                self.connections[connection_id] = connection
                self._register_connection_with_scene(connection)

                # Create honest chain blocks at same vertical level as Genesis (blue blocks level)
        for i in range(1, 5):  # Create Honest_1 through Honest_4
            block_id = f"Honest_{i}"
            # Position honest blocks to the right of Genesis
            grid_x = genesis_grid_x + (i * AnimationConstants.BLOCK_SPACING)
            grid_y = center_grid_y  # Same level as Genesis (blue blocks)

            pixel_pos = self.coords.grid_to_pixel(grid_x, grid_y)
            centered_pos = (pixel_pos[0] - center_offset, pixel_pos[1] - center_offset)

            honest_block = AutoRegisterBlock(
                centered_pos[0], centered_pos[1],
                block_id,
                self.coords.grid_size,
                scene=self,
                color=(0, 0, 255)
            )
            honest_block.grid_x = grid_x
            honest_block.grid_y = grid_y
            honest_block.set_alpha(0)
            self.blocks[block_id] = honest_block

            # CREATE CONNECTIONS FOR HONEST CHAIN (exclude Honest_4)
            if i <= 3:  # Only create connections for Honest_1, Honest_2, and Honest_3
                if i == 1:
                    # Connect Honest_1 to Genesis
                    connection_id = f"Genesis_to_Honest_1"
                    connection = Connection(
                        honest_block,  # start_block (child)
                        self.blocks["Genesis"],  # end_block (parent)
                        connection_id,
                        self.coords.grid_size,
                        color=(255, 255, 255)
                    )
                    connection.set_alpha(0)
                    self.connections[connection_id] = connection
                    self._register_connection_with_scene(connection)
                else:
                    # Connect current honest block to previous honest block
                    parent_id = f"Honest_{i - 1}"
                    connection_id = f"{parent_id}_to_{block_id}"
                    connection = Connection(
                        honest_block,  # start_block (child)
                        self.blocks[parent_id],  # end_block (parent)
                        connection_id,
                        self.coords.grid_size,
                        color=(255, 255, 255)
                    )
                    connection.set_alpha(0)
                    self.connections[connection_id] = connection
                    self._register_connection_with_scene(connection)
                    # Honest_4 gets no connection - it's a standalone placeholder block

    def _register_connection_with_scene(self, connection):
        """Helper method to register connections with the scene's DAG."""
        # Get the DAG that was created by AutoRegisterBlock
        if hasattr(self, 'dag_manager') and self.dag_manager.has_dag():
            dag = self.dag_manager.dag_instance
            dag.sprite_registry[connection.sprite_id] = connection
            dag.sprites.add(connection, layer=dag.CONNECTION_LAYER)

    def _fade_in_all_blocks(self):
        """Fade in all blocks and connections using animation proxies."""
        fade_in_animations = []

        # Use animation proxies for blocks
        for block_id, block in self.blocks.items():
            block_proxy = block.animate.fade_to(255, 2.0)
            fade_in_animations.extend(block_proxy.pending_animations)
            block_proxy.pending_animations.clear()

            # Connections still need direct animation objects
        for conn_id, connection in self.connections.items():
            fade_in_animations.append(FadeToAnimation(
                sprite_id=connection.sprite_id,
                target_alpha=255,
                duration=2.0
            ))

        self.play(simultaneous(fade_in_animations))
        self.wait(1.0)

    def _fade_out_except_genesis(self):
        """Fade out all blocks except genesis using animation proxies."""
        fade_out_animations = []

        # Use animation proxies for blocks except Genesis
        for block_id, block in self.blocks.items():
            if block_id != "Genesis":
                block_proxy = block.animate.fade_to(0, 2.0)
                fade_out_animations.extend(block_proxy.pending_animations)
                block_proxy.pending_animations.clear()

                # Connections still need direct animation objects
        for conn_id, connection in self.connections.items():
            fade_out_animations.append(FadeToAnimation(
                sprite_id=connection.sprite_id,
                target_alpha=0,
                duration=2.0
            ))

        self.play(simultaneous(fade_out_animations))
        self.wait(1.0)

    def reveal_next_selfish_block(self, duration=1.0):
        """Reveal the next pre-created selfish block using animation proxies."""
        # Use the tracking list instead of alpha values
        next_block_index = len(self.selfish_block_chain) + 1
        block_id = f"Selfish_{next_block_index}"

        # Prevent revealing a 5th selfish block - only 4 are precreated
        if next_block_index > 4:
            print(f"Only 4 selfish blocks are available (Selfish_1 through Selfish_4)")
            return []

        if block_id not in self.blocks:
            print(f"No more pre-created selfish blocks available (tried {block_id})")
            return []

        if block_id in self.selfish_block_chain:
            print(f"Block {block_id} is already revealed")
            return []

            # Use animation proxy for block fade-in
        block_proxy = self.blocks[block_id].animate.fade_to(255, duration)
        animations = list(block_proxy.pending_animations)
        block_proxy.pending_animations.clear()

        # Handle connection reveal
        connection_id = None
        if next_block_index == 1:
            connection_id = "Genesis_to_Selfish_1"
        else:
            parent_id = f"Selfish_{next_block_index - 1}"
            connection_id = f"{parent_id}_to_{block_id}"

        if connection_id in self.connections:
            # Create connection fade animation directly since connections don't have animate property
            animations.append(FadeToAnimation(
                sprite_id=connection_id,
                target_alpha=255,
                duration=duration
            ))

            # Track the revealed block BEFORE returning animations
        self.selfish_block_chain.append(block_id)
        return animations

    def reveal_next_honest_block(self, duration=1.0):
        """Reveal the next pre-created honest block using animation proxies."""
        next_block_index = len(self.honest_block_chain) + 1
        block_id = f"Honest_{next_block_index}"

        if next_block_index > 3:
            print(f"Honest_4 is a placeholder block and cannot be revealed")
            return []

        if block_id not in self.blocks:
            print(f"No more pre-created honest blocks available (tried {block_id})")
            return []

        if block_id in self.honest_block_chain:
            print(f"Block {block_id} is already revealed")
            return []

            # Use animation proxy for block fade-in
        block_proxy = self.blocks[block_id].animate.fade_to(255, duration)
        animations = list(block_proxy.pending_animations)
        block_proxy.pending_animations.clear()

        # Handle connection reveal
        connection_id = None
        if next_block_index == 1:
            connection_id = "Genesis_to_Honest_1"
        else:
            parent_id = f"Honest_{next_block_index - 1}"
            connection_id = f"{parent_id}_to_{block_id}"

        if connection_id in self.connections:
            animations.append(FadeToAnimation(
                sprite_id=connection_id,
                target_alpha=255,
                duration=duration
            ))

        self.honest_block_chain.append(block_id)
        return animations

    def animate_state_0_to_state_0(self, duration=2.0):
        """Animate from state 0 to state 0 using animation proxies with proper sequential execution."""
        print(f"[SCENE] animate_state_0_to_state_0 called with duration={duration}")
        print(
            f"[SCENE] Honest_1 current state: alpha={self.blocks['Honest_1'].alpha}, visible={self.blocks['Honest_1'].visible}")

        from blockanimator.animation import sequential, simultaneous, FadeToAnimation
        from blockanimator.consensus.constants import AnimationConstants

        # Store original positions
        genesis_original_x = self.blocks["Genesis"].grid_x
        genesis_original_y = self.blocks["Genesis"].grid_y
        honest_1_original_x = self.blocks["Honest_1"].grid_x
        honest_1_original_y = self.blocks["Honest_1"].grid_y

        # Calculate movement distance
        move_distance = AnimationConstants.BLOCK_SPACING

        # Get the connection and temporarily break observer relationship to prevent automatic alpha sync
        connection = self.connections.get("Genesis_to_Honest_1")
        if connection:
            # Remove connection from Genesis's observers to prevent automatic alpha sync during animation
            if connection in self.blocks["Genesis"].alpha_observers:
                self.blocks["Genesis"].alpha_observers.remove(connection)

                # Step 1: Move both blocks left, fade Genesis and connection
        # Create and immediately extract Genesis animations to prevent shared proxy state
        genesis_step1 = self.blocks["Genesis"].animate.move_to(
            (genesis_original_x - move_distance, genesis_original_y), duration
        ).fade_to(0, duration)
        step_1_genesis_anims = list(genesis_step1.pending_animations)
        genesis_step1.pending_animations.clear()

        # Create and immediately extract Honest_1 animations
        honest_1_step1 = self.blocks["Honest_1"].animate.move_to(
            (genesis_original_x, honest_1_original_y), duration
        )
        step_1_honest_anims = list(honest_1_step1.pending_animations)
        honest_1_step1.pending_animations.clear()

        # Add connection fade animation to step 1 (connections don't have animation proxies)
        step_1_connection_anims = []
        if connection:
            step_1_connection_anims.append(FadeToAnimation(
                sprite_id="Genesis_to_Honest_1",
                target_alpha=0,
                duration=duration
            ))

            # Step 2: Reset Genesis position and make it visible (instant)
        # Create and immediately extract Genesis reset animations
        genesis_step2 = self.blocks["Genesis"].animate.move_to(
            (genesis_original_x, genesis_original_y), 0
        ).fade_to(255, 0)
        step_2_anims = list(genesis_step2.pending_animations)
        genesis_step2.pending_animations.clear()

        # Step 3: Hide and reset Honest_1 (instant), restore connection visibility
        # Create and immediately extract Honest_1 reset animations
        honest_1_step3 = self.blocks["Honest_1"].animate.fade_to(0, 0).move_to(
            (honest_1_original_x, honest_1_original_y), 0
        )
        step_3_anims = list(honest_1_step3.pending_animations)
        honest_1_step3.pending_animations.clear()

        # Add connection fade back in AFTER the movement is complete
        step_3_connection_anims = []
        if connection:
            step_3_connection_anims.append(FadeToAnimation(
                sprite_id="Genesis_to_Honest_1",
                target_alpha=255,
                duration=0
            ))

            # Reset tracking state
        if "Honest_1" in self.honest_block_chain:
            self.honest_block_chain.remove("Honest_1")

        print(f"[SCENE] Step 1: Genesis + Honest_1 proxy chains + connection fade")
        print(f"[SCENE] Step 2: Genesis proxy chain")
        print(f"[SCENE] Step 3: Honest_1 proxy chain + connection restore")

        # Create sequential steps combining proxy animations with connection animations
        # Each step uses extracted animations to prevent shared proxy state issues
        step_1 = simultaneous(step_1_genesis_anims + step_1_honest_anims + step_1_connection_anims)
        step_2 = simultaneous(step_2_anims)
        step_3 = simultaneous(step_3_anims + step_3_connection_anims)

        # Restore observer relationship after animation sequence completes
        if connection and connection not in self.blocks["Genesis"].alpha_observers:
            self.blocks["Genesis"].alpha_observers.append(connection)

        seq_result = sequential(step_1, step_2, step_3)
        print(f"Sequential result type: {type(seq_result)}")
        print(f"Has animation_groups: {hasattr(seq_result, 'animation_groups')}")
        return seq_result