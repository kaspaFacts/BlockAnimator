# BlockAnimator\blockanimator\__init__.py

from .consensus.dags.base_dag import BlockDAG
from .consensus.dags.nakamoto_consensus.bitcoin_dag import BitcoinDAG
from .consensus.dags.layer_dag import LayerDAG
from .consensus.dags.ghostdag.ghostdag_dag import GhostdagDAG
from .consensus import StyledParent, ConsensusManager, LayerConstants, AnimationConstants
from .consensus.dags import ConsensusDAG, DAGContext, DAGFactory, DAGBuilder
from .consensus.blocks import ConsensusBlock, ConsensusBlockFactory, BlockContext

# Existing imports
from .core import Scene, CameraController, CoordinateSystem, VideoRenderer, RenderManager
from .sprites import Block, GhostdagBlock, BitcoinBlock, Connection
from .animation import (
    AnimationController,
    simultaneous,
    sequential,
    BlockAnimationProxy,
    Timeline,
    AnimationOrchestrator,
    FadeToAnimation,
    MoveToAnimation,
    ColorChangeAnimation,
    RelativeMoveAnimation,
    WaitAnimation,
    CameraMoveAnimation,
    LabelChangeAnimation
)
from .utils import DisplayConfig

__all__ = [
    # Core DAG classes
    'BlockDAG', 'BitcoinDAG', 'LayerDAG', 'GhostdagDAG',

    # Factory system
    'ConsensusDAG', 'DAGFactory', 'DAGBuilder', 'DAGContext',

    # Block system
    'ConsensusBlock', 'ConsensusBlockFactory', 'BlockContext',

    # Supporting classes
    'StyledParent', 'ConsensusManager',

    # Constants
    'LayerConstants', 'AnimationConstants',

    # Core framework
    'Scene', 'CameraController', 'CoordinateSystem', 'VideoRenderer', 'RenderManager',

    # Sprites
    'Block', 'GhostdagBlock', 'BitcoinBlock', 'Connection',

    # Animation system
    'AnimationController', 'simultaneous', 'sequential',
    'BlockAnimationProxy', 'Timeline', 'AnimationOrchestrator',
    'FadeToAnimation', 'MoveToAnimation', 'ColorChangeAnimation',
    'RelativeMoveAnimation', 'WaitAnimation', 'CameraMoveAnimation',
    'LabelChangeAnimation',

    # Utils
    'DisplayConfig'
]