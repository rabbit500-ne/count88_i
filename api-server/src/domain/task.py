"""タスクドメインモデル"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal

from src.domain.position import Position


@dataclass
class Task:
    """タスクドメインモデル"""

    task_id: Optional[int]
    task_type: Literal["BFS", "DFS"]
    phase: str
    parent_task_id: Optional[int]
    position: Position
    depth: int
    path_count: str  # 到達パス数（多倍長整数文字列）
    status: Literal["pending", "processing", "completed", "failed", "timeout"]
    priority: int
    retry_count: int
    assigned_to: Optional[str]
    assigned_at: Optional[datetime]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    def __post_init__(self):
        """バリデーション"""
        if self.task_type not in ["BFS", "DFS"]:
            raise ValueError(f"Invalid task_type: {self.task_type}")
        if self.status not in ["pending", "processing", "completed", "failed", "timeout"]:
            raise ValueError(f"Invalid status: {self.status}")
        if self.position.turn not in ["B", "W"]:
            raise ValueError(f"Invalid turn: {self.position.turn}")
