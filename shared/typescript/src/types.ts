/** オセロ（リバーシ）の型定義 */

/** 手番 */
export type Turn = "black" | "white";

/** ビットボード（64bit整数を文字列で表現） */
export type BitboardString = string;

/** 局面 */
export interface Position {
  /** 黒石の配置（16進数文字列） */
  black: BitboardString;
  /** 白石の配置（16進数文字列） */
  white: BitboardString;
  /** 手番 */
  turn: Turn;
}

/** タスクタイプ */
export type TaskType = "BFS" | "DFS";

/** タスク */
export interface Task {
  /** タスクID */
  task_id: string;
  /** タスクタイプ */
  task_type: TaskType;
  /** 局面 */
  position: Position;
  /** 深さ */
  depth: number;
  /** 親タスクID */
  parent_task_id: string | null;
  /** 推定計算時間（秒） */
  estimated_time: number;
  /** タイムスタンプ */
  timestamp: string;
}

/** タスク結果（汎用形式） */
export interface TaskAnswer {
  /** ラベル */
  label: string;
  /** 値（型はラベルによって異なる） */
  value: unknown;
}

/** 結果送信リクエスト */
export interface ResultRequest {
  /** タスクID */
  task_id: string;
  /** タスクタイプ */
  task_type: TaskType;
  /** タスク結果 */
  task_answer: TaskAnswer[];
  /** 計算時間（秒） */
  computation_time: number;
  /** クライアントID */
  client_id: string;
  /** クライアント情報 */
  client_info?: {
    user_agent?: string;
    cpu_cores?: number;
    wasm_enabled?: boolean;
  };
}
