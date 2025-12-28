"""ユースケース層が要求するリポジトリのインタフェース群"""

from src.usecase.repositories.result_repository import IResultRepository
from src.usecase.repositories.task_repository import ITaskRepository

__all__ = [
    "ITaskRepository",
    "IResultRepository",
]

