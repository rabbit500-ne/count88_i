"""結果ドメインモデル"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal, Any

from typing import Dict, List


@dataclass
class TaskAnswer:
    """タスク結果（汎用形式）"""

    label: str
    value: Any


@dataclass
class Result:
    """結果ドメインモデル"""

    result_id: Optional[int]
    task_id: int
    result_type: Literal["BFS", "DFS"]
    task_answer: List[TaskAnswer]
    game_count: Optional[str]  # 後方互換性のため（非推奨）
    child_positions: Optional[List[Dict[str, Any]]]  # 後方互換性のため（非推奨）
    computation_time: Optional[float]
    client_id: Optional[str]
    client_info: Optional[Dict[str, Any]]
    verified: bool
    verification_count: int
    created_at: datetime

    def __post_init__(self):
        """バリデーション"""
        if self.result_type not in ["BFS", "DFS"]:
            raise ValueError(f"Invalid result_type: {self.result_type}")
