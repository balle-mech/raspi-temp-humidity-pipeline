import csv
from datetime import date
from pathlib import Path

from .sensor import Measurement

_HEADER = ["timestamp", "temperature_c", "humidity_pct"]


class DailyCSVWriter:
    """日付をまたぐと自動的に新しいファイルに切り替える CSV ライター。

    出力ファイル名: <output_dir>/YYYY/MM/temp_humidity_YYYY-MM-DD.csv
    """

    def __init__(self, output_dir: str):
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._current_date: date | None = None
        self._current_path: Path | None = None

    def _path_for(self, d: date) -> Path:
        subdir = self._dir / d.strftime("%Y") / d.strftime("%m")
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir / f"temp_humidity_{d.isoformat()}.csv"

    def write(self, m: Measurement) -> None:
        today = m.timestamp.date()
        if today != self._current_date:
            self._current_date = today
            self._current_path = self._path_for(today)
            if not self._current_path.exists():
                with open(self._current_path, "w", newline="") as f:
                    csv.writer(f).writerow(_HEADER)

        with open(self._current_path, "a", newline="") as f:  # type: ignore[arg-type]
            csv.writer(f).writerow([
                m.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "" if m.temperature_c is None else m.temperature_c,
                "" if m.humidity_pct is None else m.humidity_pct,
            ])
