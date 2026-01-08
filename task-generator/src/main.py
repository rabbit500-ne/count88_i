"""タスク生成サーバのメインエントリーポイント"""

import logging
import time

from src.config import settings
from src.database.client import DatabaseClient
from src.generator.initial import generate_initial_tasks
from src.generator.intermediate import generate_intermediate_tasks
from src.valkey.client import ValkeyClient

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# 監視ループの設定
POLL_INTERVAL_SECONDS = 5  # ポーリング間隔（秒）


def main():
    """メイン関数"""
    logger.info("タスク生成サーバを起動します")
    db = DatabaseClient()
    valkey = ValkeyClient()

    # 初期タスク生成
    task_id = generate_initial_tasks(db=db, valkey=valkey, depth=6)
    logger.info(f"初期タスクを生成して投入しました: task_id={task_id}")
    logger.info("タスク生成サーバが起動しました")

    # 完了したタスクを監視して新しいタスクを生成
    processed_task_ids: set[int] = set()

    logger.info(f"監視ループを開始します（ポーリング間隔: {POLL_INTERVAL_SECONDS}秒）")
    while True:
        try:
            generated_count = generate_intermediate_tasks(
                db=db,
                valkey=valkey,
                processed_task_ids=processed_task_ids,
            )
            if generated_count > 0:
                logger.info(f"合計 {generated_count} 件のタスクを生成しました")

            time.sleep(POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logger.info("タスク生成サーバを停止します")
            break
        except Exception as e:
            logger.error(f"エラーが発生しました: {e}", exc_info=True)
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
