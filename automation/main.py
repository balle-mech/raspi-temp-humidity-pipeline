"""エアコン消し忘れ検出・自動OFFサービス。

温度CSVの周期変動からエアコンONを推測し、人感センサーが長時間
無反応なら SwitchBot 経由で OFF を送る。AUTOMATION_DRY_RUN=true
(デフォルト)の間はログ出力のみで送信しない。
"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

from automation import presence, switchbot
from automation.detector import detect_cycling
from automation.rules import decide
from processor.data import load_data

_DATA_DIR = os.environ.get("DATA_DIR", "data/raw")
_STATE_DIR = os.environ.get("STATE_DIR", "data/state")
_LOG_FILE = os.environ.get("AUTOMATION_LOG_FILE", "data/logs/automation.log")
_INTERVAL = int(os.environ.get("AUTOMATION_INTERVAL_SEC", "600"))
_WINDOW_HOURS = float(os.environ.get("AC_DETECT_WINDOW_HOURS", "3"))
_MIN_AMPLITUDE = float(os.environ.get("AC_MIN_SWING_C", "0.8"))
_MIN_SWINGS = int(os.environ.get("AC_MIN_SWINGS", "4"))
_NO_MOTION_HOURS = float(os.environ.get("NO_MOTION_HOURS", "12"))
_COOLDOWN_HOURS = float(os.environ.get("COOLDOWN_HOURS", "3"))
_DRY_RUN = os.environ.get("AUTOMATION_DRY_RUN", "true").lower() != "false"
_PIR_GPIO = os.environ.get("PIR_GPIO")
_DEVICE_ID = os.environ.get("SWITCHBOT_AIRCON_DEVICE_ID", "")

_LAST_MOTION_FILE = os.path.join(_STATE_DIR, "last_motion")
_LAST_ACTION_FILE = os.path.join(_STATE_DIR, "last_aircon_off")


def _setup_logging() -> logging.Logger:
    os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(_LOG_FILE)],
    )
    return logging.getLogger(__name__)


def _start_pir_watcher(log: logging.Logger) -> None:
    """PIR センサーの検知を last_motion ステートファイルに記録する。

    PIR_GPIO 未設定またはハードなし環境では presence データが生成されず、
    rules.decide が安全側(何もしない)に倒れる。
    """
    if not _PIR_GPIO:
        log.warning("PIR_GPIO 未設定のため人感監視は無効(自動OFFは発動しません)")
        return
    try:
        from gpiozero import MotionSensor
    except ImportError:
        log.error("gpiozero が見つかりません。pip install gpiozero してください。")
        return
    sensor = MotionSensor(int(_PIR_GPIO))
    sensor.when_motion = lambda: presence.record_motion(_LAST_MOTION_FILE, datetime.now())
    log.info("PIR 監視開始 GPIO=%s", _PIR_GPIO)


def _recent_temps(now: datetime) -> pd.Series:
    df = load_data(_DATA_DIR)
    if df.empty:
        return pd.Series(dtype=float)
    df = df[df["timestamp"] >= now - timedelta(hours=_WINDOW_HOURS)]
    return df.set_index("timestamp")["temperature_c"]


def run_once(log: logging.Logger, now: datetime | None = None) -> None:
    now = now or datetime.now()
    detection = detect_cycling(
        _recent_temps(now), min_amplitude_c=_MIN_AMPLITUDE, min_swings=_MIN_SWINGS
    )
    decision = decide(
        ac_cycling=detection.cycling,
        last_motion=presence.last_motion(_LAST_MOTION_FILE),
        last_action=presence.last_motion(_LAST_ACTION_FILE),
        now=now,
        no_motion_hours=_NO_MOTION_HOURS,
        cooldown_hours=_COOLDOWN_HOURS,
    )
    log.info("swings=%d action=%s reason=%s", detection.swing_count, decision.action, decision.reason)

    if decision.action != "turn_off":
        return
    if _DRY_RUN:
        log.info("[DRY RUN] エアコンOFFを送信するところでした(AUTOMATION_DRY_RUN=false で有効化)")
        return
    if not _DEVICE_ID:
        log.error("SWITCHBOT_AIRCON_DEVICE_ID 未設定のため送信できません")
        return
    result = switchbot.turn_off(_DEVICE_ID)
    presence.record_motion(_LAST_ACTION_FILE, now)  # クールダウン起点を記録
    log.info("エアコンOFF送信 statusCode=%s", result.get("statusCode"))


def main() -> None:
    log = _setup_logging()
    log.info(
        "automation 開始 dry_run=%s interval=%ds window=%.1fh no_motion=%.1fh",
        _DRY_RUN, _INTERVAL, _WINDOW_HOURS, _NO_MOTION_HOURS,
    )
    _start_pir_watcher(log)
    while True:
        try:
            run_once(log)
        except Exception as e:
            log.error("評価失敗: %s", e)
        time.sleep(_INTERVAL)


if __name__ == "__main__":
    main()
