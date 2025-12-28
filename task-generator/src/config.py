"""設定管理"""

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

    # Valkey設定
    valkey_host: str = "localhost"
    valkey_port: int = 6379
    valkey_db: int = 0

    # データベース設定
    database_url: str = "postgresql://count88:dev_password@localhost:5432/count88_db"

    # アプリケーション設定
    debug: bool = False
    log_level: str = "INFO"

    def get_valkey_url(self) -> str:
        """Valkey接続URLを取得"""
        return f"redis://{self.valkey_host}:{self.valkey_port}/{self.valkey_db}"


# グローバル設定インスタンス
settings = Settings()
