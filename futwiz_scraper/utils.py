import os, datetime as dt, pandas as pd

def now_iso():
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def append_csv(path: str, df: pd.DataFrame):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = not os.path.exists(path)
    df.to_csv(path, index=False, mode="a", encoding="utf-8-sig", header=header)
    return path

def month_path(dir_: str, prefix: str):
    yyyymm = dt.datetime.utcnow().strftime("%Y%m")
    return os.path.join(dir_, f"{prefix}_{yyyymm}.csv")
