# orchestrator — オーケストレーション層（将来実装）

processor のバッチ処理をスケジュール管理するレイヤー。

## 想定フェーズ（Phase 3）

### Prefect によるワークフロー管理

書籍「ビッグデータを支える技術」に記載の Prefect サーバーと CronClock を使って
バッチ処理のスケジューリングと依存管理を行う。

```python
# orchestrator/flows/daily_pipeline.py
from prefect import flow, task
from prefect.schedules import CronClock

@task
def aggregate_daily(): ...

@task
def load_to_db(): ...

@flow(schedule=CronClock("5 0 * * *"))
def daily_pipeline():
    result = aggregate_daily()
    load_to_db(result)
```

### DAG 設計（想定）

```
[collect] 毎分（systemd）
    │
[daily_aggregate] 毎日 00:05（Prefect CronClock）
    │
[load_to_db] 00:10
```
