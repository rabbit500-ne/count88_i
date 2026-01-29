/**
 * count88 ブラウザクライアント
 * 
 * タスク取得 → 計算（DFS/BFS） → 結果送信 を繰り返す
 */
import { compute } from "./othello-core.js";

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

      // 共通モジュールを使用して計算
      const taskAnswer = compute(task);
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
