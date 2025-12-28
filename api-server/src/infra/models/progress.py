"""進捗モデル"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Integer,
    BigInteger,
    String,
    Float,
    DateTime,
    NUMERIC,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.infra.database.session import Base


class Progress(Base):
    """進捗テーブル"""

    __tablename__ = "progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)

    # タスク統計
    total_tasks: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    completed_tasks: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    failed_tasks: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # 棋譜数集計
    total_games: Mapped[Optional[str]] = mapped_column(NUMERIC(80, 0), nullable=True, default=0)

    # パフォーマンス指標
    tasks_per_second: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_computation_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # クライアント情報
    active_clients: Mapped[int] = mapped_column(Integer, default=0)

    # 推定
    estimated_completion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
