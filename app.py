from flask import Flask, request, send_file, render_template, jsonify, session
import json
import os
import sqlite3
import time
import uuid
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from processing import read_file, clean_dataframe, export_dataframe

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'data_cleaner.db')

# Temporary in-memory storage for cleaned DataFrames ready to be previewed/downloaded.
# Format: {file_id: {"user_id": int, "df": DataFrame, "base_name": str, "created_at": float}}
CLEANED_FILES = {}
CLEANED_TTL_SECONDS = 60 * 30


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS processed_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_filename TEXT NOT NULL,
            cleaned_filename TEXT NOT NULL,
            stats_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        '''
    )
    conn.commit()
    conn.close()


def get_current_user_id():
    return session.get('user_id')


def login_required_api(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not get_current_user_id():
            return jsonify({'error': 'Authentification requise'}), 401
        return fn(*args, **kwargs)

    return wrapper


def _cleanup_expired_files():
    now = time.time()
    expired_ids = [
        file_id
        for file_id, payload in CLEANED_FILES.items()
        if now - payload['created_at'] > CLEANED_TTL_SECONDS
    ]
    for file_id in expired_ids:
        CLEANED_FILES.pop(file_id, None)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/auth/register', methods=['POST'])
def auth_register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get('username') or '').strip()
    password = payload.get('password') or ''

    if len(username) < 3:
        return jsonify({'error': 'Le nom utilisateur doit contenir au moins 3 caracteres'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caracteres'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, generate_password_hash(password))
        )
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Ce nom utilisateur existe deja'}), 409

    conn.close()
    session['user_id'] = user_id
    session['username'] = username

    return jsonify({'message': 'Inscription reussie', 'username': username})


@app.route('/auth/login', methods=['POST'])
def auth_login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get('username') or '').strip()
    password = payload.get('password') or ''

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
    user = cur.fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Identifiants invalides'}), 401

    session['user_id'] = int(user['id'])
    session['username'] = user['username']
    return jsonify({'message': 'Connexion reussie', 'username': user['username']})


@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    session.clear()
    return jsonify({'message': 'Deconnexion reussie'})


@app.route('/auth/me', methods=['GET'])
def auth_me():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'authenticated': False})

    return jsonify({
        'authenticated': True,
        'user_id': user_id,
        'username': session.get('username')
    })


@app.route('/clean', methods=['POST'])
@login_required_api
def clean():
    try:
        file = request.files.get('file')
        if not file or not file.filename:
            return jsonify({'error': 'Aucun fichier recu'}), 400

        strategy = request.form.get('missing_strategy', 'mean')
        df = read_file(file.stream, file.filename)
        df_cleaned, stats = clean_dataframe(df, missing_strategy=strategy)

        _cleanup_expired_files()
        file_id = uuid.uuid4().hex
        base_name = os.path.splitext(file.filename)[0]
        cleaned_filename = f'cleaned_{base_name}'

        CLEANED_FILES[file_id] = {
            'user_id': get_current_user_id(),
            'df': df_cleaned,
            'base_name': cleaned_filename,
            'created_at': time.time(),
        }

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            '''
            INSERT INTO processed_files (user_id, original_filename, cleaned_filename, stats_json)
            VALUES (?, ?, ?, ?)
            ''',
            (
                get_current_user_id(),
                file.filename,
                cleaned_filename,
                json.dumps(stats)
            )
        )
        conn.commit()
        history_id = cur.lastrowid
        conn.close()

        return jsonify({
            'message': 'Nettoyage termine',
            'file_id': file_id,
            'history_id': history_id,
            'stats': stats,
            'default_filename': f'cleaned_{file.filename}',
        })
    except Exception as e:
        return jsonify({'error': f'Erreur de nettoyage: {str(e)}'}), 400


@app.route('/preview/<file_id>', methods=['GET'])
@login_required_api
def preview_cleaned(file_id):
    payload = CLEANED_FILES.get(file_id)
    if not payload:
        return jsonify({'error': 'Fichier traite introuvable ou expire'}), 404
    if payload['user_id'] != get_current_user_id():
        return jsonify({'error': 'Acces non autorise'}), 403

    try:
        limit = int(request.args.get('limit', 20))
    except ValueError:
        limit = 20

    limit = max(1, min(limit, 100))
    df = payload['df']
    preview_df = df.head(limit)

    return jsonify({
        'columns': list(preview_df.columns),
        'rows': preview_df.fillna('').astype(str).values.tolist(),
        'rows_total': int(len(df)),
        'rows_preview': int(len(preview_df)),
    })


@app.route('/download/<file_id>', methods=['GET'])
@login_required_api
def download_cleaned(file_id):
    payload = CLEANED_FILES.get(file_id)
    if not payload:
        return jsonify({'error': 'Fichier traite introuvable ou expire'}), 404
    if payload['user_id'] != get_current_user_id():
        return jsonify({'error': 'Acces non autorise'}), 403

    export_format = request.args.get('format', 'csv').lower()
    try:
        buffer, mimetype = export_dataframe(payload['df'], export_format)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    extension = 'xlsx' if export_format == 'xls' else export_format
    download_name = f"{payload['base_name']}.{extension}"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=download_name,
        mimetype=mimetype,
    )


@app.route('/history', methods=['GET'])
@login_required_api
def history():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        SELECT id, original_filename, cleaned_filename, stats_json, created_at
        FROM processed_files
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 50
        ''',
        (get_current_user_id(),)
    )
    rows = cur.fetchall()
    conn.close()

    items = []
    for row in rows:
        items.append({
            'id': int(row['id']),
            'original_filename': row['original_filename'],
            'cleaned_filename': row['cleaned_filename'],
            'stats': json.loads(row['stats_json']),
            'created_at': row['created_at']
        })

    return jsonify({'items': items})


init_db()

if __name__ == '__main__':
    app.run(debug=True)
