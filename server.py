import json
import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import NullPool
from werkzeug.exceptions import BadRequest, Unauthorized, Conflict, HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
from logging_config import configure_logging
from validation import (
    validate_save_payload,
    validate_register_payload,
    validate_login_payload,
    validate_leaderboard_post_payload,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=None)

app.secret_key = os.getenv('SECRET_KEY', 'dev-only-change-this')

_db_url = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "pizza_clicker.db")}')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if not _db_url.startswith('sqlite'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'poolclass': NullPool}

db = SQLAlchemy(app)
configure_logging(app)


# --- Models ---

class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    nickname      = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, server_default=db.func.now())
    save              = db.relationship('Save',             backref='user', uselist=False, lazy=True)
    leaderboard_entry = db.relationship('LeaderboardEntry', backref='user', uselist=False, lazy=True)


class Save(db.Model):
    __tablename__ = 'saves'
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    pizzeria_name = db.Column(db.String(30), nullable=False, default='Moje Pizzerie')
    money         = db.Column(db.Float, nullable=False, default=0)
    total_earned  = db.Column(db.Float, nullable=False, default=0)
    click_value   = db.Column(db.Float, nullable=False, default=1)
    upgrades      = db.Column(db.Text, nullable=False, default='{}')
    last_save     = db.Column(db.BigInteger, nullable=False, default=0)


class LeaderboardEntry(db.Model):
    __tablename__ = 'leaderboard'
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    name    = db.Column(db.String(30), nullable=False)
    pps     = db.Column(db.Float, nullable=False, default=0)
    total   = db.Column(db.Float, nullable=False, default=0)


with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        import sys
        print(f'[STARTUP] db.create_all() failed: {e}', file=sys.stderr)


# --- Helpers ---

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


def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return db.session.get(User, user_id)


def require_auth():
    user = get_current_user()
    if not user:
        raise Unauthorized('Musíš být přihlášen.')
    return user


# --- Static routes ---

@app.route('/')
def index():
    return send_from_directory(os.path.join(BASE_DIR, 'public'), 'index.html')

@app.route('/css/<path:path>')
def css_files(path):
    return send_from_directory(os.path.join(BASE_DIR, 'src', 'css'), path)

@app.route('/js/<path:path>')
def js_files(path):
    return send_from_directory(os.path.join(BASE_DIR, 'src', 'js'), path)

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(os.path.join(BASE_DIR, 'public'), path)


# --- Auth endpoints ---

@app.route('/api/register', methods=['POST'])
def register():
    data = validate_register_payload(get_json_body())
    if User.query.filter_by(nickname=data['nickname']).first():
        raise Conflict('Tato přezdívka je již obsazena.')
    user = User(
        nickname=data['nickname'],
        password_hash=generate_password_hash(data['password']),
    )
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({'ok': True, 'user': {'id': user.id, 'nickname': user.nickname}})


@app.route('/api/login', methods=['POST'])
def login():
    data = validate_login_payload(get_json_body())
    user = User.query.filter_by(nickname=data['nickname']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        raise Unauthorized('Špatná přezdívka nebo heslo.')
    session['user_id'] = user.id
    return jsonify({'ok': True, 'user': {'id': user.id, 'nickname': user.nickname}})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'ok': True})


@app.route('/api/me', methods=['GET'])
def me():
    user = get_current_user()
    if not user:
        raise Unauthorized('Nejsi přihlášen.')
    return jsonify({'ok': True, 'user': {'id': user.id, 'nickname': user.nickname}})


# --- Save endpoints ---

@app.route('/api/save', methods=['GET'])
def get_save():
    user = require_auth()
    s = user.save
    if not s:
        return jsonify(None)
    return jsonify({
        'pizzeriaName': s.pizzeria_name,
        'money':        s.money,
        'totalEarned':  s.total_earned,
        'clickValue':   s.click_value,
        'upgrades':     json.loads(s.upgrades),
        'lastSave':     s.last_save,
    })


@app.route('/api/save', methods=['POST'])
def post_save():
    user = require_auth()
    save_data = validate_save_payload(get_json_body())
    s = user.save
    if not s:
        s = Save(user_id=user.id)
        db.session.add(s)
    s.pizzeria_name = save_data['pizzeriaName']
    s.money         = save_data['money']
    s.total_earned  = save_data['totalEarned']
    s.click_value   = save_data['clickValue']
    s.upgrades      = json.dumps(save_data['upgrades'])
    s.last_save     = save_data['lastSave']
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/save', methods=['DELETE'])
def delete_save():
    user = require_auth()
    if user.save:
        db.session.delete(user.save)
        db.session.commit()
    return jsonify({'ok': True})


# --- Leaderboard endpoints ---

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    entries = LeaderboardEntry.query.order_by(LeaderboardEntry.total.desc()).limit(10).all()
    return jsonify([{'name': e.name, 'pps': e.pps, 'total': e.total} for e in entries])


@app.route('/api/leaderboard', methods=['POST'])
def post_leaderboard():
    user = require_auth()
    data = validate_leaderboard_post_payload(get_json_body())
    display_name = user.save.pizzeria_name if user.save else user.nickname
    entry = user.leaderboard_entry
    if not entry:
        entry = LeaderboardEntry(user_id=user.id)
        db.session.add(entry)
    entry.name  = display_name
    entry.pps   = data['pps']
    entry.total = data['total']
    db.session.commit()
    return jsonify({'ok': True})


# --- Error handlers ---

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
