# BlockAnimator\blockanimator\consensus\dag_types.py

from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class StyledParent:
    """Helper for defining parent relationships with visual styling."""
    parent_id: str
    color: Optional[tuple] = None
    width: int = 2
    selected_parent: bool = False
    kwargs: Dict[str, Any] = None

    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}