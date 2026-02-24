import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import io
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler


def read_file(file_stream, filename):
    """Charge un fichier en DataFrame quel que soit le format supporté."""
    # pandas sait déjà convertir selon le suffixe
    if filename.endswith('.csv'):
        return pd.read_csv(file_stream)
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        return pd.read_excel(file_stream)
    elif filename.endswith('.json'):
        return pd.read_json(file_stream)
    elif filename.endswith('.xml'):
        try:
            return pd.read_xml(file_stream, parser='lxml')
        except Exception:
            try:
                file_stream.seek(0)
            except Exception:
                pass
            return pd.read_xml(file_stream, parser='etree')
    else:
        raise ValueError("Format non supporté")


def handle_missing(df, strategy='mean'):
    """Retourne une copie du DataFrame avec les valeurs manquantes traitées.

    La stratégie peut être : 'drop', 'mean', 'median', 'mode' ou autre (aucune action).
    """
    if strategy == 'drop':
        return df.dropna()
    elif strategy == 'mean':
        return df.fillna(df.mean(numeric_only=True))
    elif strategy == 'median':
        return df.fillna(df.median(numeric_only=True))
    elif strategy == 'mode':
        return df.fillna(df.mode().iloc[0])
    else:
        return df

def remove_duplicates(df):
    """Supprime les doublons et retourne le DataFrame sans doublons."""
    return df.drop_duplicates()

def remove_outliers_iqr(df):
    """Supprime les outliers selon la règle de l'IQR.

    Retourne un tuple (df_filtered, count_removed).
    """
    df2 = df.copy()
    num_cols = df2.select_dtypes(include=np.number).columns
    if len(num_cols) == 0:
        return df2, 0
    Q1 = df2[num_cols].quantile(0.25)
    Q3 = df2[num_cols].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    mask = ((df2[num_cols] >= lower) & (df2[num_cols] <= upper)).all(axis=1)
    filtered = df2[mask]
    removed = len(df2) - len(filtered)
    return filtered, removed

def normalize(df):
    """Normalise les colonnes numériques en 0‑1 et renvoie le DataFrame.

    Retourne également le nombre de colonnes normalisées pour les statistiques.
    """
    scaler = MinMaxScaler()
    cols = df.select_dtypes(include=np.number).columns
    if len(cols) > 0:
        df[cols] = scaler.fit_transform(df[cols])
    return df, len(cols)


def clean_dataframe(df, missing_strategy='mean'):
    """Applique toute la chaîne de nettoyage et renvoie (df_cleaned, stats)."""
    stats = {}
    stats['rows_before'] = len(df)
    stats['columns'] = len(df.columns)
    stats['missing_values_before'] = int(df.isna().sum().sum())

    # traitement des valeurs manquantes
    df_missing = handle_missing(df, missing_strategy)
    stats['missing_values_after'] = int(df_missing.isna().sum().sum())
    stats['missing_removed'] = stats['missing_values_before'] - stats['missing_values_after']

    # doublons
    dup_before = df_missing.duplicated().sum()
    df_dup = remove_duplicates(df_missing)
    dup_after = df_dup.duplicated().sum()
    stats['duplicates_removed'] = int(dup_before - dup_after)

    # outliers
    df_out, out_removed = remove_outliers_iqr(df_dup)
    stats['outliers_removed'] = int(out_removed)

    # normalisation
    df_norm, norm_cols = normalize(df_out)
    stats['normalized_columns'] = norm_cols

    stats['rows_after'] = len(df_norm)

    # qualité simple : pourcentages de suppressions
    score = 100.0
    if stats['rows_before'] > 0:
        score -= (stats['missing_removed'] / stats['rows_before']) * 20
        score -= (stats['duplicates_removed'] / stats['rows_before']) * 20
        score -= (stats['outliers_removed'] / stats['rows_before']) * 20
    stats['quality_score'] = round(max(score, 0), 2)

    return df_norm, stats


def export_dataframe(df, fmt: str):
    """Génère un BytesIO contenant le DataFrame dans le format demandé."""
    buf = io.BytesIO()
    fmt_lower = fmt.lower()
    if fmt_lower == 'csv':
        df.to_csv(buf, index=False)
        mimetype = 'text/csv'
    elif fmt_lower in ('xlsx', 'xls'):
        df.to_excel(buf, index=False, engine='openpyxl')
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif fmt_lower == 'json':
        buf.write(df.to_json(orient='records', date_format='iso').encode('utf-8'))
        mimetype = 'application/json'
    elif fmt_lower == 'xml':
        buf.write(df.to_xml(index=False).encode('utf-8'))
        mimetype = 'application/xml'
    else:
        raise ValueError(f"Format d'export inconnu: {fmt}")
    buf.seek(0)
    return buf, mimetype
