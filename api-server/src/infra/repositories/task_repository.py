"""タスクリポジトリ"""

from typing import Optional, List

from sqlalchemy.orm import Session

from src.domain.task import Task as DomainTask
from src.infra.models.task import Task as TaskModel
from src.usecase.repositories.task_repository import ITaskRepository


class TaskRepository(ITaskRepository):
    """タスクリポジトリ実装"""

    def __init__(self, db: Session):
        """
        初期化

        Args:
            db: データベースセッション
        """
        self.db = db

    def create(self, task: DomainTask) -> DomainTask:
        """タスクを作成"""
        task_model = TaskModel(
            task_type=task.task_type,
            phase=task.phase,
            parent_task_id=task.parent_task_id,
            position_black=task.position.black.to_bytes(8, byteorder="big"),
            position_white=task.position.white.to_bytes(8, byteorder="big"),
            turn=task.position.turn,
            depth=task.depth,
            status=task.status,
            priority=task.priority,
            retry_count=task.retry_count,
            assigned_to=task.assigned_to,
            assigned_at=task.assigned_at,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
        )
        self.db.add(task_model)
        self.db.flush()
        return self._to_domain(task_model)

    def get_by_id(self, task_id: int) -> Optional[DomainTask]:
        """IDでタスクを取得"""
        task_model = self.db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
        if task_model is None:
            return None
        return self._to_domain(task_model)

    def update(self, task: DomainTask) -> DomainTask:
        """タスクを更新"""
        if task.task_id is None:
            raise ValueError("task_id is required for update")
        task_model = (
            self.db.query(TaskModel).filter(TaskModel.task_id == task.task_id).first()
        )
        if task_model is None:
            raise ValueError(f"Task not found: {task.task_id}")

        task_model.status = task.status
        task_model.assigned_to = task.assigned_to
        task_model.assigned_at = task.assigned_at
        task_model.started_at = task.started_at
        task_model.completed_at = task.completed_at
        task_model.retry_count = task.retry_count

        self.db.flush()
        return self._to_domain(task_model)

    def get_pending_tasks(
        self, limit: int = 100, phase: Optional[str] = None
    ) -> List[DomainTask]:
        """待機中のタスクを取得"""
        query = self.db.query(TaskModel).filter(TaskModel.status == "pending")
        if phase:
            query = query.filter(TaskModel.phase == phase)
        query = query.order_by(TaskModel.priority.desc(), TaskModel.created_at.asc())
        task_models = query.limit(limit).all()
        return [self._to_domain(task_model) for task_model in task_models]

    def _to_domain(self, task_model: TaskModel) -> DomainTask:
        """モデルをドメインに変換"""
        from src.domain.position import Position

        position = Position(
            black=int.from_bytes(task_model.position_black, byteorder="big"),
            white=int.from_bytes(task_model.position_white, byteorder="big"),
            turn=task_model.turn,
        )

        return DomainTask(
            task_id=task_model.task_id,
            task_type=task_model.task_type,
            phase=task_model.phase,
            parent_task_id=task_model.parent_task_id,
            position=position,
            depth=task_model.depth,
            status=task_model.status,
            priority=task_model.priority,
            retry_count=task_model.retry_count,
            assigned_to=task_model.assigned_to,
            assigned_at=task_model.assigned_at,
            created_at=task_model.created_at,
            started_at=task_model.started_at,
            completed_at=task_model.completed_at,
        )
