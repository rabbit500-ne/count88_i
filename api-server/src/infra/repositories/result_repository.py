"""結果リポジトリ"""

from typing import Optional, List

from sqlalchemy.orm import Session

from src.domain.result import Result as DomainResult
from src.infra.models.result import Result as ResultModel
from src.usecase.repositories.result_repository import IResultRepository


class ResultRepository(IResultRepository):
    """結果リポジトリ実装"""

    def __init__(self, db: Session):
        """
        初期化

        Args:
            db: データベースセッション
        """
        self.db = db

    def create(self, result: DomainResult) -> DomainResult:
        """結果を作成"""
        result_model = ResultModel(
            task_id=result.task_id,
            result_type=result.result_type,
            task_answer=[{"label": ta.label, "value": ta.value} for ta in result.task_answer],
            game_count=result.game_count,
            child_positions=result.child_positions,
            computation_time=result.computation_time,
            client_id=result.client_id,
            client_info=result.client_info,
            verified=result.verified,
            verification_count=result.verification_count,
            created_at=result.created_at,
        )
        self.db.add(result_model)
        self.db.flush()
        return self._to_domain(result_model)

    def get_by_id(self, result_id: int) -> Optional[DomainResult]:
        """IDで結果を取得"""
        result_model = (
            self.db.query(ResultModel).filter(ResultModel.result_id == result_id).first()
        )
        if result_model is None:
            return None
        return self._to_domain(result_model)

    def get_by_task_id(self, task_id: int) -> List[DomainResult]:
        """タスクIDで結果を取得"""
        result_models = (
            self.db.query(ResultModel).filter(ResultModel.task_id == task_id).all()
        )
        return [self._to_domain(result_model) for result_model in result_models]

    def _to_domain(self, result_model: ResultModel) -> DomainResult:
        """モデルをドメインに変換"""
        from src.domain.result import TaskAnswer

        task_answer = [
            TaskAnswer(label=ta["label"], value=ta["value"]) for ta in result_model.task_answer
        ]

        return DomainResult(
            result_id=result_model.result_id,
            task_id=result_model.task_id,
            result_type=result_model.result_type,
            task_answer=task_answer,
            game_count=str(result_model.game_count) if result_model.game_count else None,
            child_positions=result_model.child_positions,
            computation_time=result_model.computation_time,
            client_id=result_model.client_id,
            client_info=result_model.client_info,
            verified=result_model.verified,
            verification_count=result_model.verification_count,
            created_at=result_model.created_at,
        )
