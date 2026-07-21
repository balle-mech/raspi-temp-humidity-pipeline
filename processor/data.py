import glob
import os

import pandas as pd

_DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "../data/raw"))

_COLUMN_ALIASES = {
    "Timestamp": "timestamp",
    "Temperature (℃)": "temperature_c",
    "Humidity (%)": "humidity_pct",
}


def load_data(data_dir: str = _DATA_DIR) -> pd.DataFrame:
    files = glob.glob(os.path.join(data_dir, "**", "*.csv"), recursive=True)
    dfs = []
    for path in sorted(files):
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
            df.columns = [c.strip() for c in df.columns]
            df = df.rename(columns=_COLUMN_ALIASES)
            if "timestamp" in df.columns:
                dfs.append(df[["timestamp", "temperature_c", "humidity_pct"]])
        except Exception:
            pass
    if not dfs:
        return pd.DataFrame(columns=["timestamp", "temperature_c", "humidity_pct"])
    combined = pd.concat(dfs, ignore_index=True)
    combined["timestamp"] = pd.to_datetime(combined["timestamp"], errors="coerce")
    combined = (
        combined.dropna(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    return combined


def resample_for_display(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) < 2:
        return df
    days = (df.index[-1] - df.index[0]).total_seconds() / 86400
    if days <= 1:
        rule = "5min"
    elif days <= 3:
        rule = "30min"
    elif days <= 7:
        rule = "1h"
    elif days <= 30:
        rule = "6h"
    else:
        rule = "1D"
    return df.resample(rule).mean().dropna(how="all")


def rolling_median(df: pd.DataFrame, window: str = "1h") -> pd.DataFrame:
    """時刻インデックス済みデータにローリング中央値を掛けてセンサーノイズを抑える。

    DHT-11 は単発読みの外れ値が出やすいため、平均ではなく中央値を使う。
    """
    if df.empty:
        return df
    return df.rolling(window).median()


def x_format(days: float) -> str:
    if days <= 1:
        return "%H:%M"
    elif days <= 7:
        return "%m/%d(%a) %H時"
    elif days <= 30:
        return "%m/%d"
    else:
        return "%Y/%m"


def compute_temp_domain(df: pd.DataFrame) -> list[float]:
    return [float(df["temperature_c"].min()) - 0.5, float(df["temperature_c"].max()) + 0.5]


def compute_hum_domain(df: pd.DataFrame) -> list[float]:
    return [float(df["humidity_pct"].min()) - 5.0, float(df["humidity_pct"].max()) + 5.0]
