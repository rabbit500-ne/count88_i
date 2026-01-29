"""公開画面ルーター（htmx + Jinja2）"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.infra.database.session import get_db
from src.infra.models.result import Result
from src.infra.models.task import Task


router = APIRouter()

_base_views_dir = Path(__file__).resolve().parent / "views"
templates = Jinja2Templates(directory=str(_base_views_dir))


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """公開用トップページ"""
    return templates.TemplateResponse(
        "public/index.html",
        {
            "request": request,
        },
    )


@router.get("/participate", response_class=HTMLResponse)
def participate(request: Request) -> HTMLResponse:
    """分散計算参加ページ"""
    return templates.TemplateResponse(
        "public/participate.html",
        {
            "request": request,
        },
    )


@router.get("/progress-fragment", response_class=HTMLResponse)
def progress_fragment(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """進捗フラグメント（公開用、簡易版）"""
    def _count_tasks(*, statuses: Optional[tuple[str, ...]] = None) -> int:
        q = db.query(func.count(Task.task_id))
        if statuses is not None:
            if len(statuses) == 1:
                q = q.filter(Task.status == statuses[0])
            else:
                q = q.filter(Task.status.in_(statuses))
        return int(q.scalar() or 0)

    total = _count_tasks()
    completed = _count_tasks(statuses=("completed",))
    progress_pct = (completed / total) * 100.0 if total > 0 else 0.0

    # game_count合計（DFS結果から）
    sum_games = db.query(func.sum(Result.game_count)).scalar()

    return templates.TemplateResponse(
        "public/_progress.html",
        {
            "request": request,
            "total": total,
            "completed": completed,
            "progress_pct": progress_pct,
            "sum_games": str(sum_games) if sum_games is not None else None,
        },
    )
