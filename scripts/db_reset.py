"""データベースリセットスクリプト

PostgreSQLの全テーブルをTRUNCATE、Valkeyの全データを削除します。
開発環境で初期状態からやり直すために使用します。

使用方法:
    uv run python scripts/db_reset.py           # 確認プロンプトあり
    uv run python scripts/db_reset.py --force   # 確認なしで実行
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

import psycopg2
import redis


def get_database_url() -> str:
    """環境変数または既定値からデータベースURLを取得"""
    import os

    return os.getenv(
        "DATABASE_URL",
        "postgresql://count88:dev_password@localhost:5432/count88_db",
    )


def get_valkey_config() -> tuple[str, int, int]:
    """環境変数または既定値からValkey設定を取得"""
    import os

    host = os.getenv("VALKEY_HOST", "localhost")
    port = int(os.getenv("VALKEY_PORT", "6379"))
    db = int(os.getenv("VALKEY_DB", "0"))
    return host, port, db


def reset_postgresql(dsn: str, verbose: bool = True) -> bool:
    """PostgreSQLの全テーブルをリセット"""
    try:
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                # テーブル一覧を取得
                cur.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                tables = [row[0] for row in cur.fetchall()]

                if not tables:
                    if verbose:
                        print("PostgreSQL: テーブルが存在しません")
                    return True

                # alembic_versionは除外（マイグレーション履歴）
                tables_to_truncate = [t for t in tables if t != "alembic_version"]

                if not tables_to_truncate:
                    if verbose:
                        print("PostgreSQL: リセット対象のテーブルがありません")
                    return True

                # TRUNCATE実行（CASCADE で依存関係も処理）
                table_list = ", ".join(tables_to_truncate)
                cur.execute(f"TRUNCATE {table_list} RESTART IDENTITY CASCADE")

                if verbose:
                    print(f"PostgreSQL: {len(tables_to_truncate)}個のテーブルをリセットしました")
                    for t in tables_to_truncate:
                        print(f"  - {t}")

        return True

    except psycopg2.Error as e:
        print(f"PostgreSQLエラー: {e}", file=sys.stderr)
        return False


def reset_valkey(host: str, port: int, db: int, verbose: bool = True) -> bool:
    """Valkeyの全データを削除"""
    try:
        client = redis.Redis(host=host, port=port, db=db)
        client.ping()  # 接続確認

        # キー数を取得
        key_count = client.dbsize()

        # FLUSHDB実行
        client.flushdb()

        if verbose:
            print(f"Valkey: DB {db} の {key_count} 個のキーを削除しました")

        client.close()
        return True

    except redis.RedisError as e:
        print(f"Valkeyエラー: {e}", file=sys.stderr)
        return False


def confirm_reset() -> bool:
    """ユーザーに確認を求める"""
    print("\n" + "=" * 50)
    print("⚠️  警告: この操作は元に戻せません")
    print("=" * 50)
    print("\n以下のデータが全て削除されます:")
    print("  - PostgreSQL: tasks, results, progress テーブルの全レコード")
    print("  - Valkey: 指定DBの全キー")
    print()

    response = input("本当にリセットしますか？ (yes/no): ").strip().lower()
    return response == "yes"


def main(args: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="データベースをリセットします（PostgreSQL + Valkey）"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="確認プロンプトをスキップ",
    )
    parser.add_argument(
        "--postgres-only",
        action="store_true",
        help="PostgreSQLのみリセット",
    )
    parser.add_argument(
        "--valkey-only",
        action="store_true",
        help="Valkeyのみリセット",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="出力を抑制",
    )

    parsed = parser.parse_args(args)
    verbose = not parsed.quiet

    # 確認プロンプト
    if not parsed.force:
        if not confirm_reset():
            print("キャンセルしました")
            return 0

    success = True

    # PostgreSQLリセット
    if not parsed.valkey_only:
        dsn = get_database_url()
        if verbose:
            print(f"\nPostgreSQLに接続中... ({dsn.split('@')[1] if '@' in dsn else dsn})")
        if not reset_postgresql(dsn, verbose):
            success = False

    # Valkeyリセット
    if not parsed.postgres_only:
        host, port, db = get_valkey_config()
        if verbose:
            print(f"\nValkeyに接続中... ({host}:{port}, DB={db})")
        if not reset_valkey(host, port, db, verbose):
            success = False

    if verbose:
        print()
        if success:
            print("✅ リセット完了")
        else:
            print("❌ リセット中にエラーが発生しました")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
