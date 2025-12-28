"""タスク生成サーバのメインエントリーポイント"""

import logging

from src.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """メイン関数"""
    logger.info("タスク生成サーバを起動します")
    # TODO: Phase 1では最小限の実装
    # Phase 2以降で、タスク生成ロジックを実装
    logger.info("タスク生成サーバが起動しました")


if __name__ == "__main__":
    main()
