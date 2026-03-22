import json
import os
import time
from collections import defaultdict, deque
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, send_from_directory, session
from flask_compress import Compress
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import NullPool
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden, Conflict, HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
from logging_config import configure_logging
from validation import (
    validate_save_payload,
    validate_register_payload,
    validate_login_payload,
    validate_leaderboard_post_payload,
    validate_change_password_payload,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=None)
Compress(app)

app.secret_key = os.getenv('SECRET_KEY', 'dev-only-change-this')

app.config['SESSION_COOKIE_SECURE']    = True
app.config['SESSION_COOKIE_HTTPONLY']  = True
app.config['SESSION_COOKIE_SAMESITE']  = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

_db_url = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "pizza_clicker.db")}')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if not _db_url.startswith('sqlite'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'poolclass': NullPool}

db = SQLAlchemy(app)
configure_logging(app)




class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    nickname      = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, server_default=db.func.now())
    save              = db.relationship('Save',             backref='user', uselist=False, lazy=True, cascade='all, delete-orphan')
    leaderboard_entry = db.relationship('LeaderboardEntry', backref='user', uselist=False, lazy=True, cascade='all, delete-orphan')


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
    extra_data    = db.Column(db.Text, nullable=True, default='{}')


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
        db.session.rollback()
    try:
        with db.engine.connect() as _conn:
            _conn.execute(db.text("ALTER TABLE saves ADD COLUMN extra_data TEXT DEFAULT '{}'"))
            _conn.commit()
    except Exception:
        pass  # column already exists or table not yet created




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


@app.route('/api/register', methods=['POST'])
def register():
    _check_login_rate()
    data = validate_register_payload(get_json_body())
    if User.query.filter_by(nickname=data['nickname']).first():
        raise Conflict('Tato přezdívka je již obsazena.')
    user = User(
        nickname=data['nickname'],
        password_hash=generate_password_hash(data['password']),
    )
    db.session.add(user)
    db.session.commit()
    session.permanent = True
    session['user_id'] = user.id
    return jsonify({'ok': True, 'user': {'id': user.id, 'nickname': user.nickname}})


@app.route('/api/login', methods=['POST'])
def login():
    _check_login_rate()
    data = validate_login_payload(get_json_body())
    user = User.query.filter_by(nickname=data['nickname']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        raise Unauthorized('Špatná přezdívka nebo heslo.')
    session.permanent = True
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


_save_buckets: dict = defaultdict(deque)  
_SAVE_RATE_LIMIT = 35  
_SAVE_RATE_WINDOW = 1.0

def _check_save_rate(user_id):
    now = time.monotonic()
    bucket = _save_buckets[user_id]
    cutoff = now - _SAVE_RATE_WINDOW
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= _SAVE_RATE_LIMIT:
        raise Forbidden('Příliš mnoho požadavků. Zpomal prosím.')
    bucket.append(now)


# --- Brute-force ochrana loginu ---
_login_buckets: dict = defaultdict(deque)  # IP -> deque of monotonic timestamps
_LOGIN_RATE_LIMIT  = 10   # max pokusů
_LOGIN_RATE_WINDOW = 60.0 # za 60 sekund

def _check_login_rate():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
    now = time.monotonic()
    bucket = _login_buckets[ip]
    cutoff = now - _LOGIN_RATE_WINDOW
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= _LOGIN_RATE_LIMIT:
        raise Forbidden('Příliš mnoho pokusů o přihlášení. Zkus to znovu za minutu.')
    bucket.append(now)

@app.route('/api/save', methods=['GET'])
def get_save():
    user = require_auth()
    s = user.save
    if not s:
        return jsonify(None)
    extra = json.loads(s.extra_data or '{}')
    return jsonify({
        'pizzeriaName': s.pizzeria_name,
        'money':        s.money,
        'totalEarned':  s.total_earned,
        'clickValue':   s.click_value,
        'upgrades':     json.loads(s.upgrades),
        'lastSave':     s.last_save,
        'earnedAchievements': extra.get('earnedAchievements', {}),
        'totalClicks':  extra.get('totalClicks', 0),
        'streak':       extra.get('streak', 0),
        'lastLoginDate': extra.get('lastLoginDate', None),
        'prestigeLevel': extra.get('prestigeLevel', 0),
    })


@app.route('/api/save', methods=['POST'])
def post_save():
    user = require_auth()
    _check_save_rate(user.id)
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
    s.extra_data    = json.dumps({
        'earnedAchievements': save_data['earnedAchievements'],
        'totalClicks':        save_data['totalClicks'],
        'streak':             save_data['streak'],
        'lastLoginDate':      save_data['lastLoginDate'],
        'prestigeLevel':      save_data['prestigeLevel'],
    })
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/save', methods=['DELETE'])
def delete_save():
    user = require_auth()
    if user.save:
        db.session.delete(user.save)
        db.session.commit()
    return jsonify({'ok': True})


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



@app.route('/api/stats', methods=['GET'])
def get_stats():
    registered_users = db.session.query(db.func.count(User.id)).scalar()
    active_saves     = db.session.query(db.func.count(Save.id)).scalar()
    return jsonify({
        'registered_users': registered_users,
        'active_saves':     active_saves,
    })



@app.route('/api/profile', methods=['GET'])
def get_profile():
    user = require_auth()
    s = user.save
    upgrades_bought = 0
    if s:
        import json as _json
        upgrades_bought = sum(1 for v in _json.loads(s.upgrades).values() if v)
    return jsonify({
        'nickname':       user.nickname,
        'created_at':     user.created_at.isoformat() if user.created_at else None,
        'total_earned':   s.total_earned if s else 0,
        'money':          s.money        if s else 0,
        'upgrades_bought': upgrades_bought,
    })


@app.route('/api/profile/password', methods=['POST'])
def change_password():
    user = require_auth()
    data = validate_change_password_payload(get_json_body())
    if not check_password_hash(user.password_hash, data['old_password']):
        raise Forbidden('Staré heslo není správné.')
    user.password_hash = generate_password_hash(data['new_password'])
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/profile', methods=['DELETE'])
def delete_profile():
    user = require_auth()
    db.session.delete(user)
    db.session.commit()
    session.clear()
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
