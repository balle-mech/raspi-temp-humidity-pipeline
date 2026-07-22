"""過去CSVに対してエアコンON判定を走らせ、精度を目視確認するためのCLI。

使い方(Pi 上で):
    python -m automation.backtest [data/raw] [日数]

1時間刻みで直近3時間窓を評価し、「エアコンONと推測される時間帯」を表示する。
実際のエアコン使用記憶と突き合わせて閾値(AC_MIN_SWING_C 等)を調整する。
"""

import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

from automation.detector import detect_cycling
from processor.data import load_data


def backtest(data_dir: str, days: int) -> list[tuple]:
    df = load_data(data_dir)
    if df.empty:
        return []
    temps = df.set_index("timestamp")["temperature_c"]
    end = temps.index.max()
    start = max(temps.index.min(), end - timedelta(days=days))
    results = []
    for ts in pd.date_range(start + timedelta(hours=3), end, freq="1h"):
        window = temps[ts - timedelta(hours=3): ts]
        d = detect_cycling(window)
        results.append((ts, d.cycling, d.swing_count))
    return results


def _print_intervals(results: list[tuple]) -> None:
    on_start = None
    prev_ts = None
    for ts, cycling, _ in results:
        if cycling and on_start is None:
            on_start = ts
        elif not cycling and on_start is not None:
            print(f"  {on_start:%m/%d %H:%M} 〜 {prev_ts:%m/%d %H:%M}  エアコンON推測")
            on_start = None
        prev_ts = ts
    if on_start is not None:
        print(f"  {on_start:%m/%d %H:%M} 〜 {prev_ts:%m/%d %H:%M}  エアコンON推測")


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    results = backtest(data_dir, days)
    if not results:
        print("データがありません。")
        sys.exit(1)
    hits = sum(1 for _, c, _ in results if c)
    print(f"評価点数: {len(results)}(1時間刻み)、ON判定: {hits}")
    _print_intervals(results)
