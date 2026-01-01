"""API ルーター"""

from fastapi import APIRouter

from src.api.v1.task import router as v1_task_router
from src.api.v1.result import router as v1_result_router


router = APIRouter()
router.include_router(v1_task_router, prefix="/api/v1", tags=["task"])
router.include_router(v1_result_router, prefix="/api/v1", tags=["result"])

