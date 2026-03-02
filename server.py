import json
import os
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.')

SAVE_FILE = os.path.join(os.path.dirname(__file__), 'save.json')
LEADERBOARD_FILE = os.path.join(os.path.dirname(__file__), 'leaderboard.json')


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)


@app.route('/api/save', methods=['GET'])
def get_save():
    if not os.path.exists(SAVE_FILE):
        return jsonify(None)
    with open(SAVE_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/api/save', methods=['POST'])
def post_save():
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(request.get_json(), f, ensure_ascii=False, indent=2)
    return jsonify({'ok': True})

@app.route('/api/save', methods=['DELETE'])
def delete_save():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
    return jsonify({'ok': True})


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return jsonify([])
    with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/api/leaderboard', methods=['POST'])
def post_leaderboard():
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(request.get_json(), f, ensure_ascii=False, indent=2)
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True)
