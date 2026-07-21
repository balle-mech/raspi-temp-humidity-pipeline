# セットアップ

## 1. 環境変数

```bash
cp .envrc.example .envrc
# .envrc を編集して DEVICE0 を設定
direnv allow
```

環境変数の一覧は下表を参照。

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|------------|------|
| `DEVICE0` | ✓ | — | IIO デバイスパス（例: `/sys/bus/iio/devices/iio:device0`） |
| `MEASUREMENT_INTERVAL_SEC` | — | `60` | 計測間隔（秒） |
| `DATA_DIR` | — | `data/raw` | CSV 出力ディレクトリ |
| `LOG_FILE` | — | `data/logs/collector.log` | ログファイルパス |
| `LOG_LEVEL` | — | `INFO` | ログレベル（DEBUG/INFO/WARNING/ERROR） |

## 2. 仮想環境

```bash
python -m venv temp-humidity-sensor-venv
source temp-humidity-sensor-venv/bin/activate
pip install -r requirements.txt
```

## 3. 動作確認

```bash
python -m collector.main
```

## 4. systemd サービス登録（常時稼働）

```bash
# パスを実環境に合わせて編集
sudo cp infra/systemd/temp-humidity-collector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable temp-humidity-collector
sudo systemctl start temp-humidity-collector
sudo systemctl status temp-humidity-collector
```

## 5. ログ確認

```bash
journalctl -u temp-humidity-collector -f
tail -f data/logs/collector.log
```

## ブランチ戦略

| ブランチ | 用途 |
|----------|------|
| `main` | 常に動作する最新版。直接コミットせず PR 経由でマージする |
| `feature/<機能名>` | 機能開発用。`main` から分岐し、マージ後は削除する |
| `archive/<名前>` | 現構成から外した実装を履歴ごと残す退避先（例: `archive/databricks-pipeline`） |

- 機能開発ブランチは `feature/` プレフィックスで始める（例: `feature/dashboard-smoothing`）
- `dev` プレフィックスや恒久的な開発ブランチ（`develop` 等）は使わない
