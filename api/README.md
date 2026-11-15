# api — 計測値の読み取り API

Mac mini の life-data が、この API から温湿度を定期的に取りに行く（Pi からは送らない）。
可視化は life-data 側の React の画面で行う。この API は計測値を返すだけ。

## なぜ Pi から送らず、Mac mini から取りに来るのか

- Mac mini が止まっていても取りこぼさない。Pi の CSV が元データで、Mac mini は「最後に取った時刻」から続きを取る
- Pi に Mac mini や GitHub への書き込み用の鍵を置かなくてよい
- 取り込みのスケジュールと失敗時のやり直しが Mac mini 側に集まる

決定の記録は life-data の ADR-0008。

## 守ること

- 読み取り専用（GET だけ）。計測データを変える口を作らない
- 待ち受けは Tailscale の IP だけ。0.0.0.0 にしない。Tailscale の ACL で Mac mini からだけ通す
- Pi の `data/raw/` は消さない（Mac mini が取り終える前に消すと取りこぼす）

## 環境変数

| 変数名 | 既定 | 説明 |
|--------|------|------|
| `API_HOST` | `127.0.0.1` | 待ち受けるアドレス。Tailscale の IP を入れる |
| `API_PORT` | `8600` | 待ち受けるポート |
| `DATA_DIR` | `data/raw` | collector と同じ CSV の置き場 |
