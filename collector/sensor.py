import os
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Measurement:
    timestamp: datetime
    temperature_c: float | None
    humidity_pct: float | None


class IIOSensor:
    """Linux IIO サブシステム (sysfs) 経由でセンサー値を読み取る。

    デバイスパス例: /sys/bus/iio/devices/iio:device0
    """

    def __init__(self, device_path: str):
        self.device_path = device_path

    def _read_milliunit(self, filename: str) -> int | None:
        path = os.path.join(self.device_path, filename)
        try:
            with open(path) as f:
                return int(f.readline())
        except (OSError, ValueError):
            return None

    def read(self) -> Measurement:
        temp_raw = self._read_milliunit("in_temp_input")
        humidity_raw = self._read_milliunit("in_humidityrelative_input")
        return Measurement(
            timestamp=datetime.now(),
            temperature_c=temp_raw / 1000 if temp_raw is not None else None,
            humidity_pct=humidity_raw / 1000 if humidity_raw is not None else None,
        )
