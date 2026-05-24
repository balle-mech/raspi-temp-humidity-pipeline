# processor — 処理層（将来実装）

collector が書き出した CSV を処理するレイヤー。
「ビッグデータを支える技術」の Spark / Flink に相当する役割。

## 想定フェーズ

### バッチ処理（Phase 2）

日次 CSV を読み込み、集計・変換して SQLite または TimescaleDB に格納する。

```
data/raw/temp_humidity_YYYY-MM-DD.csv
    │  pandas / polars で読み込み
    ▼
日次集計（平均・最大・最小・標準偏差）
    │
    ▼
data/processed/daily_summary_YYYY-MM-DD.csv  または  SQLite
```

想定スクリプト:
- `processor/batch/daily_aggregate.py` — 日次集計
- `processor/batch/load_to_sqlite.py` — SQLite へのロード

### ストリーム処理（Phase 3）

Mosquitto（MQTT ブローカー）をローカルに立て、collector が publish → processor が subscribe。

```
collector → MQTT publish → Mosquitto → processor subscribe
                                           │
                                           ├─ 閾値アラート（温度 > 35℃ 等）
                                           └─ 移動平均の計算
```

想定スクリプト:
- `processor/stream/alert.py` — 閾値超過アラート
- `processor/stream/moving_avg.py` — 移動平均

## 参考（書籍対応）

| 本書の概念 | このプロジェクトでの対応 |
|------------|--------------------------|
| バッチ処理 | pandas/polars による日次集計スクリプト |
| ストリーム処理 | MQTT subscribe + リアルタイム処理 |
| データレイク | `data/raw/` の CSV ファイル群 |
