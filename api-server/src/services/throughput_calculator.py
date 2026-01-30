"""スループット計算バックグラウンドサービス"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.infra.database.session import SessionLocal
from src.infra.models.result import Result
from src.infra.queue.client import ValkeyClient

logger = logging.getLogger(__name__)

# Redisキー
THROUGHPUT_KEY = "stats:throughput"  # 棋譜数/秒
LAST_GAME_COUNT_KEY = "stats:last_game_count"  # 前回の棋譜数
LAST_TIMESTAMP_KEY = "stats:last_timestamp"  # 前回のタイムスタンプ

# 計算間隔（秒）
CALC_INTERVAL = 60  # 1分ごとに計算
# スループット計算に使う期間（秒）
THROUGHPUT_WINDOW = 600  # 過去10分


class ThroughputCalculator:
    """スループット計算サービス"""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._valkey: Optional[ValkeyClient] = None

    def _get_valkey(self) -> ValkeyClient:
        if self._valkey is None:
            self._valkey = ValkeyClient()
        return self._valkey

    def _get_current_game_count(self, db: Session) -> Optional[Decimal]:
        """現在の総棋譜数を取得"""
        result = db.query(func.sum(Result.game_count)).scalar()
        return Decimal(str(result)) if result is not None else None

    def _calculate_throughput(self) -> None:
        """スループットを計算してRedisに保存"""
        db: Session = SessionLocal()
        try:
            valkey = self._get_valkey()
            now = datetime.utcnow()
            current_count = self._get_current_game_count(db)

            if current_count is None:
                logger.debug("棋譜数がまだ0のためスキップ")
                return

            # 前回の値を取得
            last_count_str = valkey.get(LAST_GAME_COUNT_KEY)
            last_timestamp_str = valkey.get(LAST_TIMESTAMP_KEY)

            if last_count_str and last_timestamp_str:
                last_count = Decimal(last_count_str)
                last_timestamp = datetime.fromisoformat(last_timestamp_str)

                elapsed = (now - last_timestamp).total_seconds()

                # 過去10分以内のデータのみ使用
                if 0 < elapsed <= THROUGHPUT_WINDOW:
                    diff = current_count - last_count
                    if diff >= 0:
                        throughput = float(diff) / elapsed
                        valkey.set(THROUGHPUT_KEY, str(throughput), ex=THROUGHPUT_WINDOW * 2)
                        logger.debug(f"スループット更新: {throughput:.2f} 棋譜/秒")

            # 現在の値を保存
            valkey.set(LAST_GAME_COUNT_KEY, str(current_count), ex=THROUGHPUT_WINDOW * 2)
            valkey.set(LAST_TIMESTAMP_KEY, now.isoformat(), ex=THROUGHPUT_WINDOW * 2)

        except Exception as e:
            logger.warning(f"スループット計算エラー: {e}")
        finally:
            db.close()

    async def _run_loop(self) -> None:
        """計算ループ"""
        while self._running:
            try:
                self._calculate_throughput()
            except Exception as e:
                logger.error(f"スループット計算ループエラー: {e}")
            await asyncio.sleep(CALC_INTERVAL)

    def start(self) -> None:
        """バックグラウンドタスクを開始"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("スループット計算サービス開始")

    def stop(self) -> None:
        """バックグラウンドタスクを停止"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("スループット計算サービス停止")


# シングルトンインスタンス
throughput_calculator = ThroughputCalculator()
