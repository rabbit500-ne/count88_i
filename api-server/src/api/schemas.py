"""API スキーマ（Pydantic）"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


class PositionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    black: str = Field(..., description="0x から始まる16進表現（64bit）")
    white: str = Field(..., description="0x から始まる16進表現（64bit）")
    turn: Literal["black", "white"]


class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    task_type: Literal["BFS", "DFS"]
    position: PositionSchema
    depth: int
    parent_task_id: Optional[str] = None
    estimated_time: float = 5.0
    timestamp: datetime


class TaskAnswerSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    value: Any


class ResultRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    task_type: Literal["BFS", "DFS"]
    task_answer: list[TaskAnswerSchema]
    computation_time: Optional[float] = None
    client_id: Optional[str] = None
    client_info: Optional[dict[str, Any]] = None


class ResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["accepted"]
    result_id: str
    next_task_available: bool
    message: str = "結果を受け付けました"


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: str
    message: str
    timestamp: datetime

