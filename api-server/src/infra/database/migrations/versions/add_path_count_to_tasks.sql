-- Issue #12: tasksテーブルにpath_countカラムを追加
-- 到達パス数（多倍長整数文字列）を保存するためのカラム

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS path_count VARCHAR(80) NOT NULL DEFAULT '1';

-- コメント追加
COMMENT ON COLUMN tasks.path_count IS '到達パス数（多倍長整数文字列）';
