from flask import Flask, request, send_file, render_template
import io
import os
import pandas as pd
from processing import *

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clean', methods=['POST'])
def clean():
    try:
        file = request.files['file']
        if not file:
            return "Aucun fichier reçu", 400
        
        df = read_file(file, file.filename)

        df = handle_missing(df, 'mean')
        df = remove_duplicates(df)
        df = remove_outliers_iqr(df)
        df = normalize(df)

        buffer = io.BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name="cleaned.csv")
    except Exception as e:
        return f"Erreur : {str(e)}", 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
