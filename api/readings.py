"""日次 CSV から、ある時刻より後の計測値を読む（Mac mini が差分だけ取りに来るため）。

旧フォーマット（Timestamp, Temperature (℃), Humidity (%)）と新フォーマットの両方を読む。
ファイル名の日付で、since より前の日のファイルは開かない。
"""

from __future__ import annotations

import csv
import re
from datetime import date, datetime
from pathlib import Path

_ALIASES = {
    "Timestamp": "timestamp",
    "Temperature (℃)": "temperature_c",
    "Humidity (%)": "humidity_pct",
}
_DAY = re.compile(r"(\d{4}-\d{2}-\d{2})")
DEFAULT_LIMIT = 5000


def _file_day(path: Path) -> date | None:
    m = _DAY.search(path.name)
    return date.fromisoformat(m.group(1)) if m else None


def _num(s: str | None) -> float | None:
    try:
        return float(s) if s not in (None, "") else None
    except ValueError:
        return None


def _rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = [_ALIASES.get(h.strip(), h.strip()) for h in next(reader, [])]
        if "timestamp" not in header:
            return
        idx = {k: header.index(k) for k in ("timestamp", "temperature_c", "humidity_pct") if k in header}
        for cells in reader:
            try:
                ts = datetime.strptime(cells[idx["timestamp"]].strip(), "%Y-%m-%d %H:%M:%S")
            except (IndexError, ValueError):
                continue  # 壊れた行・空行
            get = lambda k: cells[idx[k]] if k in idx and idx[k] < len(cells) else None  # noqa: E731
            yield ts, _num(get("temperature_c")), _num(get("humidity_pct"))


def read_since(data_dir: Path, since: datetime | None, limit: int = DEFAULT_LIMIT) -> tuple[list[dict], bool]:
    """since より後（since は含まない）の計測値を古い順に最大 limit 件。2つ目は続きがあるか。"""
    files = [p for p in Path(data_dir).rglob("*.csv") if since is None or (_file_day(p) or since.date()) >= since.date()]
    rows = sorted(r for p in files for r in _rows(p) if since is None or r[0] > since)
    out = [
        {"timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"), "temperature_c": t, "humidity_pct": h}
        for ts, t, h in rows[:limit]
    ]
    return out, len(rows) > limit


def latest(data_dir: Path) -> str | None:
    files = sorted(Path(data_dir).rglob("*.csv"), key=lambda p: (_file_day(p) or date.min, p.name))
    for p in reversed(files):
        rows = list(_rows(p))
        if rows:
            return max(rows)[0].strftime("%Y-%m-%d %H:%M:%S")
    return None
