"""タスクAPI"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, Response, status
from redis.exceptions import ConnectionError, TimeoutError
from sqlalchemy.orm import Session

from src.api.schemas import ErrorResponse, TaskResponse, PositionSchema
from src.infra.database.session import get_db
from src.infra.queue.client import ValkeyClient
from src.infra.repositories.task_repository import TaskRepository
from src.usecase.task_usecase import TaskUsecase


router = APIRouter()


def _bb_to_hex(v: int) -> str:
    return f"0x{v:016x}"


def _turn_to_api(turn: str) -> str:
    return "black" if turn == "B" else "white"


@router.get(
    "/task",
    response_model=TaskResponse,
    responses={
        204: {"description": "No Content"},
        503: {"model": ErrorResponse},
    },
)
def get_task(
    response: Response,
    db: Session = Depends(get_db),
    x_client_id: str | None = Header(default=None, alias="X-Client-ID"),
) -> TaskResponse | None:
    """タスクを取得"""
    task_repo = TaskRepository(db)
    valkey = ValkeyClient()
    usecase = TaskUsecase(task_repo, valkey, commit=db.commit)

    try:
        task = usecase.get_task(x_client_id)
    except (ConnectionError, TimeoutError):
        err = ErrorResponse(
            error="queue_unavailable",
            message="Valkeyに接続できません",
            timestamp=datetime.now(timezone.utc),
        )
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return err  # type: ignore[return-value]

    if task is None:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None

    return TaskResponse(
        task_id=str(task.task_id),
        task_type=task.task_type,
        position=PositionSchema(
            black=_bb_to_hex(task.position.black),
            white=_bb_to_hex(task.position.white),
            turn=_turn_to_api(task.position.turn),
        ),
        depth=task.depth,
        parent_task_id=str(task.parent_task_id) if task.parent_task_id is not None else None,
        estimated_time=5.0,
        timestamp=datetime.now(timezone.utc),
    )

