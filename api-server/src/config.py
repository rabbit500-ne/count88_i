"""設定管理"""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()


class Settings(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # データベース設定
    database_url: str = "postgresql://count88:dev_password@localhost:5432/count88_db"

    # Valkey設定
    valkey_host: str = "localhost"
    valkey_port: int = 6379
    valkey_db: int = 0

    # アプリケーション設定
    debug: bool = False
    log_level: str = "INFO"

    # セキュリティ設定
    secret_key: Optional[str] = None

    def get_database_url(self) -> str:
        """データベース接続URLを取得"""
        return self.database_url

    def get_valkey_url(self) -> str:
        """Valkey接続URLを取得"""
        return f"redis://{self.valkey_host}:{self.valkey_port}/{self.valkey_db}"


# グローバル設定インスタンス
settings = Settings()
