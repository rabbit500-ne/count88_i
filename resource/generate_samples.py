"""サンプル局面データファイルを生成するスクリプト"""
import json
import os

# 終局まで60手の合法棋譜（検証済み）
# 2文字ずつで1手を表す
full_kifu = (
    "D3"  # 1
    "E3"  # 2
    "F4"  # 3
    "C5"  # 4
    "C4"  # 5
    "D2"  # 6
    "D6"  # 7
    "F5"  # 8
    "E6"  # 9
    "C3"  # 10
    "E2"  # 11
    "F3"  # 12
    "B4"  # 13
    "B5"  # 14
    "G4"  # 15
    "G5"  # 16
    "C6"  # 17
    "D7"  # 18
    "F6"  # 19
    "E7"  # 20
    "E1"  # 21
    "D1"  # 22
    "C2"  # 23
    "F2"  # 24
    "G3"  # 25
    "B3"  # 26
    "A4"  # 27
    "H4"  # 28
    "H5"  # 29
    "C1"  # 30
    "A5"  # 31
    "B6"  # 32
    "C7"  # 33
    "G6"  # 34
    "F7"  # 35
    "D8"  # 36
    "E8"  # 37
    "F1"  # 38
    "B2"  # 39
    "G2"  # 40
    "H3"  # 41
    "A3"  # 42
    "H6"  # 43
    "A6"  # 44
    "B7"  # 45
    "G7"  # 46
    "C8"  # 47
    "F8"  # 48
    "B1"  # 49
    "A2"  # 50
    "G1"  # 51
    "A7"  # 52
    "H2"  # 53
    "B8"  # 54
    "H7"  # 55
    "H1"  # 56
    "G8"  # 57
    "A1"  # 58
    "A8"  # 59
    "H8"  # 60
)

# オセロ初期局面（ビットボード）
# D4=白, E4=黒, D5=黒, E5=白
INITIAL_BLACK = (1 << 28) | (1 << 35)  # E4, D5
INITIAL_WHITE = (1 << 27) | (1 << 36)  # D4, E5

# 8方向のシフト量とマスク
DIRECTIONS = [
    (1, 0xFEFEFEFEFEFEFEFE),   # 右
    (-1, 0x7F7F7F7F7F7F7F7F),  # 左
    (8, 0xFFFFFFFFFFFFFF00),    # 下
    (-8, 0x00FFFFFFFFFFFFFF),   # 上
    (9, 0xFEFEFEFEFEFEFE00),   # 右下
    (-9, 0x007F7F7F7F7F7F7F),  # 左上
    (7, 0x7F7F7F7F7F7F7F00),   # 左下
    (-7, 0x00FEFEFEFEFEFEFE),  # 右上
]

def move_to_position(move: str) -> int:
    """座標をビット位置に変換"""
    col = ord(move[0].upper()) - ord('A')
    row = int(move[1]) - 1
    return row * 8 + col

def make_move(black: int, white: int, turn: str, move_bit: int) -> tuple:
    """手を打つ（石を反転させる）"""
    if turn == "black":
        player, opponent = black, white
    else:
        player, opponent = white, black
    
    new_player = player | move_bit
    to_flip = 0
    
    for shift, mask in DIRECTIONS:
        current = move_bit
        dir_to_flip = 0
        found_opponent = False
        
        for _ in range(8):
            if shift > 0:
                current = (current << shift) & mask
            else:
                current = (current >> -shift) & mask
            
            if current == 0:
                break
            
            if (opponent & current) != 0:
                found_opponent = True
                dir_to_flip |= current
            elif (player & current) != 0:
                if found_opponent:
                    to_flip |= dir_to_flip
                break
            else:
                break
    
    new_player |= to_flip
    new_opponent = opponent & ~to_flip
    next_turn = "white" if turn == "black" else "black"
    
    if turn == "black":
        return new_player, new_opponent, next_turn
    else:
        return new_opponent, new_player, next_turn

def bigint_to_hex(num: int) -> str:
    """整数を16進数文字列に変換"""
    return f"0x{num:016x}"

def replay_kifu(kifu: str) -> tuple:
    """棋譜を再生して最終局面を取得"""
    black = INITIAL_BLACK
    white = INITIAL_WHITE
    turn = "black"
    
    for i in range(0, len(kifu), 2):
        move = kifu[i:i+2]
        pos = move_to_position(move)
        move_bit = 1 << pos
        black, white, turn = make_move(black, white, turn, move_bit)
    
    return black, white, turn

# ファイル生成
output_dir = os.path.dirname(os.path.abspath(__file__))

for depth in range(1, 61):  # 1から60まで（終局まで）
    # depth手目までの棋譜を抽出（2文字×depth手）
    kifu = full_kifu[:depth * 2]
    
    # 棋譜を再生して局面を取得
    black, white, turn = replay_kifu(kifu)
    
    # 直近5手（最大10文字）を取得
    recent_moves = kifu[-10:] if len(kifu) >= 10 else kifu
    
    filename = f"D{depth:02d}_{recent_moves}.json"
    filepath = os.path.join(output_dir, filename)
    
    data = {
        "black": bigint_to_hex(black),
        "white": bigint_to_hex(white),
        "turn": turn,
        "kifu": kifu
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Created: {filename}")

print(f"\n合計 60 ファイルを生成しました。")
