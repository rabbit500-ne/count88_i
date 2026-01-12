"""データベースコピースクリプト

PostgreSQLのバックアップ/リストア、環境間コピーを行います。

使用方法:
    # バックアップ
    uv run python scripts/db_copy.py backup                    # デフォルトファイル名
    uv run python scripts/db_copy.py backup -o mybackup.sql    # ファイル名指定

    # リストア
    uv run python scripts/db_copy.py restore backup.sql
    uv run python scripts/db_copy.py restore backup.sql --force  # 確認なし

    # 環境間コピー（ソース → ターゲット）
    uv run python scripts/db_copy.py copy --source-url "postgresql://..." --target-url "postgresql://..."
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_database_url() -> str:
    """環境変数または既定値からデータベースURLを取得"""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://count88:dev_password@localhost:5432/count88_db",
    )


def parse_database_url(url: str) -> dict[str, str]:
    """データベースURLをパースして辞書で返す"""
    # postgresql://user:password@host:port/dbname
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return {
        "user": parsed.username or "",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "dbname": parsed.path.lstrip("/") if parsed.path else "",
    }


def run_pg_command(cmd: list[str], env: dict[str, str], verbose: bool = True) -> bool:
    """PostgreSQLコマンドを実行"""
    try:
        result = subprocess.run(
            cmd,
            env={**os.environ, **env},
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"エラー: {result.stderr}", file=sys.stderr)
            return False
        if verbose and result.stdout:
            print(result.stdout)
        return True
    except FileNotFoundError as e:
        print(f"コマンドが見つかりません: {e}", file=sys.stderr)
        print("PostgreSQLクライアントツール（pg_dump, psql）がインストールされているか確認してください")
        return False


def backup_database(output_file: str, dsn: str, verbose: bool = True) -> bool:
    """PostgreSQLをバックアップ"""
    db_config = parse_database_url(dsn)

    if verbose:
        print(f"バックアップ中... -> {output_file}")

    cmd = [
        "pg_dump",
        "-h", db_config["host"],
        "-p", db_config["port"],
        "-U", db_config["user"],
        "-d", db_config["dbname"],
        "-f", output_file,
        "--clean",  # DROP文を含める
        "--if-exists",  # DROP IF EXISTS
    ]

    env = {"PGPASSWORD": db_config["password"]}

    if run_pg_command(cmd, env, verbose):
        if verbose:
            file_size = Path(output_file).stat().st_size
            print(f"✅ バックアップ完了: {output_file} ({file_size:,} bytes)")
        return True
    return False


def restore_database(input_file: str, dsn: str, verbose: bool = True) -> bool:
    """PostgreSQLをリストア"""
    if not Path(input_file).exists():
        print(f"エラー: ファイルが見つかりません: {input_file}", file=sys.stderr)
        return False

    db_config = parse_database_url(dsn)

    if verbose:
        print(f"リストア中... <- {input_file}")

    cmd = [
        "psql",
        "-h", db_config["host"],
        "-p", db_config["port"],
        "-U", db_config["user"],
        "-d", db_config["dbname"],
        "-f", input_file,
        "-q",  # quiet
    ]

    env = {"PGPASSWORD": db_config["password"]}

    if run_pg_command(cmd, env, verbose):
        if verbose:
            print(f"✅ リストア完了")
        return True
    return False


def copy_database(source_url: str, target_url: str, verbose: bool = True) -> bool:
    """環境間でデータベースをコピー"""
    # 一時ファイルにバックアップしてリストア
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_file = f"temp_copy_{timestamp}.sql"

    try:
        if verbose:
            print(f"ソースDBからバックアップ中...")

        if not backup_database(temp_file, source_url, verbose=False):
            return False

        if verbose:
            print(f"ターゲットDBへリストア中...")

        if not restore_database(temp_file, target_url, verbose=False):
            return False

        if verbose:
            print(f"✅ コピー完了")
        return True

    finally:
        # 一時ファイルを削除
        if Path(temp_file).exists():
            Path(temp_file).unlink()


def confirm_restore() -> bool:
    """リストア前の確認"""
    print("\n" + "=" * 50)
    print("⚠️  警告: この操作は既存データを上書きします")
    print("=" * 50)
    print()
    response = input("本当にリストアしますか？ (yes/no): ").strip().lower()
    return response == "yes"


def confirm_copy() -> bool:
    """コピー前の確認"""
    print("\n" + "=" * 50)
    print("⚠️  警告: ターゲットDBの既存データが上書きされます")
    print("=" * 50)
    print()
    response = input("本当にコピーしますか？ (yes/no): ").strip().lower()
    return response == "yes"


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="データベースのバックアップ/リストア/コピー"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # backup サブコマンド
    backup_parser = subparsers.add_parser("backup", help="データベースをバックアップ")
    backup_parser.add_argument(
        "-o", "--output",
        help="出力ファイル名（デフォルト: backup_YYYYMMDD_HHMMSS.sql）",
    )
    backup_parser.add_argument(
        "--database-url",
        help="データベースURL（デフォルト: 環境変数 DATABASE_URL）",
    )

    # restore サブコマンド
    restore_parser = subparsers.add_parser("restore", help="データベースをリストア")
    restore_parser.add_argument(
        "input_file",
        help="リストアするSQLファイル",
    )
    restore_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="確認プロンプトをスキップ",
    )
    restore_parser.add_argument(
        "--database-url",
        help="データベースURL（デフォルト: 環境変数 DATABASE_URL）",
    )

    # copy サブコマンド
    copy_parser = subparsers.add_parser("copy", help="環境間でデータベースをコピー")
    copy_parser.add_argument(
        "--source-url",
        required=True,
        help="コピー元のデータベースURL",
    )
    copy_parser.add_argument(
        "--target-url",
        required=True,
        help="コピー先のデータベースURL",
    )
    copy_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="確認プロンプトをスキップ",
    )

    parsed = parser.parse_args(args)

    if parsed.command == "backup":
        dsn = parsed.database_url or get_database_url()
        output = parsed.output
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"backup_{timestamp}.sql"

        print(f"データベース: {dsn.split('@')[1] if '@' in dsn else dsn}")
        success = backup_database(output, dsn)
        return 0 if success else 1

    elif parsed.command == "restore":
        dsn = parsed.database_url or get_database_url()

        if not parsed.force:
            if not confirm_restore():
                print("キャンセルしました")
                return 0

        print(f"データベース: {dsn.split('@')[1] if '@' in dsn else dsn}")
        success = restore_database(parsed.input_file, dsn)
        return 0 if success else 1

    elif parsed.command == "copy":
        if not parsed.force:
            if not confirm_copy():
                print("キャンセルしました")
                return 0

        print(f"ソース: {parsed.source_url.split('@')[1] if '@' in parsed.source_url else parsed.source_url}")
        print(f"ターゲット: {parsed.target_url.split('@')[1] if '@' in parsed.target_url else parsed.target_url}")
        success = copy_database(parsed.source_url, parsed.target_url)
        return 0 if success else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
