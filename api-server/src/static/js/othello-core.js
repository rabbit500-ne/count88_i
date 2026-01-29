/**
 * オセロ棋譜カウント - 共通コアロジック
 * 
 * ブラウザ（client.js）とNode.js（評価スクリプト）の両方から使用可能
 */

// ビットボード操作ユーティリティ
export const bitboardStringToBigInt = (str) => {
  if (str.startsWith("0x") || str.startsWith("0X")) {
    return BigInt(str);
  }
  return BigInt(`0x${str}`);
};

export const bigIntToBitboardString = (num) => {
  // 64bit整数を扱うため、BigIntを使用
  return `0x${num.toString(16).padStart(16, "0")}`;
};

// 8方向のマスク（盤面端を考慮）
const DIRECTIONS = [
  { shift: 1, mask: 0xFEFEFEFEFEFEFEFEn },   // 右
  { shift: -1, mask: 0x7F7F7F7F7F7F7F7Fn },  // 左
  { shift: 8, mask: 0xFFFFFFFFFFFFFF00n },    // 下
  { shift: -8, mask: 0x00FFFFFFFFFFFFFFn },   // 上
  { shift: 9, mask: 0xFEFEFEFEFEFEFE00n },   // 右下
  { shift: -9, mask: 0x007F7F7F7F7F7F7Fn },  // 左上
  { shift: 7, mask: 0x7F7F7F7F7F7F7F00n },   // 左下
  { shift: -7, mask: 0x00FEFEFEFEFEFEFEn },  // 右上
];

/**
 * オセロの合法手計算（ビットボード操作）
 * @param {string} black - 黒石のビットボード（16進数文字列）
 * @param {string} white - 白石のビットボード（16進数文字列）
 * @param {string} turn - 手番 ("black" | "white")
 * @returns {bigint} 合法手のビットボード
 */
export const getLegalMoves = (black, white, turn) => {
  const player = turn === "black" ? bitboardStringToBigInt(black) : bitboardStringToBigInt(white);
  const opponent = turn === "black" ? bitboardStringToBigInt(white) : bitboardStringToBigInt(black);
  const empty = ~(player | opponent) & 0xFFFFFFFFFFFFFFFFn;
  
  let legalMoves = 0n;

  // 各空きマスについて、8方向に相手の石を挟めるかチェック
  for (let pos = 0n; pos < 64n; pos++) {
    const bit = 1n << pos;
    if ((empty & bit) === 0n) continue; // 空きマスでない

    for (const dir of DIRECTIONS) {
      let current = bit;
      let foundOpponent = false;

      // 隣接マスをチェック
      for (let i = 0; i < 8; i++) {
        if (dir.shift > 0) {
          current = (current << BigInt(dir.shift)) & dir.mask;
        } else {
          current = (current >> BigInt(-dir.shift)) & dir.mask;
        }
        
        if (current === 0n) break;
        
        if ((opponent & current) !== 0n) {
          foundOpponent = true;
        } else if ((player & current) !== 0n) {
          if (foundOpponent) {
            legalMoves |= bit;
          }
          break;
        } else {
          break;
        }
      }
    }
  }

  return legalMoves;
};

/**
 * 手を打つ（石を反転させる）
 * @param {string} black - 黒石のビットボード（16進数文字列）
 * @param {string} white - 白石のビットボード（16進数文字列）
 * @param {string} turn - 手番 ("black" | "white")
 * @param {bigint} move - 着手位置のビット
 * @returns {{black: string, white: string, turn: string}} 新しい局面
 */
export const makeMove = (black, white, turn, move) => {
  const player = turn === "black" ? bitboardStringToBigInt(black) : bitboardStringToBigInt(white);
  const opponent = turn === "black" ? bitboardStringToBigInt(white) : bitboardStringToBigInt(black);
  const moveBit = BigInt(move);
  
  let newPlayer = player | moveBit;
  let newOpponent = opponent;
  let toFlip = 0n;

  // 各方向に石を反転
  for (const dir of DIRECTIONS) {
    let current = moveBit;
    let foundOpponent = false;
    let dirToFlip = 0n;

    for (let i = 0; i < 8; i++) {
      if (dir.shift > 0) {
        current = (current << BigInt(dir.shift)) & dir.mask;
      } else {
        current = (current >> BigInt(-dir.shift)) & dir.mask;
      }
      
      if (current === 0n) break;
      
      if ((opponent & current) !== 0n) {
        foundOpponent = true;
        dirToFlip |= current;
      } else if ((player & current) !== 0n) {
        if (foundOpponent) {
          toFlip |= dirToFlip;
        }
        break;
      } else {
        break;
      }
    }
  }

  // 石を反転
  newPlayer |= toFlip;
  newOpponent &= ~toFlip;

  // 手番を交代
  const nextTurn = turn === "black" ? "white" : "black";

  if (turn === "black") {
    return {
      black: bigIntToBitboardString(newPlayer),
      white: bigIntToBitboardString(newOpponent),
      turn: nextTurn,
    };
  } else {
    return {
      black: bigIntToBitboardString(newOpponent),
      white: bigIntToBitboardString(newPlayer),
      turn: nextTurn,
    };
  }
};

/**
 * DFSアルゴリズム（深さ優先探索で終局までカウント）
 * @param {object} task - タスク情報 { position: { black, white, turn } }
 * @returns {Array<{label: string, value: string}>} 結果
 */
export const computeDFS = (task) => {
  const startPosition = task.position;
  
  // 再帰的なDFS関数
  const dfs = (black, white, turn, passCount) => {
    const legalMoves = getLegalMoves(black, white, turn);
    
    if (legalMoves === 0n) {
      // 合法手がない場合（パス）
      if (passCount === 1) {
        // 2連続パス → ゲーム終了、1棋譜としてカウント
        return 1n;
      } else {
        // パス（手番交代して続行）
        const nextTurn = turn === "black" ? "white" : "black";
        return dfs(black, white, nextTurn, 1);
      }
    }
    
    // 各合法手を再帰的に探索
    let total = 0n;
    for (let pos = 0n; pos < 64n; pos++) {
      const moveBit = 1n << pos;
      if ((legalMoves & moveBit) === 0n) continue;
      
      const nextPosition = makeMove(black, white, turn, moveBit);
      total += dfs(
        nextPosition.black,
        nextPosition.white,
        nextPosition.turn,
        0
      );
    }
    
    return total;
  };
  
  // DFS実行
  const gameCount = dfs(
    startPosition.black,
    startPosition.white,
    startPosition.turn,
    0
  );
  
  // 結果を返す（BigIntを文字列に変換）
  return [{ label: "game_count", value: gameCount.toString() }];
};

/**
 * BFSアルゴリズム（幅優先探索で指定深さまで展開）
 * @param {object} task - タスク情報 { position: { black, white, turn }, depth: number }
 * @returns {Array<{label: string, value: any}>} 結果
 */
export const computeBFS = (task) => {
  const startPosition = task.position;
  const targetDepth = task.depth || 6;

  // 局面を文字列化してキーとして使用（重複排除用）
  const positionKey = (pos) => `${pos.black}:${pos.white}:${pos.turn}`;

  // 深さごとのキュー
  let queue = [{ position: startPosition, passCount: 0 }];
  const resultPositions = new Map(); // 局面 -> 到達パス数（BigInt）

  for (let depth = 0; depth < targetDepth; depth++) {
    const nextQueue = [];

    for (const { position, passCount } of queue) {
      const legalMoves = getLegalMoves(position.black, position.white, position.turn);

      if (legalMoves === 0n) {
        // 合法手がない場合（パス）
        if (passCount === 1) {
          // 2連続パス → ゲーム終了（この深さで終了）
          const key = positionKey(position);
          if (!resultPositions.has(key)) {
            resultPositions.set(key, 0n);
          }
          resultPositions.set(key, resultPositions.get(key) + 1n);
          continue;
        } else {
          // パス（手番交代、深さは進める）
          const passPosition = {
            black: position.black,
            white: position.white,
            turn: position.turn === "black" ? "white" : "black",
          };
          nextQueue.push({ position: passPosition, passCount: 1 });
          continue;
        }
      }

      // 各合法手を展開
      for (let pos = 0n; pos < 64n; pos++) {
        const moveBit = 1n << pos;
        if ((legalMoves & moveBit) === 0n) continue;

        const nextPosition = makeMove(position.black, position.white, position.turn, moveBit);
        nextQueue.push({ position: nextPosition, passCount: 0 });
      }
    }

    queue = nextQueue;
  }

  // 目標深さに到達した局面を結果に追加
  for (const { position } of queue) {
    const key = positionKey(position);
    if (!resultPositions.has(key)) {
      resultPositions.set(key, 0n);
    }
    resultPositions.set(key, resultPositions.get(key) + 1n);
  }

  // 結果をフォーマット
  const childPositions = [];
  for (const [key, pathCount] of resultPositions.entries()) {
    const [black, white, turn] = key.split(":");
    childPositions.push({
      position: {
        black,
        white,
        turn,
      },
      // JSON互換のため文字列化（多倍長整数）
      path_count: pathCount.toString(),
    });
  }

  return [{ label: "child_positions", value: childPositions }];
};

/**
 * タスクタイプに応じて計算を実行
 * @param {object} task - タスク情報
 * @returns {Array} 結果
 */
export const compute = (task) => {
  if (task.task_type === "DFS") {
    return computeDFS(task);
  }
  return computeBFS(task);
};
