"""Valkeyクライアント"""

import logging
import time
from typing import Optional

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

    def _ensure_connected(self) -> None:
        """接続を確認し、必要に応じて再接続"""
        if self._client is None:
            self.connect()
            return
        try:
            self._client.ping()
        except (ConnectionError, TimeoutError):
            self.connect()

    def push_task(self, queue_name: str, task_id: int) -> None:
        """タスクをキューに追加"""
        self._ensure_connected()
        for attempt in range(self.max_retries):
            try:
                self._client.lpush(queue_name, str(task_id))
                return
            except (ConnectionError, TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    self._ensure_connected()
                else:
                    logger.error(f"Valkey push 失敗: {e}")
                    raise

    def pop_task(self, queue_name: str) -> Optional[int]:
        """タスクIDをRPOPで取得（空ならNone）"""
        self._ensure_connected()
        for attempt in range(self.max_retries):
            try:
                result = self._client.rpop(queue_name)
                if result is None:
                    return None
                return int(result)
            except (ConnectionError, TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    self._ensure_connected()
                else:
                    logger.error(f"Valkey pop 失敗: {e}")
                    raise
        return None

    def set_lock(self, lock_key: str, value: str, ttl: int = 60) -> bool:
        """ロックを設定（SET NX EX）"""
        self._ensure_connected()
        try:
            return bool(self._client.set(lock_key, value, ex=ttl, nx=True))
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Valkey lock 失敗: {e}")
            raise

    def delete_lock(self, lock_key: str) -> None:
        """ロックを削除"""
        self._ensure_connected()
        try:
            self._client.delete(lock_key)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Valkey lock delete 失敗: {e}")
            raise

    def close(self) -> None:
        """接続を閉じる"""
        if self._client:
            self._client.close()
            self._client = None

