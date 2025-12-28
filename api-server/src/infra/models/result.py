"""結果モデル"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    String,
    Float,
    DateTime,
    Boolean,
    Integer,
    CheckConstraint,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database.session import Base


class Result(Base):
    """結果テーブル"""

    __tablename__ = "results"

    result_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False
    )
    result_type: Mapped[str] = mapped_column(String(10), nullable=False)

    # タスク結果（汎用形式、JSONB形式）
    task_answer: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # 後方互換性のための個別カラム（非推奨、将来削除予定）
    game_count: Mapped[Optional[str]] = mapped_column(NUMERIC(80, 0), nullable=True)
    child_positions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # メタデータ
    computation_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    client_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    client_info: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # 検証
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # リレーション
    task: Mapped["Task"] = relationship("Task", backref="results")

    __table_args__ = (
        CheckConstraint("result_type IN ('BFS', 'DFS')", name="check_result_type"),
        Index("idx_task_id", "task_id"),
        Index("idx_verified", "verified"),
    )
