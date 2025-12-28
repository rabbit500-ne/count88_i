"""Valkeyクライアント"""

import logging
import time
from typing import Optional, Any

import redis
from redis.exceptions import ConnectionError, TimeoutError

from src.config import settings

logger = logging.getLogger(__name__)


class ValkeyClient:
    """Valkeyクライアントラッパー"""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        初期化

        Args:
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[redis.Redis] = None

    def connect(self) -> None:
        """Valkeyに接続"""
        try:
            self._client = redis.Redis(
                host=settings.valkey_host,
                port=settings.valkey_port,
                db=settings.valkey_db,
                decode_responses=False,  # バイナリデータを扱うため
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # 接続テスト
            self._client.ping()
            logger.info("Valkeyに接続しました")
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Valkey接続エラー: {e}")
            raise

    def _ensure_connected(self) -> None:
        """接続を確認し、必要に応じて再接続"""
        if self._client is None:
            self.connect()
        try:
            self._client.ping()
        except (ConnectionError, TimeoutError):
            logger.warning("Valkey接続が切れました。再接続します。")
            self.connect()

    def push_task(self, queue_name: str, task_id: int) -> None:
        """
        タスクをキューに追加

        Args:
            queue_name: キュー名（例: "task_queue:bfs:phase1"）
            task_id: タスクID
        """
        self._ensure_connected()
        for attempt in range(self.max_retries):
            try:
                self._client.lpush(queue_name, str(task_id))
                logger.debug(f"タスク {task_id} をキュー {queue_name} に追加しました")
                return
            except (ConnectionError, TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"キュー追加失敗（試行 {attempt + 1}/{self.max_retries}）: {e}")
                    time.sleep(self.retry_delay)
                    self._ensure_connected()
                else:
                    logger.error(f"キュー追加に失敗しました: {e}")
                    raise

    def pop_task(self, queue_name: str) -> Optional[int]:
        """
        タスクをキューから取得

        Args:
            queue_name: キュー名

        Returns:
            タスクID（キューが空の場合はNone）
        """
        self._ensure_connected()
        for attempt in range(self.max_retries):
            try:
                result = self._client.rpop(queue_name)
                if result is None:
                    return None
                return int(result)
            except (ConnectionError, TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"キュー取得失敗（試行 {attempt + 1}/{self.max_retries}）: {e}")
                    time.sleep(self.retry_delay)
                    self._ensure_connected()
                else:
                    logger.error(f"キュー取得に失敗しました: {e}")
                    raise
        return None

    def set_lock(self, lock_key: str, value: str, ttl: int = 60) -> bool:
        """
        ロックを設定

        Args:
            lock_key: ロックキー
            value: ロック値
            ttl: タイムアウト（秒）

        Returns:
            ロック設定に成功した場合True
        """
        self._ensure_connected()
        try:
            return self._client.set(lock_key, value, ex=ttl, nx=True)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"ロック設定に失敗しました: {e}")
            raise

    def delete_lock(self, lock_key: str) -> None:
        """
        ロックを削除

        Args:
            lock_key: ロックキー
        """
        self._ensure_connected()
        try:
            self._client.delete(lock_key)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"ロック削除に失敗しました: {e}")
            raise

    def close(self) -> None:
        """接続を閉じる"""
        if self._client:
            self._client.close()
            self._client = None
