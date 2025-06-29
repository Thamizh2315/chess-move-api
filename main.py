from flask import Flask, request, jsonify
import chess
import time

app = Flask(__name__)

PIECE_VALUES = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9}
MAX_DEPTH = 6
MAX_TIME = 40

def evaluate_capture_score(board):
    score = 0
    for move in board.move_stack:
        if board.is_capture(move):
            captured = board.piece_at(move.to_square)
            if captured:
                score += PIECE_VALUES.get(captured.piece_type, 0)
    return score

def search_best_move(board, depth, start_time):
    if time.time() - start_time > MAX_TIME or depth == 0:
        return None, evaluate_capture_score(board)

    best_score = -1
    best_move = None
    for move in board.legal_moves:
        board.push(move)
        _, score = search_best_move(board, depth - 1, start_time)
        board.pop()
        if score > best_score:
            best_score = score
            if depth == MAX_DEPTH:
                best_move = move
    return best_move, best_score

def can_checkmate_in_6_moves(board, depth, start_time):
    if time.time() - start_time > MAX_TIME or depth == 0:
        return False
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            board.pop()
            return True
        if can_checkmate_in_6_moves(board, depth - 1, start_time):
            board.pop()
            return True
        board.pop()
    return False

def best_move_within_40s(fen):
    board = chess.Board(fen)
    start_time = time.time()
    if can_checkmate_in_6_moves(board, MAX_DEPTH, start_time):
        for move in board.legal_moves:
            board.push(move)
            if can_checkmate_in_6_moves(board, MAX_DEPTH - 1, start_time):
                board.pop()
                return move.uci()
            board.pop()
    best_move, _ = search_best_move(board, MAX_DEPTH, start_time)
    return best_move.uci() if best_move else None

@app.route('/suggest_move', methods=['POST'])
def suggest_move():
    data = request.get_json()
    fen = data.get('fen')
    if not fen:
        return jsonify({'error': 'FEN not provided'}), 400
    move = best_move_within_40s(fen)
    return jsonify({'fen': fen, 'move': move})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
