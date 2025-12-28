"""結果リポジトリ（ユースケース側インタフェース）"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.result import Result as DomainResult


class IResultRepository(ABC):
    """結果リポジトリインターフェース

    - ここでは「ユースケースが必要とする操作」だけを定義する
    - DB/ORMなどのインフラ詳細は露出させない
    """

    @abstractmethod
    def create(self, result: DomainResult) -> DomainResult:
        """結果を作成"""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, result_id: int) -> Optional[DomainResult]:
        """IDで結果を取得"""
        raise NotImplementedError

    @abstractmethod
    def get_by_task_id(self, task_id: int) -> List[DomainResult]:
        """タスクIDで結果を取得"""
        raise NotImplementedError

