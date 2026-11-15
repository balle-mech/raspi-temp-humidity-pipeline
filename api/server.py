"""計測値を返す読み取り専用の HTTP API（Mac mini の life-data が定期的に取りに来る）。

    GET /health                      → {"status": "ok", "latest": "YYYY-MM-DD HH:MM:SS" | null}
    GET /readings?since=<ISO時刻>    → {"readings": [...], "more": bool}
        since より後の計測値を古い順に返す。more が true なら、最後の timestamp を since にして続きを取る。
        since を省くと最初から返す。

- 標準ライブラリだけで動く（collector と同じ）
- 書き込みの口はない。GET 以外は 501
- 待ち受けるアドレスは API_HOST（既定 127.0.0.1）。Tailscale の IP を渡し、ACL で Mac mini だけに開ける

使い方:
    API_HOST=$(tailscale ip -4) python -m api.server
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from api.readings import DEFAULT_LIMIT, latest, read_since


def make_server(host: str, port: int, data_dir: Path) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: dict) -> None:
            raw = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:  # noqa: N802
            url = urlparse(self.path)
            q = parse_qs(url.query)
            if url.path == "/health":
                return self._send(200, {"status": "ok", "latest": latest(data_dir)})
            if url.path == "/readings":
                try:
                    since = datetime.fromisoformat(q["since"][0]) if "since" in q else None
                    limit = min(int(q.get("limit", [DEFAULT_LIMIT])[0]), DEFAULT_LIMIT)
                except ValueError:
                    return self._send(400, {"error": "since は ISO 形式の時刻（例: 2026-11-15T09:00:00）"})
                rows, more = read_since(data_dir, since, limit)
                return self._send(200, {"readings": rows, "more": more})
            return self._send(404, {"error": "not found"})

    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    host = os.environ.get("API_HOST", "127.0.0.1")
    port = int(os.environ.get("API_PORT", "8600"))
    data_dir = Path(os.environ.get("DATA_DIR", "data/raw"))
    server = make_server(host, port, data_dir)
    print(f"readings API: http://{host}:{server.server_port} (data={data_dir})", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
