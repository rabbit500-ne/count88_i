/**
 * 合法手のみで構成された終局までの棋譜を生成するスクリプト
 */
import { getLegalMoves, makeMove, bigIntToBitboardString } from '../api-server/src/static/js/othello-core.js';

// オセロの初期局面
const INITIAL_BLACK = 1n << 28n | 1n << 35n;  // E4, D5
const INITIAL_WHITE = 1n << 27n | 1n << 36n;  // D4, E5

// ビット位置を座標に変換
function positionToMove(pos) {
  const col = String.fromCharCode('A'.charCodeAt(0) + (pos % 8));
  const row = Math.floor(pos / 8) + 1;
  return `${col}${row}`;
}

// 合法手のリストを取得（ビット位置の配列）
function getLegalMovePositions(black, white, turn) {
  const legalMoves = getLegalMoves(black, white, turn);
  const positions = [];
  for (let pos = 0n; pos < 64n; pos++) {
    if ((legalMoves & (1n << pos)) !== 0n) {
      positions.push(Number(pos));
    }
  }
  return positions;
}

// 盤面を表示
function printBoard(black, white) {
  const blackBigInt = typeof black === 'string' ? BigInt(black) : black;
  const whiteBigInt = typeof white === 'string' ? BigInt(white) : white;
  
  console.log('  A B C D E F G H');
  for (let row = 0; row < 8; row++) {
    let line = `${row + 1} `;
    for (let col = 0; col < 8; col++) {
      const pos = row * 8 + col;
      const bit = 1n << BigInt(pos);
      if ((blackBigInt & bit) !== 0n) {
        line += '● ';
      } else if ((whiteBigInt & bit) !== 0n) {
        line += '○ ';
      } else {
        line += '. ';
      }
    }
    console.log(line);
  }
}

// 石の数をカウント
function countStones(black, white) {
  const blackBigInt = typeof black === 'string' ? BigInt(black) : black;
  const whiteBigInt = typeof white === 'string' ? BigInt(white) : white;
  
  let blackCount = 0;
  let whiteCount = 0;
  for (let i = 0n; i < 64n; i++) {
    if ((blackBigInt & (1n << i)) !== 0n) blackCount++;
    if ((whiteBigInt & (1n << i)) !== 0n) whiteCount++;
  }
  return { blackCount, whiteCount };
}

// 終局まで棋譜を生成
function generateKifu() {
  let black = bigIntToBitboardString(INITIAL_BLACK);
  let white = bigIntToBitboardString(INITIAL_WHITE);
  let turn = 'black';
  
  const kifuMoves = [];
  let passCount = 0;
  let moveNumber = 0;
  
  console.log('=== 棋譜生成開始 ===\n');
  console.log('初期局面:');
  printBoard(black, white);
  console.log();
  
  while (passCount < 2) {
    const legalPositions = getLegalMovePositions(black, white, turn);
    
    if (legalPositions.length === 0) {
      // パス
      console.log(`${moveNumber + 1}. ${turn === 'black' ? '黒' : '白'}: パス`);
      passCount++;
      turn = turn === 'black' ? 'white' : 'black';
      continue;
    }
    
    passCount = 0;
    
    // 合法手の中から選択（ここでは最初の合法手を選択）
    // より自然な棋譜にするため、中央寄りの手を優先
    const centerDistance = (pos) => {
      const col = pos % 8;
      const row = Math.floor(pos / 8);
      return Math.abs(col - 3.5) + Math.abs(row - 3.5);
    };
    
    // 中央に近い手を優先
    legalPositions.sort((a, b) => centerDistance(a) - centerDistance(b));
    
    const selectedPos = legalPositions[0];
    const moveStr = positionToMove(selectedPos);
    const moveBit = 1n << BigInt(selectedPos);
    
    kifuMoves.push(moveStr);
    moveNumber++;
    
    // 手を実行
    const result = makeMove(black, white, turn, moveBit);
    black = result.black;
    white = result.white;
    
    console.log(`${moveNumber}. ${turn === 'black' ? '黒' : '白'}: ${moveStr}`);
    
    turn = result.turn;
  }
  
  // 終局
  console.log('\n=== 終局 ===\n');
  printBoard(black, white);
  
  const { blackCount, whiteCount } = countStones(black, white);
  console.log(`\n結果: 黒 ${blackCount} - ${whiteCount} 白`);
  
  if (blackCount > whiteCount) {
    console.log('黒の勝ち！');
  } else if (whiteCount > blackCount) {
    console.log('白の勝ち！');
  } else {
    console.log('引き分け！');
  }
  
  const kifuString = kifuMoves.join('');
  console.log(`\n手数: ${kifuMoves.length}手`);
  console.log(`\n棋譜: ${kifuString}`);
  
  // Python形式で出力
  console.log('\n=== Python形式 ===');
  console.log('full_kifu = (');
  kifuMoves.forEach((move, i) => {
    console.log(`    "${move}"  # ${i + 1}`);
  });
  console.log(')');
  
  console.log(`\n最終局面:`);
  console.log(`  black: "${black}"`);
  console.log(`  white: "${white}"`);
  console.log(`  turn: "${turn}"`);
  
  return { kifuMoves, kifuString, finalBlack: black, finalWhite: white };
}

// 実行
generateKifu();
