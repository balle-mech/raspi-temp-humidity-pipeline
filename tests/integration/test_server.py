"""api.server: 読み取り専用の HTTP API。実際にポートを開いて確かめる。"""

import json
import threading
import urllib.error
import urllib.request

import pytest

from api.server import make_server


@pytest.fixture
def base(tmp_path):
    p = tmp_path / "2026" / "11" / "temp_humidity_2026-11-15.csv"
    p.parent.mkdir(parents=True)
    p.write_text("timestamp,temperature_c,humidity_pct\n2026-11-15 00:00:00,20,50\n2026-11-15 00:05:00,21,51\n")
    server = make_server("127.0.0.1", 0, tmp_path)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def get(url):
    with urllib.request.urlopen(url) as r:
        return r.status, json.load(r)


def test_readings_since(base):
    status, body = get(f"{base}/readings?since=2026-11-15T00:00:00")
    assert status == 200
    assert [r["timestamp"] for r in body["readings"]] == ["2026-11-15 00:05:00"]
    assert body["more"] is False


def test_health_shows_latest(base):
    _, body = get(f"{base}/health")
    assert body == {"status": "ok", "latest": "2026-11-15 00:05:00"}


def test_bad_since_is_400(base):
    with pytest.raises(urllib.error.HTTPError) as e:
        get(f"{base}/readings?since=yesterday")
    assert e.value.code == 400


def test_writes_are_rejected(base):
    req = urllib.request.Request(f"{base}/readings", data=b"x", method="POST")
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code in (404, 405, 501)
