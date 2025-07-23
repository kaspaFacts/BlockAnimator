# BlockAnimator

Working on completing manim-like animation system INCOMPLETE

Requirements and Getting Started
Prerequisites

    Python 3.8 or higher README.md:19
    Git (for cloning the repository) README.md:20
    A code editor (VS Code, PyCharm, etc.) README.md:21

Installation
Option A: Install as Package

# Install directly from GitHub  
pip install git+https://github.com/KapsaFacts/BlockAnimator.git  
  
# Or clone and install  
git clone https://github.com/KapsaFacts/BlockAnimator.git  
cd BlockAnimator  
pip install .

Option B: Development Installation

    Clone the repository

git clone https://github.com/KapsaFacts/BlockAnimator.git    
cd BlockAnimator

    Create virtual environment (recommended)

# Create virtual environment    
python -m venv blockanimator-env    
    
# Activate it    
# On Windows:    
blockanimator-env\Scripts\activate    
# On macOS/Linux:    
source blockanimator-env/bin/activate

    Install in development mode

pip install -e .

Verify Installation

# test_installation.py    
try:    
    import blockanimator    
    print("✓ Successfully imported blockanimator")    
        
    from blockanimator import Scene, BlockDAG  
    print("✓ Successfully imported core classes")    
        
except ImportError as e:    
    print(f"✗ Import failed: {e}")

run blockanimator demo_scenes.py then you can select from any of the demo scenes

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/kaspaFacts/BlockAnimator)