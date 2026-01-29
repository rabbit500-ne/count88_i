#!/usr/bin/env node
/**
 * DFS処理時間計測スクリプト
 * 
 * 使用方法:
 *   node dfs-benchmark.mjs                     # サンプル局面でテスト
 *   node dfs-benchmark.mjs --depth 10          # D10の局面を生成してテスト
 *   node dfs-benchmark.mjs --file ../../../../../resource/D01_F5.json  # ファイルから局面を読み込み
 *   node dfs-benchmark.mjs --black 0x... --white 0x... --turn black  # 局面を指定
 *   node dfs-benchmark.mjs --json '{"black":"0x...","white":"0x...","turn":"black"}'
 * 
 * オプション:
 *   --file PATH     : 局面をJSONファイルから読み込み
 *   --depth N       : 初期局面からBFSでN手進めた局面でDFSを実行
 *   --black HEX     : 黒石のビットボード（16進数）
 *   --white HEX     : 白石のビットボード（16進数）
 *   --turn TURN     : 手番 (black | white)
 *   --json JSON     : 局面をJSON形式で指定
 *   --iterations N  : 繰り返し回数（デフォルト: 1）
 *   --verbose       : 詳細出力
 */

import fs from "fs";
import path from "path";
import { computeDFS, computeBFS, getLegalMoves, bigIntToBitboardString } from "../othello-core.js";

// 初期局面（オセロの開始位置）
const INITIAL_POSITION = {
  black: "0x0000000810000000",  // D5, E4
  white: "0x0000001008000000",  // D4, E5
  turn: "black"
};

// コマンドライン引数のパース
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    file: null,
    depth: null,
    black: null,
    white: null,
    turn: null,
    json: null,
    iterations: 1,
    verbose: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === "--file" && args[i + 1]) {
      options.file = args[++i];
    } else if (arg === "--depth" && args[i + 1]) {
      options.depth = parseInt(args[++i], 10);
    } else if (arg === "--black" && args[i + 1]) {
      options.black = args[++i];
    } else if (arg === "--white" && args[i + 1]) {
      options.white = args[++i];
    } else if (arg === "--turn" && args[i + 1]) {
      options.turn = args[++i];
    } else if (arg === "--json" && args[i + 1]) {
      options.json = args[++i];
    } else if (arg === "--iterations" && args[i + 1]) {
      options.iterations = parseInt(args[++i], 10);
    } else if (arg === "--verbose" || arg === "-v") {
      options.verbose = true;
    } else if (arg === "--help" || arg === "-h") {
      console.log(`
DFS処理時間計測スクリプト

使用方法:
  node dfs-benchmark.mjs                     # サンプル局面でテスト（浅い深さ）
  node dfs-benchmark.mjs --file ../../../../../resource/D01_F5.json  # ファイルから局面を読み込み
  node dfs-benchmark.mjs --depth 10          # D10の局面を生成してテスト
  node dfs-benchmark.mjs --black 0x... --white 0x... --turn black
  node dfs-benchmark.mjs --json '{"black":"0x...","white":"0x...","turn":"black"}'

オプション:
  --file PATH     : 局面をJSONファイルから読み込み（resource/D01_F5.json など）
  --depth N       : 初期局面からBFSでN手進めた局面の1つでDFSを実行
  --black HEX     : 黒石のビットボード（16進数）
  --white HEX     : 白石のビットボード（16進数）
  --turn TURN     : 手番 (black | white)
  --json JSON     : 局面をJSON形式で指定
  --iterations N  : 繰り返し回数（デフォルト: 1）
  --verbose, -v   : 詳細出力
  --help, -h      : ヘルプを表示
`);
      process.exit(0);
    }
  }

  return options;
}

// 盤面を視覚化
function visualizeBoard(black, white) {
  const blackBits = BigInt(black.startsWith("0x") ? black : `0x${black}`);
  const whiteBits = BigInt(white.startsWith("0x") ? white : `0x${white}`);
  
  let board = "  a b c d e f g h\n";
  for (let row = 0; row < 8; row++) {
    board += `${row + 1} `;
    for (let col = 0; col < 8; col++) {
      const pos = BigInt(row * 8 + col);
      const bit = 1n << pos;
      if ((blackBits & bit) !== 0n) {
        board += "● ";
      } else if ((whiteBits & bit) !== 0n) {
        board += "○ ";
      } else {
        board += ". ";
      }
    }
    board += "\n";
  }
  return board;
}

// BFSで指定深さまで進めた局面を取得
function getPositionAtDepth(depth) {
  const result = computeBFS({
    position: INITIAL_POSITION,
    depth: depth
  });
  
  const childPositions = result.find(r => r.label === "child_positions")?.value || [];
  if (childPositions.length === 0) {
    throw new Error(`No positions found at depth ${depth}`);
  }
  
  // 最初の局面を返す
  return childPositions[0].position;
}

// DFSベンチマーク実行
function runBenchmark(position, iterations, verbose) {
  console.log("=".repeat(60));
  console.log("DFS ベンチマーク");
  console.log("=".repeat(60));
  
  if (verbose) {
    console.log("\n【局面】");
    console.log(visualizeBoard(position.black, position.white));
    console.log(`Black: ${position.black}`);
    console.log(`White: ${position.white}`);
    console.log(`Turn: ${position.turn}`);
    
    const legalMoves = getLegalMoves(position.black, position.white, position.turn);
    const moveCount = legalMoves.toString(2).split("1").length - 1;
    console.log(`合法手数: ${moveCount}`);
  }
  
  console.log(`\n【実行】 iterations=${iterations}`);
  
  const times = [];
  let lastResult = null;
  
  for (let i = 0; i < iterations; i++) {
    const startTime = performance.now();
    
    const result = computeDFS({
      task_type: "DFS",
      position: position
    });
    
    const endTime = performance.now();
    const elapsedMs = endTime - startTime;
    times.push(elapsedMs);
    lastResult = result;
    
    if (verbose || iterations === 1) {
      const gameCount = result.find(r => r.label === "game_count")?.value || "0";
      console.log(`  [${i + 1}/${iterations}] ${elapsedMs.toFixed(3)} ms (棋譜数: ${gameCount})`);
    }
  }
  
  // 統計
  console.log("\n【結果】");
  const gameCount = lastResult.find(r => r.label === "game_count")?.value || "0";
  console.log(`棋譜数: ${gameCount}`);
  
  if (iterations > 1) {
    const avgMs = times.reduce((a, b) => a + b, 0) / times.length;
    const minMs = Math.min(...times);
    const maxMs = Math.max(...times);
    
    console.log(`\n【統計】`);
    console.log(`  平均: ${avgMs.toFixed(3)} ms`);
    console.log(`  最小: ${minMs.toFixed(3)} ms`);
    console.log(`  最大: ${maxMs.toFixed(3)} ms`);
  } else {
    console.log(`処理時間: ${times[0].toFixed(3)} ms`);
  }
  
  console.log("=".repeat(60));
  
  return {
    position,
    gameCount,
    times,
    avgMs: times.reduce((a, b) => a + b, 0) / times.length,
  };
}

// メイン関数
function main() {
  const options = parseArgs();
  let position;
  
  // 局面の決定
  if (options.file) {
    // ファイルから読み込み
    try {
      const filePath = path.resolve(options.file);
      const content = fs.readFileSync(filePath, "utf-8");
      position = JSON.parse(content);
      console.log(`局面ファイル読み込み: ${options.file}\n`);
    } catch (e) {
      console.error(`Error: ファイルの読み込みに失敗しました: ${options.file}`);
      console.error(e.message);
      process.exit(1);
    }
  } else if (options.json) {
    // JSON形式で指定
    try {
      position = JSON.parse(options.json);
    } catch (e) {
      console.error("Error: Invalid JSON format");
      process.exit(1);
    }
  } else if (options.black && options.white && options.turn) {
    // 個別指定
    position = {
      black: options.black,
      white: options.white,
      turn: options.turn,
    };
  } else if (options.depth !== null) {
    // BFSで指定深さまで進めた局面を使用
    console.log(`初期局面からBFSで ${options.depth} 手進めた局面を生成中...`);
    position = getPositionAtDepth(options.depth);
    console.log(`局面生成完了\n`);
  } else {
    // デフォルト: D50相当の終局間近サンプル局面（終局まで約10-14手）
    console.log("【注意】引数なしで実行: D50相当のサンプル局面を使用します");
    console.log("任意の局面をテストするには --json オプションを使用してください\n");
    
    // D50相当のサンプル局面（盤面の約78%が埋まっている状態）
    // 終局まで約10-14手で、数秒〜数十秒で完了する想定
    position = {
      black: "0x007E7E3E1E0E0600",  // 約25石
      white: "0xFF81817D61717938",  // 約25石、空き約14マス
      turn: "black"
    };
  }
  
  // ベンチマーク実行
  runBenchmark(position, options.iterations, options.verbose);
}

main();
