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
