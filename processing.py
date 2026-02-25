import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler

def read_file(file_stream, filename):
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
    return df.drop_duplicates()

def remove_outliers_iqr(df):
    df2 = df.copy()
    num_cols = df2.select_dtypes(include=np.number).columns
    if len(num_cols) == 0:
        return df2
    Q1 = df2[num_cols].quantile(0.25)
    Q3 = df2[num_cols].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    mask = ((df2[num_cols] >= lower) & (df2[num_cols] <= upper)).all(axis=1)
    return df2[mask]

def normalize(df):
    scaler = MinMaxScaler()
    cols = df.select_dtypes(include=np.number).columns
    df[cols] = scaler.fit_transform(df[cols])
    return df
