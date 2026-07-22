"""SwitchBot API v1.1 クライアント(標準ライブラリのみ)。

デバイスID の確認:
    python -m automation.switchbot devices
"""

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from urllib.request import Request, urlopen

_API_BASE = "https://api.switch-bot.com/v1.1"


def make_sign(token: str, secret: str, t: str, nonce: str) -> str:
    digest = hmac.new(
        secret.encode(), f"{token}{t}{nonce}".encode(), hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode()


def _headers(token: str, secret: str) -> dict:
    t = str(int(time.time() * 1000))
    nonce = str(uuid.uuid4())
    return {
        "Authorization": token,
        "sign": make_sign(token, secret, t, nonce),
        "t": t,
        "nonce": nonce,
        "Content-Type": "application/json; charset=utf8",
    }


def _credentials(token: str | None, secret: str | None) -> tuple[str, str]:
    token = token or os.environ.get("SWITCHBOT_TOKEN", "")
    secret = secret or os.environ.get("SWITCHBOT_SECRET", "")
    if not token or not secret:
        raise RuntimeError("SWITCHBOT_TOKEN / SWITCHBOT_SECRET が設定されていません。")
    return token, secret


def send_command(
    device_id: str,
    command: str,
    *,
    token: str | None = None,
    secret: str | None = None,
) -> dict:
    token, secret = _credentials(token, secret)
    body = json.dumps(
        {"command": command, "parameter": "default", "commandType": "command"}
    ).encode()
    req = Request(
        f"{_API_BASE}/devices/{device_id}/commands",
        data=body,
        headers=_headers(token, secret),
        method="POST",
    )
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def turn_off(device_id: str, **kwargs) -> dict:
    return send_command(device_id, "turnOff", **kwargs)


def list_devices(*, token: str | None = None, secret: str | None = None) -> dict:
    token, secret = _credentials(token, secret)
    req = Request(f"{_API_BASE}/devices", headers=_headers(token, secret))
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())["body"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "devices":
        body = list_devices()
        print("--- 赤外線リモコン(エアコンはここから deviceId を選ぶ) ---")
        for d in body.get("infraredRemoteList", []):
            print(f"{d['deviceId']}  {d['remoteType']}  {d['deviceName']}")
        print("--- 物理デバイス ---")
        for d in body.get("deviceList", []):
            print(f"{d['deviceId']}  {d.get('deviceType', '?')}  {d.get('deviceName', '')}")
    else:
        print(__doc__)
