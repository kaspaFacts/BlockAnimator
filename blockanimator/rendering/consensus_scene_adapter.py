# BlockAnimator\blockanimator\rendering\consensus_scene_adapter.py

from typing import List

from .visual_dag_renderer import VisualDAGRenderer
from ..animation import Animation
from ..consensus.dags.dag_factory import DAGFactory


class ConsensusSceneAdapter:
    def __init__(self, scene, consensus_type: str, **dag_config):
        self.logical_dag = DAGFactory.create_dag(consensus_type, **dag_config)
        self.renderer = VisualDAGRenderer(scene, self.logical_dag)

    def add(self, block_id: str, parents=None, **kwargs) -> List[Animation]:
        return self.renderer.add_visual_block(block_id, parents=parents, **kwargs)