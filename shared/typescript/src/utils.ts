/** ユーティリティ関数 */

import { Position, Turn } from "./types";
import { INITIAL_BLACK, INITIAL_WHITE, BLACK } from "./constants";

/**
 * 初期局面を作成
 */
export function createInitialPosition(): Position {
  return {
    black: INITIAL_BLACK,
    white: INITIAL_WHITE,
    turn: BLACK,
  };
}

/**
 * ビットボード文字列を数値に変換
 */
export function bitboardStringToNumber(bitboard: string): number {
  if (bitboard.startsWith("0x") || bitboard.startsWith("0X")) {
    return parseInt(bitboard, 16);
  }
  return parseInt(bitboard, 16);
}

/**
 * 数値をビットボード文字列に変換
 */
export function numberToBitboardString(value: number): string {
  return `0x${value.toString(16).padStart(16, "0")}`;
}
