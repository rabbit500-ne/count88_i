"""タスクモデル"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    String,
    Integer,
    DateTime,
    CheckConstraint,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infra.database.session import Base


class Task(Base):
    """タスクテーブル"""

    __tablename__ = "tasks"

    task_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(10), nullable=False)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)

    parent_task_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("tasks.task_id"), nullable=True
    )

    # 局面データ
    position_black: Mapped[bytes] = mapped_column("position_black", nullable=False)  # BYTEA
    position_white: Mapped[bytes] = mapped_column("position_white", nullable=False)  # BYTEA
    turn: Mapped[str] = mapped_column(String(1), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, nullable=False)
    path_count: Mapped[str] = mapped_column(String(80), nullable=False, default="1")  # 到達パス数（多倍長整数文字列）

    # ステータス管理
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    priority: Mapped[int] = mapped_column(Integer, default=100)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # クライアント情報
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # リレーション
    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task", remote_side=[task_id], backref="child_tasks"
    )

    __table_args__ = (
        CheckConstraint("task_type IN ('BFS', 'DFS')", name="check_task_type"),
        CheckConstraint("turn IN ('B', 'W')", name="check_turn"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'timeout')",
            name="check_status",
        ),
        Index("idx_status", "status"),
        Index("idx_phase", "phase"),
        Index("idx_assigned", "assigned_to", "assigned_at"),
    )
