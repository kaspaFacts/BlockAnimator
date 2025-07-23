# BlockAnimator
Create Animations using PyGame and Output to MP4 using OpenCV

Currently broken(in the process of rewriting for ease of adding additional consensus methods, 
when complete, will only require adding consensus methods within blockanimator\consensus dir.)

Since writing this README cli interface has been added to run demos from terminal with the ability to override settings.
(Incomplete for rewrite)

To run a demo, check what demo will be run at the bottom of demo.py, comment out any you do not wish to run, then run demo.py directly(in pycharm, right-click on demo.py and "Run"), a new mp4 video will be generated in the same folder next to demo.py

stress test - FiftyBlocksDemo (creates 50 blocks, spaced along the coord grid, with connections to 9 previous blocks, moves from grid position to circular arrangement, then moves back to grid arrangement while half of the blocks fade opacity to 30%, and the other half change to green, while connections remain updated to each block)

NOTE: when viewing animations in a media player(and sliding time), the media player will drop frames, but frames are rendered and exported to mp4


Installation Instructions for BlockAnimator Prerequisites

    Python 3.8 or higher
    Git (for cloning the repository)
    A code editor (VS Code, PyCharm, etc.)

Step 1: Clone the Repository

git clone https://github.com/KapsaFacts/BlockAnimator.git  
cd BlockAnimator

Step 2: Create a Virtual Environment (Recommended)

# Create virtual environment  
python -m venv blockanimator-env  
  
# Activate it  
# On Windows:  
blockanimator-env\Scripts\activate  
# On macOS/Linux:  
source blockanimator-env/bin/activate

Step 3: Install the Package

From the BlockAnimator project root directory, install in development mode:

pip install -e .

This installs the package based on the configuration you set up, which includes all dependencies like pygame, opencv-python, and numpy.
Step 4: Verify Installation

Test that the package imports correctly:

# test_installation.py  
try:  
    import blockanimator  
    print("✓ Successfully imported blockanimator")  
      
    from blockanimator import Scene, BlockDAG, BitcoinDAG, GhostDAG  
    print("✓ Successfully imported core classes")  
      
    print(f"Available classes: {[attr for attr in dir(blockanimator) if not attr.startswith('_')]}")  
      
except ImportError as e:  
    print(f"✗ Import failed: {e}")

Step 5: Run Demo Examples
Option A: Run Examples from the BlockAnimator/examples/ Directory

Navigate to the examples folder and run any demo:

cd examples  
python basic_dag_demo.py  
python bitcoin_chain_demo.py  
python ghostdag_demo.py

or right-click -> run in editor

Option B: Create Your Own Project

Create a new directory outside of BlockAnimator:

mkdir my-blockchain-animations  
cd my-blockchain-animations

Create a simple test script:

# my_first_animation.py
from blockanimator import Scene, BlockDAG  
  
class MyFirstAnimation(Scene):  
    def construct(self):  
        # Create a DAG  
        dag = BlockDAG(self)  
          
        # Add some blocks  
        genesis_anims = dag.add("Genesis", (10, 25), label="G")  
        self.play(genesis_anims)  
          
        block_a_anims = dag.add("A", (25, 25), label="A", parents=["Genesis"])  
        self.play(block_a_anims)  
          
        self.wait(2)  
  
if __name__ == "__main__":  
    scene = MyFirstAnimation()  
    scene.construct()  
    scene.render()

Run your animation:

python my_first_animation.py

# TODO format this properly
# TODO fix examples (only ghostdag_demo.py is properly set up to work with new manim-like cli interface)

https://deepwiki.com/kaspaFacts/BlockAnimator