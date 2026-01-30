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
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[redis.Redis] = None

    def connect(self) -> None:
        """Valkeyに接続"""
        self._client = redis.Redis(
            host=settings.valkey_host,
            port=settings.valkey_port,
            db=settings.valkey_db,
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        self._client.ping()

    def _ensure_connected(self) -> None:
        if self._client is None:
            self.connect()
            return
        try:
            self._client.ping()
        except (ConnectionError, TimeoutError):
            self.connect()

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

    def queue_length(self, queue_name: str) -> int:
        """キュー長を取得"""
        self._ensure_connected()
        try:
            return int(self._client.llen(queue_name))
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Valkey llen 失敗: {e}")
            raise

    def get(self, key: str) -> Optional[str]:
        """キーの値を取得"""
        self._ensure_connected()
        try:
            result = self._client.get(key)
            if result is None:
                return None
            return result.decode("utf-8") if isinstance(result, bytes) else str(result)
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Valkey get 失敗: {e}")
            return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """キーに値を設定"""
        self._ensure_connected()
        try:
            return bool(self._client.set(key, value, ex=ex))
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Valkey set 失敗: {e}")
            return False

