(() => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const getClientId = () => {
    const key = "count88_client_id";
    let v = localStorage.getItem(key);
    if (!v) {
      v = (globalThis.crypto && crypto.randomUUID) ? crypto.randomUUID() : `client-${Date.now()}-${Math.random()}`;
      localStorage.setItem(key, v);
    }
    return v;
  };

  const el = (id) => document.getElementById(id);

  const setText = (id, text) => {
    const e = el(id);
    if (e) e.textContent = String(text);
  };

  const appendLog = (msg) => {
    const log = el("client-log");
    if (!log) return;
    const line = `[${new Date().toISOString()}] ${msg}\n`;
    log.textContent = (line + log.textContent).slice(0, 8000);
  };

  const clientId = getClientId();

  const state = {
    running: false,
    backoffMs: 200,
  };

  // ビットボード操作ユーティリティ
  const bitboardStringToBigInt = (str) => {
    if (str.startsWith("0x") || str.startsWith("0X")) {
      return BigInt(str);
    }
    return BigInt(`0x${str}`);
  };

  const bigIntToBitboardString = (num) => {
    // 64bit整数を扱うため、BigIntを使用
    return `0x${num.toString(16).padStart(16, "0")}`;
  };

  // オセロの合法手計算（ビットボード操作）
  const getLegalMoves = (black, white, turn) => {
    const player = turn === "black" ? bitboardStringToBigInt(black) : bitboardStringToBigInt(white);
    const opponent = turn === "black" ? bitboardStringToBigInt(white) : bitboardStringToBigInt(black);
    const empty = ~(player | opponent) & 0xFFFFFFFFFFFFFFFFn;
    
    let legalMoves = 0n;
    
    // 8方向のマスク（盤面端を考慮）
    const directions = [
      { shift: 1, mask: 0xFEFEFEFEFEFEFEFEn },   // 右
      { shift: -1, mask: 0x7F7F7F7F7F7F7F7Fn },  // 左
      { shift: 8, mask: 0xFFFFFFFFFFFFFF00n },    // 下
      { shift: -8, mask: 0x00FFFFFFFFFFFFFFn },   // 上
      { shift: 9, mask: 0xFEFEFEFEFEFEFE00n },   // 右下
      { shift: -9, mask: 0x007F7F7F7F7F7F7Fn },  // 左上
      { shift: 7, mask: 0x7F7F7F7F7F7F7F00n },   // 左下
      { shift: -7, mask: 0x00FEFEFEFEFEFEFEn },  // 右上
    ];

    // 各空きマスについて、8方向に相手の石を挟めるかチェック
    for (let pos = 0n; pos < 64n; pos++) {
      const bit = 1n << pos;
      if ((empty & bit) === 0n) continue; // 空きマスでない

      for (const dir of directions) {
        let current = bit;
        let foundOpponent = false;
        let toFlip = 0n;

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
            toFlip |= current;
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

  // 手を打つ（石を反転させる）
  const makeMove = (black, white, turn, move) => {
    const player = turn === "black" ? bitboardStringToBigInt(black) : bitboardStringToBigInt(white);
    const opponent = turn === "black" ? bitboardStringToBigInt(white) : bitboardStringToBigInt(black);
    const moveBit = BigInt(move);
    
    let newPlayer = player | moveBit;
    let newOpponent = opponent;
    let toFlip = 0n;

    // 8方向のマスク
    const directions = [
      { shift: 1, mask: 0xFEFEFEFEFEFEFEFEn },
      { shift: -1, mask: 0x7F7F7F7F7F7F7F7Fn },
      { shift: 8, mask: 0xFFFFFFFFFFFFFF00n },
      { shift: -8, mask: 0x00FFFFFFFFFFFFFFn },
      { shift: 9, mask: 0xFEFEFEFEFEFEFE00n },
      { shift: -9, mask: 0x007F7F7F7F7F7F7Fn },
      { shift: 7, mask: 0x7F7F7F7F7F7F7F00n },
      { shift: -7, mask: 0x00FEFEFEFEFEFEFEn },
    ];

    // 各方向に石を反転
    for (const dir of directions) {
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

  // DFSアルゴリズム（深さ優先探索で終局までカウント）
  const computeDFS = (task) => {
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

  // BFSアルゴリズム（幅優先探索で指定深さまで展開）
  const computeBFS = (task) => {
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

  const computeStub = async (task) => {
    if (task.task_type === "DFS") {
      // DFSタスクの場合は実際の計算を実行
      return computeDFS(task);
    }
    // BFSタスクの場合は実際の計算を実行
    return computeBFS(task);
  };

  const postResult = async (task, taskAnswer, computationTimeSec) => {
    const payload = {
      task_id: String(task.task_id),
      task_type: task.task_type,
      task_answer: taskAnswer,
      computation_time: computationTimeSec,
      client_id: clientId,
      client_info: {
        user_agent: navigator.userAgent,
        cpu_cores: navigator.hardwareConcurrency ?? null,
        wasm_enabled: typeof WebAssembly === "object",
      },
    };

    const res = await fetch("/api/v1/result", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Client-ID": clientId,
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`result failed: ${res.status} ${text}`);
    }
    return await res.json();
  };

  const loop = async () => {
    setText("client-status", "running");
    while (state.running) {
      try {
        const t0 = performance.now();
        const res = await fetch("/api/v1/task", {
          headers: { "X-Client-ID": clientId },
        });

        if (res.status === 204) {
          setText("client-status", "no_task");
          state.backoffMs = Math.min(2000, state.backoffMs + 100);
          await sleep(state.backoffMs);
          continue;
        }

        if (!res.ok) {
          const text = await res.text().catch(() => "");
          appendLog(`task fetch error: ${res.status} ${text}`);
          setText("client-status", "error");
          state.backoffMs = Math.min(5000, state.backoffMs * 2);
          await sleep(state.backoffMs);
          continue;
        }

        const task = await res.json();
        setText("last-task", task.task_id);
        setText("client-status", `got_${task.task_type}`);

        const taskAnswer = await computeStub(task);
        const computationTimeSec = (performance.now() - t0) / 1000.0;

        const result = await postResult(task, taskAnswer, computationTimeSec);
        appendLog(`accepted: task_id=${task.task_id} result_id=${result.result_id} next=${result.next_task_available}`);
        state.backoffMs = 200;

        // 次タスクが無さそうでも、少し待って再取得（UIでもキュー状況が見える）
        await sleep(result.next_task_available ? 50 : 500);
      } catch (e) {
        appendLog(String(e));
        setText("client-status", "error");
        state.backoffMs = Math.min(5000, state.backoffMs * 2);
        await sleep(state.backoffMs);
      }
    }
    setText("client-status", "stopped");
  };

  const init = () => {
    setText("client-id", clientId);
    setText("client-status", "idle");

    const startBtn = el("btn-start");
    const stopBtn = el("btn-stop");
    if (startBtn) {
      startBtn.addEventListener("click", () => {
        if (state.running) return;
        state.running = true;
        startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
        appendLog("start");
        void loop();
      });
    }
    if (stopBtn) {
      stopBtn.addEventListener("click", () => {
        state.running = false;
        stopBtn.disabled = true;
        if (startBtn) startBtn.disabled = false;
        appendLog("stop");
      });
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

