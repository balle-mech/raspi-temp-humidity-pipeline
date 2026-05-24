import logging
import os
import time

from .sensor import IIOSensor
from .writer import DailyCSVWriter

_INTERVAL = int(os.environ.get("MEASUREMENT_INTERVAL_SEC", "300"))
_DATA_DIR = os.environ.get("DATA_DIR", "data/raw")
_LOG_FILE = os.environ.get("LOG_FILE", "data/logs/collector.log")
_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


def _setup_logging() -> logging.Logger:
    os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, _LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(_LOG_FILE),
        ],
    )
    return logging.getLogger(__name__)


def main() -> None:
    log = _setup_logging()

    device_path = os.environ.get("DEVICE0")
    if not device_path:
        log.error("DEVICE0 environment variable is not set.")
        raise SystemExit(1)

    sensor = IIOSensor(device_path)
    writer = DailyCSVWriter(_DATA_DIR)

    log.info("Collector started. device=%s interval=%ds output=%s", device_path, _INTERVAL, _DATA_DIR)

    while True:
        try:
            m = sensor.read()
            writer.write(m)
            log.info(
                "temp=%s°C humidity=%s%%",
                m.temperature_c if m.temperature_c is not None else "N/A",
                m.humidity_pct if m.humidity_pct is not None else "N/A",
            )
        except Exception as e:
            log.error("Measurement failed: %s", e)

        time.sleep(_INTERVAL)


if __name__ == "__main__":
    main()
