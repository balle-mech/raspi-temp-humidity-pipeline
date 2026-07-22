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
| `main` | 安定版。`develop` からのマージのみを受け付け、直接コミットしない |
| `develop` | 開発の統合ブランチ。機能ブランチの派生元・マージ先 |
| `feature/<機能名>` | 機能開発用。`develop` から分岐し、マージ後は削除する |
| `archive/<名前>` | 現構成から外した実装を履歴ごと残す退避先（例: `archive/databricks-pipeline`） |

- 機能開発ブランチは `feature/` プレフィックスで始める（例: `feature/dashboard-smoothing`）。`dev` プレフィックスは使わない
- フロー: `feature/*` → PR → `develop` → 動作確認後 `main` へマージ

## 6. エアコン自動OFF（automation）

温度の周期変動からエアコンONを推測し、人感センサーが長時間無反応なら
SwitchBot 経由で OFF を送る。**デフォルトはドライラン**（ログのみ）。

### 環境変数（.env に追記）

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|------------|------|
| `SWITCHBOT_TOKEN` / `SWITCHBOT_SECRET` | ✓ | — | SwitchBot アプリ → プロフィール → 設定 → 開発者向けオプション |
| `SWITCHBOT_AIRCON_DEVICE_ID` | ✓ | — | `python -m automation.switchbot devices` で確認 |
| `PIR_GPIO` | — | 無効 | 人感センサーの GPIO 番号。未設定なら自動OFFは発動しない |
| `AUTOMATION_DRY_RUN` | — | `true` | `false` で実際に OFF を送信 |
| `NO_MOTION_HOURS` | — | `12` | 無人と判断するまでの時間 |
| `AC_MIN_SWING_C` / `AC_MIN_SWINGS` | — | `0.8` / `4` | サイクル判定の振幅(℃)・反転回数 |
| `AUTOMATION_INTERVAL_SEC` | — | `600` | 評価間隔（秒） |
| `COOLDOWN_HOURS` | — | `3` | OFF送信後の再送抑止時間 |

### 有効化の手順

1. 過去データで判定精度を確認: `python -m automation.backtest data/raw 7`
   （表示された「エアコンON推測」時間帯を実際の使用記憶と突き合わせる）
2. ドライランで数日運用し、ログ（`data/logs/automation.log`）を確認
3. 問題なければ `.env` で `AUTOMATION_DRY_RUN=false`

### systemd 登録

```bash
sudo cp infra/systemd/temp-humidity-automation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now temp-humidity-automation
```
