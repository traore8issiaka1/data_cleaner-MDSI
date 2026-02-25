from flask import Flask, request, send_file, render_template, jsonify
import io
import os
from uuid import uuid4
from processing import *

# stockage en mémoire des DataFrames traités (démo uniquement)
storage = {}

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    """Traite le fichier, renvoie les statistiques, un aperçu HTML et un jeton."""
    file = request.files.get('file')
    if not file:
        return jsonify(error="Aucun fichier reçu"), 400
    try:
        df = read_file(file, file.filename)
        cleaned_df, stats = clean_dataframe(df)

        # conserver le résultat pour le téléchargement
        token = str(uuid4())
        storage[token] = cleaned_df

        preview_html = cleaned_df.head(20).to_html(classes='table table-striped', index=False)
        return jsonify(token=token, stats=stats, preview=preview_html)
    except Exception as e:
        return jsonify(error=str(e)), 400

@app.route('/download/<token>', methods=['GET'])
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

# garder la route /clean pour compatibilité
@app.route('/clean', methods=['POST'])
def clean():
    return process()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
