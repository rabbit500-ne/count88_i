"""UI ルーター（htmx + Jinja2）"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from redis.exceptions import ConnectionError, TimeoutError
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.infra.database.session import get_db
from src.infra.models.result import Result
from src.infra.models.task import Task
from src.infra.queue.client import ValkeyClient


router = APIRouter()

_views_dir = Path(__file__).resolve().parent / "views"
templates = Jinja2Templates(directory=str(_views_dir))


@dataclass(frozen=True)
class QueueStatus:
    name: str
    length: Optional[int]
    error: Optional[str]


def _get_queue_status(
    *,
    valkey: ValkeyClient,
    queue_names: tuple[str, ...] = (
        "task_queue:bfs:phase1",
        "task_queue:bfs:phase2",
        "task_queue:dfs:phase3",
    ),
) -> list[QueueStatus]:
    out: list[QueueStatus] = []
    for q in queue_names:
        try:
            out.append(QueueStatus(name=q, length=valkey.queue_length(q), error=None))
        except (ConnectionError, TimeoutError) as e:
            out.append(QueueStatus(name=q, length=None, error=str(e)))
    return out


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """トップページ（フルページ）"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@router.get("/progress", response_class=HTMLResponse)
def progress_fragment(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """進捗フラグメント"""
    total = int(db.query(func.count(Task.task_id)).scalar() or 0)
    pending = int(db.query(func.count(Task.task_id)).filter(Task.status == "pending").scalar() or 0)
    processing = int(
        db.query(func.count(Task.task_id)).filter(Task.status == "processing").scalar() or 0
    )
    completed = int(
        db.query(func.count(Task.task_id)).filter(Task.status == "completed").scalar() or 0
    )
    failed = int(
        db.query(func.count(Task.task_id))
        .filter(Task.status.in_(("failed", "timeout")))
        .scalar()
        or 0
    )

    pct = 0.0
    if total > 0:
        pct = (completed / total) * 100.0

    return templates.TemplateResponse(
        "_progress.html",
        {
            "request": request,
            "total": total,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "progress_pct": pct,
        },
    )


@router.get("/statistics", response_class=HTMLResponse)
def statistics_fragment(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """統計フラグメント"""
    results_total = int(db.query(func.count(Result.result_id)).scalar() or 0)
    avg_time = db.query(func.avg(Result.computation_time)).scalar()
    sum_games = db.query(func.sum(Result.game_count)).scalar()

    valkey = ValkeyClient()
    queues = _get_queue_status(valkey=valkey)

    return templates.TemplateResponse(
        "_statistics.html",
        {
            "request": request,
            "results_total": results_total,
            "avg_time": float(avg_time) if avg_time is not None else None,
            "sum_games": str(sum_games) if sum_games is not None else None,
            "queues": queues,
        },
    )


@router.get("/tasks", response_class=HTMLResponse)
def tasks_fragment(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """タスク一覧フラグメント（デバッグ用途）"""
    rows: list[dict[str, Any]] = []
    tasks = db.query(Task).order_by(Task.created_at.desc()).limit(20).all()
    for t in tasks:
        rows.append(
            {
                "task_id": t.task_id,
                "task_type": t.task_type,
                "phase": t.phase,
                "status": t.status,
                "depth": t.depth,
                "assigned_to": t.assigned_to,
                "created_at": t.created_at,
                "completed_at": t.completed_at,
            }
        )

    return templates.TemplateResponse(
        "_tasks.html",
        {
            "request": request,
            "tasks": rows,
        },
    )

