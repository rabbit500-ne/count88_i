"""タスク生成サーバのメインエントリーポイント"""

import logging

from src.config import settings
from src.database.client import DatabaseClient
from src.generator.initial import generate_initial_tasks
from src.valkey.client import ValkeyClient

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """メイン関数"""
    logger.info("タスク生成サーバを起動します")
    db = DatabaseClient()
    valkey = ValkeyClient()

    task_id = generate_initial_tasks(db=db, valkey=valkey, depth=6)
    logger.info(f"初期タスクを生成して投入しました: task_id={task_id}")
    logger.info("タスク生成サーバが起動しました")


if __name__ == "__main__":
    main()
