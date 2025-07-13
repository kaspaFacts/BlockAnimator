# BlockAnimator\blockanimator\consensus\dags\dag_factory.py

from typing import List, Dict, Any
from .consensus_dags import ConsensusDAG
import importlib


class DAGFactory:
    """Factory for creating consensus-specific DAGs."""

    _DAG_TYPES = {
        "bitcoin": ("nakamoto_consensus.bitcoin_dag", "BitcoinDAG"),
        "ghostdag": ("ghostdag.ghostdag_dag", "GhostdagDAG"),
        "layer": ("layer_dag", "LayerDAG"),
        "iota": ("iota.iota_dag", "IOTADAG"),
    }

    @classmethod
    def create_dag(cls, consensus_type: str, **kwargs) -> ConsensusDAG:
        """Create a DAG for the specified consensus type."""
        if consensus_type not in cls._DAG_TYPES:
            raise ValueError(f"Unsupported consensus type: {consensus_type}")

        module_name, class_name = cls._DAG_TYPES[consensus_type]

        # Build the full module path for the nested directory structure
        full_module_name = f"blockanimator.consensus.dags.{module_name}"
        module = importlib.import_module(full_module_name)
        dag_class = getattr(module, class_name)

        return dag_class(consensus_type, **kwargs)

    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported consensus types."""
        return list(cls._DAG_TYPES.keys())


class DAGBuilder:
    """Builder for creating DAGs with a fluent interface."""

    def __init__(self, consensus_type: str):
        self.consensus_type = consensus_type
        self.config = {}

    def with_config(self, **kwargs) -> 'DAGBuilder':
        """Add configuration parameters to the DAG."""
        self.config.update(kwargs)
        return self

    def with_k_parameter(self, k: int) -> 'DAGBuilder':
        """Set the k parameter for consensus algorithms that use it."""
        self.config['k'] = k
        return self

    def build(self) -> ConsensusDAG:
        """Create the DAG instance."""
        return DAGFactory.create_dag(self.consensus_type, **self.config)

    @classmethod
    def create(cls, consensus_type: str) -> 'DAGBuilder':
        """Convenience method to start building a DAG."""
        return cls(consensus_type)