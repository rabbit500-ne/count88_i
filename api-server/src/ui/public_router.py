"""公開画面ルーター（htmx + Jinja2）"""

from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.infra.database.session import get_db
from src.infra.models.result import Result
from src.infra.queue.client import ValkeyClient
from src.services.throughput_calculator import THROUGHPUT_KEY


logger = logging.getLogger(__name__)

router = APIRouter()

_base_views_dir = Path(__file__).resolve().parent / "views"
templates = Jinja2Templates(directory=str(_base_views_dir))

# オセロの全棋譜数の予想（10^58）
ESTIMATED_TOTAL_GAMES = Decimal("1e58")


def _format_duration(seconds: float) -> str:
    """秒数を人間が読みやすい形式に変換"""
    if seconds <= 0:
        return ""
    
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    years = days // 365
    
    # 非常に大きな年数は科学表記法で表示
    if years > 1e12:
        # 10^n 形式で表示
        import math
        exp = int(math.log10(years))
        mantissa = years / (10 ** exp)
        return f"約 {mantissa:.1f} × 10<sup>{exp}</sup> 年"
    elif years > 1000000:
        return f"約 {years / 1e6:.1f} 百万年"
    elif years > 1000:
        return f"約 {years:,} 年"
    elif days > 365:
        return f"約 {years:,} 年"
    elif days > 0:
        return f"約 {days:,} 日 {hours} 時間"
    elif hours > 0:
        return f"約 {hours} 時間 {minutes} 分"
    elif minutes > 0:
        return f"約 {minutes} 分"
    else:
        return "まもなく完了"


def _get_throughput() -> Optional[float]:
    """Redisからスループット（棋譜数/秒）を取得"""
    try:
        valkey = ValkeyClient()
        value = valkey.get(THROUGHPUT_KEY)
        if value:
            return float(value)
    except Exception as e:
        logger.warning(f"スループット取得エラー: {e}")
    return None


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """公開用トップページ"""
    return templates.TemplateResponse(
        "public/index.html",
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
    # game_count合計（DFS結果から）
    sum_games = db.query(func.sum(Result.game_count)).scalar()

    # 残り時間推定（10^58 / スループット）
    estimated_remaining: Optional[str] = None
    throughput = _get_throughput()
    if throughput and throughput > 0:
        remaining_seconds = float(ESTIMATED_TOTAL_GAMES / Decimal(str(throughput)))
        estimated_remaining = _format_duration(remaining_seconds)

    return templates.TemplateResponse(
        "public/_progress.html",
        {
            "request": request,
            "sum_games": str(sum_games) if sum_games is not None else None,
            "estimated_remaining": estimated_remaining,
        },
    )
