from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from collections import defaultdict
import random

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MOVES = ["グー", "チョキ", "パー"]
COUNTER_MOVES = {"グー": "パー", "チョキ": "グー", "パー": "チョキ"}
player_history = []
results = []

def build_transition_matrix(moves, order=3):
    matrix = defaultdict(lambda: defaultdict(int))
    for i in range(len(moves) - order):
        state = tuple(moves[i:i + order])
        next_move = moves[i + order]
        matrix[state][next_move] += 1
    return matrix

def predict_next_move(moves, transition_matrix, order=3):
    if len(moves) < order:
        return random.choice(MOVES)
    state = tuple(moves[-order:])
    next_moves = transition_matrix.get(state, {})
    return max(next_moves, key=next_moves.get) if next_moves else random.choice(MOVES)

def judge(player, computer):
    if player == computer:
        return "引き分け"
    elif (player == "グー" and computer == "チョキ") or \
         (player == "チョキ" and computer == "パー") or \
         (player == "パー" and computer == "グー"):
        return "勝ち"
    else:
        return "負け"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/play', methods=['POST'])
def play():
    data = request.get_json()
    player_move = data['move']
    matrix = build_transition_matrix(player_history)
    ai_move = COUNTER_MOVES.get(predict_next_move(player_history, matrix), random.choice(MOVES))
    result = judge(player_move, ai_move)
    player_history.append(player_move)
    results.append({'player': player_move, 'ai': ai_move, 'result': result})

    win_count = sum(1 for r in results if r['result'] == '勝ち')
    draw_count = sum(1 for r in results if r['result'] == '引き分け')
    loss_count = sum(1 for r in results if r['result'] == '負け')
    total = len(results)
    win_rate = round((win_count / (total - draw_count)) * 100, 2) if total - draw_count else 0

    return jsonify({
        'player': player_move,
        'ai': ai_move,
        'result': result,
        'stats': {
            'total': total,
            'wins': win_count,
            'draws': draw_count,
            'losses': loss_count,
            'win_rate': f"{win_rate}%"
        }
    })

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    for file in files:
        df = pd.read_excel(file)
        moves = df['player'].tolist()
        player_history.extend(moves)
    return jsonify({'message': 'ファイルを読み込みました', 'total_loaded': len(player_history)})

if __name__ == '__main__':
    app.run(debug=True)
