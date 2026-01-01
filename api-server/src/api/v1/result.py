"""結果API"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from redis.exceptions import ConnectionError, TimeoutError
from sqlalchemy.orm import Session

from src.api.schemas import ErrorResponse, ResultRequest, ResultResponse
from src.infra.database.session import get_db
from src.infra.queue.client import ValkeyClient
from src.infra.repositories.result_repository import ResultRepository
from src.infra.repositories.task_repository import TaskRepository
from src.usecase.result_usecase import ResultUsecase


router = APIRouter()


@router.post(
    "/result",
    response_model=ResultResponse,
    responses={503: {"model": ErrorResponse}},
)
def post_result(
    payload: ResultRequest,
    response: Response,
    db: Session = Depends(get_db),
    x_client_id: str | None = Header(default=None, alias="X-Client-ID"),
) -> ResultResponse:
    """結果を受け取る"""
    task_repo = TaskRepository(db)
    result_repo = ResultRepository(db)
    valkey = ValkeyClient()
    usecase = ResultUsecase(task_repo, result_repo, valkey, commit=db.commit)

    client_id = payload.client_id or x_client_id

    try:
        saved, next_available = usecase.submit_result(
            task_id=int(payload.task_id),
            task_type=payload.task_type,
            task_answer=[ta.model_dump() for ta in payload.task_answer],
            computation_time=payload.computation_time,
            client_id=client_id,
            client_info=payload.client_info,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (ConnectionError, TimeoutError):
        err = ErrorResponse(
            error="queue_unavailable",
            message="Valkeyに接続できません",
            timestamp=datetime.now(timezone.utc),
        )
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return err  # type: ignore[return-value]

    return ResultResponse(
        status="accepted",
        result_id=str(saved.result_id),
        next_task_available=next_available,
        message="結果を受け付けました",
    )

