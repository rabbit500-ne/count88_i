/**
 * 棋譜の合法性を検証するスクリプト
 */
import { getLegalMoves, makeMove, bigIntToBitboardString } from '../api-server/src/static/js/othello-core.js';

// 検証対象の棋譜（終局まで60手）
const full_kifu = 
  "D3" +  // 1
  "E3" +  // 2
  "F4" +  // 3
  "C5" +  // 4
  "C4" +  // 5
  "D2" +  // 6
  "D6" +  // 7
  "F5" +  // 8
  "E6" +  // 9
  "C3" +  // 10
  "E2" +  // 11
  "F3" +  // 12
  "B4" +  // 13
  "B5" +  // 14
  "G4" +  // 15
  "G5" +  // 16
  "C6" +  // 17
  "D7" +  // 18
  "F6" +  // 19
  "E7" +  // 20
  "E1" +  // 21
  "D1" +  // 22
  "C2" +  // 23
  "F2" +  // 24
  "G3" +  // 25
  "B3" +  // 26
  "A4" +  // 27
  "H4" +  // 28
  "H5" +  // 29
  "C1" +  // 30
  "A5" +  // 31
  "B6" +  // 32
  "C7" +  // 33
  "G6" +  // 34
  "F7" +  // 35
  "D8" +  // 36
  "E8" +  // 37
  "F1" +  // 38
  "B2" +  // 39
  "G2" +  // 40
  "H3" +  // 41
  "A3" +  // 42
  "H6" +  // 43
  "A6" +  // 44
  "B7" +  // 45
  "G7" +  // 46
  "C8" +  // 47
  "F8" +  // 48
  "B1" +  // 49
  "A2" +  // 50
  "G1" +  // 51
  "A7" +  // 52
  "H2" +  // 53
  "B8" +  // 54
  "H7" +  // 55
  "H1" +  // 56
  "G8" +  // 57
  "A1" +  // 58
  "A8" +  // 59
  "H8";   // 60

// オセロの初期局面
// ビットボード表現（A1=bit0, H8=bit63）
// 標準配置: D4=白, E4=黒, D5=黒, E5=白
// D4 = col3, row3 = bit 3*8+3 = bit27
// E4 = col4, row3 = bit 3*8+4 = bit28
// D5 = col3, row4 = bit 4*8+3 = bit35
// E5 = col4, row4 = bit 4*8+4 = bit36
const INITIAL_BLACK = 1n << 28n | 1n << 35n;  // E4, D5
const INITIAL_WHITE = 1n << 27n | 1n << 36n;  // D4, E5

// 座標をビット位置に変換
function moveToPosition(move) {
  const col = move[0].toUpperCase().charCodeAt(0) - 'A'.charCodeAt(0);  // 0-7
  const row = parseInt(move[1]) - 1;  // 0-7
  return row * 8 + col;
}

// ビット位置を座標に変換
function positionToMove(pos) {
  const col = String.fromCharCode('A'.charCodeAt(0) + (pos % 8));
  const row = Math.floor(pos / 8) + 1;
  return `${col}${row}`;
}

// 合法手のリストを取得
function getLegalMovesList(black, white, turn) {
  const legalMoves = getLegalMoves(black, white, turn);
  const moves = [];
  for (let pos = 0n; pos < 64n; pos++) {
    if ((legalMoves & (1n << pos)) !== 0n) {
      moves.push(positionToMove(Number(pos)));
    }
  }
  return moves;
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

// 棋譜の検証
function validateKifu(kifu) {
  let black = bigIntToBitboardString(INITIAL_BLACK);
  let white = bigIntToBitboardString(INITIAL_WHITE);
  let turn = 'black';
  
  console.log('=== 初期局面 ===');
  printBoard(black, white);
  console.log();
  
  const moves = [];
  for (let i = 0; i < kifu.length; i += 2) {
    moves.push(kifu.slice(i, i + 2));
  }
  
  let invalidMoves = [];
  
  for (let i = 0; i < moves.length; i++) {
    const move = moves[i];
    const moveNum = i + 1;
    const pos = moveToPosition(move);
    const moveBit = 1n << BigInt(pos);
    
    // 合法手を取得
    const legalMoves = getLegalMoves(black, white, turn);
    const legalMovesList = getLegalMovesList(black, white, turn);
    
    // この手が合法かチェック
    const isLegal = (legalMoves & moveBit) !== 0n;
    
    if (!isLegal) {
      console.log(`❌ ${moveNum}手目: ${move} (${turn}) - 不正な手!`);
      console.log(`   合法手: [${legalMovesList.join(', ')}]`);
      console.log();
      console.log(`=== ${moveNum}手目直前の局面 ===`);
      printBoard(black, white);
      invalidMoves.push({ moveNum, move, turn, legalMoves: legalMovesList });
      
      // パスが必要だったかチェック
      if (legalMoves === 0n) {
        console.log(`   → 合法手がありません。パスが必要でした。`);
        // パスして相手番に
        turn = turn === 'black' ? 'white' : 'black';
        // この手をもう一度検証
        const newLegalMoves = getLegalMoves(black, white, turn);
        const isLegalAfterPass = (newLegalMoves & moveBit) !== 0n;
        if (isLegalAfterPass) {
          console.log(`   → パス後、${turn}の手として ${move} は合法です。`);
          const result = makeMove(black, white, turn, moveBit);
          black = result.black;
          white = result.white;
          turn = result.turn;
          continue;
        }
      }
      break;
    }
    
    // 手を実行
    const result = makeMove(black, white, turn, moveBit);
    black = result.black;
    white = result.white;
    turn = result.turn;
    
    console.log(`✓ ${moveNum}手目: ${move}`);
  }
  
  if (invalidMoves.length === 0) {
    console.log();
    console.log('=== 49手目後の局面 ===');
    printBoard(black, white);
    console.log();
    console.log(`✅ 全 ${moves.length} 手が合法です！`);
    console.log(`最終局面:`);
    console.log(`  black: ${black}`);
    console.log(`  white: ${white}`);
    console.log(`  turn: ${turn}`);
  } else {
    console.log();
    console.log(`❌ ${invalidMoves.length} 個の不正な手が見つかりました。`);
  }
  
  return invalidMoves;
}

// 実行
console.log('=== 棋譜検証開始 ===');
console.log(`棋譜: ${full_kifu}`);
console.log(`手数: ${full_kifu.length / 2} 手`);
console.log();

validateKifu(full_kifu);
