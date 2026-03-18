import json
import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.exceptions import BadRequest, HTTPException
from logging_config import configure_logging
from validation import validate_leaderboard_payload, validate_save_payload

app = Flask(__name__, static_folder='.')

SAVE_FILE = os.path.join(os.path.dirname(__file__), 'save.json')
LEADERBOARD_FILE = os.path.join(os.path.dirname(__file__), 'leaderboard.json')


configure_logging(app)


def get_json_body():
    if not request.is_json:
        raise BadRequest('Request must use application/json content type.')

    try:
        data = request.get_json()
    except BadRequest as error:
        raise BadRequest('Request body must contain valid JSON.') from error

    if data is None:
        raise BadRequest('Request body must contain valid JSON.')

    return data


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
    save_data = validate_save_payload(get_json_body())
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
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
    leaderboard_data = validate_leaderboard_payload(get_json_body())
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(leaderboard_data, f, ensure_ascii=False, indent=2)
    return jsonify({'ok': True})


@app.errorhandler(HTTPException)
def handle_http_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'ok': False, 'error': error.description}), error.code
    return error.description, error.code


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.exception('Unexpected server error: %s', error)
    if request.path.startswith('/api/'):
        return jsonify({'ok': False, 'error': 'Internal server error'}), 500
    return 'Internal server error', 500

if __name__ == '__main__':
    debug_enabled = os.getenv('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes'}
    app.run(debug=debug_enabled)
