"""タスクリポジトリ（ユースケース側インタフェース）"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.task import Task as DomainTask


class ITaskRepository(ABC):
    """タスクリポジトリインターフェース

    - ここでは「ユースケースが必要とする操作」だけを定義する
    - DB/ORMなどのインフラ詳細は露出させない
    """

    @abstractmethod
    def create(self, task: DomainTask) -> DomainTask:
        """タスクを作成"""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, task_id: int) -> Optional[DomainTask]:
        """IDでタスクを取得"""
        raise NotImplementedError

    @abstractmethod
    def update(self, task: DomainTask) -> DomainTask:
        """タスクを更新"""
        raise NotImplementedError

    @abstractmethod
    def get_pending_tasks(
        self, limit: int = 100, phase: Optional[str] = None
    ) -> List[DomainTask]:
        """待機中のタスクを取得"""
        raise NotImplementedError

