"""FastAPI アプリケーションのエントリポイント"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.infra.database.session import Base, engine
from src.api.router import router as api_router
from src.ui.router import router as ui_router


def create_app() -> FastAPI:
    """FastAPIアプリを生成"""
    app = FastAPI(title="count88 api-server", version="0.1.0")

    @app.on_event("startup")
    def _startup() -> None:
        # 開発用: マイグレーション未整備のため、最低限テーブルを作成
        # 本番/運用では Alembic に移行する想定
        Base.metadata.create_all(bind=engine)

    @app.get("/", include_in_schema=False)
    def _root() -> RedirectResponse:
        return RedirectResponse(url="/ui/", status_code=302)

    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(ui_router, prefix="/ui", tags=["ui"])
    app.include_router(api_router)
    return app


app = create_app()

