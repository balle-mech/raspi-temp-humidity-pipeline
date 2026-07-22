"""人感センサー(PIR)の最終検知時刻をステートファイルで管理する。"""

import os
from datetime import datetime

_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def record_motion(path, when: datetime) -> None:
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        f.write(when.strftime(_TIME_FORMAT))
    os.replace(tmp, path)


def last_motion(path) -> datetime | None:
    try:
        with open(path) as f:
            return datetime.strptime(f.read().strip(), _TIME_FORMAT)
    except (OSError, ValueError):
        return None
