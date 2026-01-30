"""FastAPI アプリケーションのエントリポイント"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.infra.database.session import Base, engine
from src.api.router import router as api_router
from src.ui.admin_router import router as admin_router
from src.ui.public_router import router as public_router
from src.services.throughput_calculator import throughput_calculator


def create_app() -> FastAPI:
    """FastAPIアプリを生成"""
    app = FastAPI(title="count88 api-server", version="0.1.0")

    @app.on_event("startup")
    def _startup() -> None:
        # 開発用: マイグレーション未整備のため、最低限テーブルを作成
        # 本番/運用では Alembic に移行する想定
        Base.metadata.create_all(bind=engine)
        # スループット計算バックグラウンドタスク開始
        throughput_calculator.start()

    @app.on_event("shutdown")
    def _shutdown() -> None:
        throughput_calculator.stop()

    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # 公開画面（認証不要）
    app.include_router(public_router, tags=["public"])

    # 管理画面（本番ではnginxでBasic認証を適用）
    # パスは.envのADMIN_PATHから取得（デフォルト: ctrl-panel）
    admin_prefix = f"/{settings.admin_path}"
    app.include_router(admin_router, prefix=admin_prefix, tags=["admin"])

    # JSON API
    app.include_router(api_router)

    return app


app = create_app()

