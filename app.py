from flask import Flask, request, send_file, render_template, jsonify, redirect, url_for, session, g
import io
import os
import pandas as pd
from uuid import uuid4
from processing import *
from models import db, User, CleanupLog
from functools import wraps

# stockage en mémoire des DataFrames traités (éviter pour production)
storage = {}

# database configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data_cleaner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')

# initialize extensions
db.init_app(app)
with app.app_context():
    db.create_all()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.before_request
def load_user():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/clean', methods=['POST'])
def clean():
    """Ancienne route : renvoie directement un CSV pour compatibilité.

    Elle utilise désormais la même logique que /process.
    """
    file = request.files.get('file')
    if not file:
        return "Aucun fichier reçu", 400
    try:
        df = read_file(file, file.filename)
        cleaned_df, stats = clean_dataframe(df)
        buffer = io.BytesIO()
        cleaned_df.to_csv(buffer, index=False)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="cleaned.csv")
    except Exception as e:
        return f"Erreur : {str(e)}", 400

@app.route('/process', methods=['POST'])
@login_required
def process():
    """Traite le fichier, retourne des statistiques et un aperçu HTML.

    Le dossier nettoyé est conservé en mémoire avec un jeton.
    """
    file = request.files.get('file')
    if not file:
        return jsonify(error="Aucun fichier reçu"), 400
    try:
        df = read_file(file, file.filename)
        cleaned_df, stats = clean_dataframe(df)
        # record the operation for future analysis / IA training
        if g.user:
            log = CleanupLog(user_id=g.user.id, stats=stats, filename=file.filename)
            db.session.add(log)
            db.session.commit()
        token = str(uuid4())
        storage[token] = cleaned_df
        preview_html = cleaned_df.head(20).to_html(classes='table table-striped', index=False)
        return jsonify(token=token, stats=stats, preview=preview_html)
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.route('/download/<token>', methods=['GET'])
@login_required
def download(token):
    fmt = request.args.get('format', 'csv')
    df = storage.get(token)
    if df is None:
        return "Token invalide ou expiré", 404
    try:
        buffer, mimetype = export_dataframe(df, fmt)
        filename = f"cleaned.{fmt}"
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)
    except Exception as e:
        return f"Erreur d'export : {e}", 400



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template('register.html', error='Tous les champs sont requis')
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Ce nom existe déjà')
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        return render_template('login.html', error='Identifiants invalides')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
