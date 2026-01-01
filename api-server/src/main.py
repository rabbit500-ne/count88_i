"""FastAPI アプリケーションのエントリポイント"""

from fastapi import FastAPI

from src.infra.database.session import Base, engine
from src.api.router import router as api_router


def create_app() -> FastAPI:
    """FastAPIアプリを生成"""
    app = FastAPI(title="count88 api-server", version="0.1.0")

    @app.on_event("startup")
    def _startup() -> None:
        # 開発用: マイグレーション未整備のため、最低限テーブルを作成
        # 本番/運用では Alembic に移行する想定
        Base.metadata.create_all(bind=engine)

    app.include_router(api_router)
    return app


app = create_app()

