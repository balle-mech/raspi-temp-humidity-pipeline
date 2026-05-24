# raspi-temp-humidity-pipeline

Raspberry Pi で温湿度を継続計測し、ローカルCSVに蓄積するパイプライン。
将来的にストリーム処理・ワークフローオーケストレーション・可視化へ段階的に拡張できる構成。

## アーキテクチャ概要

「ビッグデータを支える技術（西田圭介 著）」のレイヤー構成を参考に設計。

```
[センサー]
    │  Linux IIO sysfs 経由
    ▼
[collector]          ← Phase 1（実装済）
  センサー読み取り → 日次CSVローテーション書き込み
  systemd で常時稼働
    │
    ▼
[processor]          ← Phase 2（将来）
  バッチ: 日次集計（平均・最大・最小・異常値検出）
  ストリーム: リアルタイム閾値アラート（Flink 的な役割）
    │
    ▼
[sink]               ← Phase 2〜3（将来）
  ・ローカル SQLite / TimescaleDB → Grafana 可視化
  ・オブジェクトストレージ（S3 / Azure Blob）への定期エクスポート
    │
    ▼
[orchestrator]       ← Phase 3（将来）
  Apache Airflow または Prefect でワークフロー管理
  日次バッチのスケジューリング、アラート通知
```

## ハードウェア

- **ボード**: Raspberry Pi 5
- **センサー**: DHT-11（温度・湿度）
- **インターフェース**: Linux IIO サブシステム経由（sysfs ファイル読み取り）
  - 温度: `$DEVICE0/in_temp_input`（単位: m℃、1000 で割って ℃）
  - 湿度: `$DEVICE0/in_humidityrelative_input`（単位: m%、1000 で割って %）

## セットアップ

→ [CONTRIBUTING.md](CONTRIBUTING.md) を参照。

## CSV スキーマ

`data/raw/YYYY/MM/temp_humidity_YYYY-MM-DD.csv`（日次ファイル）

| カラム | 型 | 説明 |
|--------|----|------|
| `timestamp` | string | `YYYY-MM-DD HH:MM:SS` |
| `temperature_c` | float | 温度（℃）。読み取り失敗時は空文字 |
| `humidity_pct` | float | 湿度（%）。読み取り失敗時は空文字 |

## 将来フェーズの設計メモ

### Phase 2: ローカル処理
- **バッチ処理**: 日次 CSV を集計（平均・最大・最小・異常値検出）
- **ストリーム処理**: MQTT ブローカー（Mosquitto）をローカルで立て、
  collector が publish → processor が subscribe してリアルタイム処理
- **異常検知**: 温度/湿度が閾値超過したら通知

### Phase 3: ワークフロー管理
- **Prefect** でバッチ処理のスケジューリングと依存管理（書籍記載）
- Prefect CronClock によるスケジュール定義（書籍記載）
- DAG 設計:
  `collect（毎分）→ daily_aggregate（日次）`

## ドキュメント作成のルール

### 書かないこと（メンテナンス負荷を抑える）

- **ソースコードを読めばわかること**: 関数の実装詳細、具体的なコード例（コードとドキュメントの乖離が発生する）
- **他のドキュメントと重複する内容**: 同じ情報を複数箇所に書かない。必要ならリンクで参照する
- **自動取得可能な情報**: ディレクトリツリー（`tree`/`ls` で取得可能）、依存パッケージ一覧（`package.json` で確認可能）

### 書くこと

- **方針・ルール**: なぜそうするのか（Why）、どうあるべきか（What）
- **設計思想**: 技術選定の理由、アーキテクチャの方針

### 図表

- 設計変更時は対応する図表も同時に更新してコードとの乖離を防ぐ
