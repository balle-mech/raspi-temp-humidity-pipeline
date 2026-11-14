# Mac mini デプロイ・データ連携の設計方針

温湿度Webアプリ統合後の配置と、Raspberry Pi の計測データを Web アプリから参照する方式の検討メモ。

## 方針

- **Web アプリは統合後に Mac mini へデプロイする。** 将来ローカル LLM（Ollama 等）を同一マシンで動かすなど、拡張余地を確保するため。LLM は別プロセスで動くため Web アプリと競合しない。
- **データ連携は GitHub 経由を基本とする。** Pi が計測 CSV を同リポジトリへ push し、Mac mini 側が pull して Web アプリがローカルファイルを読む。

## データ連携方式

```
[Raspberry Pi]  collector → CSV → 定期 commit/push（data 専用ブランチ）
        │
        ▼  GitHub
[Mac mini]      launchd で定期 git pull → Web アプリがローカルの CSV を参照
```

### 設計上の判断（Why）

| 論点 | 判断 | 理由 |
|------|------|------|
| push 頻度 | 1時間ごとなど、まとめて push | 毎分 push はコミット履歴が肥大化する |
| 開発 push との衝突 | `data` 専用ブランチ（または専用ディレクトリ）に分離し、Pi 側は `pull --rebase` してから push | 開発ブランチと Pi の push が競合するのを避ける |
| 認証 | 対象リポジトリ限定の deploy key（書き込み許可） | 権限を最小化する |
| 参照方法 | raw URL 直接参照でなく、pull したローカルファイルを読む | private 化した場合にトークン管理が不要になる |
| リアルタイム性 | 求めない（遅延 = push 間隔 + pull 間隔） | GitHub 経由の構成上の制約 |

### 代替案（リアルタイム性が必要になった場合）

Pi から Mac mini の API へ直接 POST する（Tailscale 経由が安全）。GitHub へは日次でバックアップ push のみ行う。履歴肥大化も避けられる。

## 未決事項

- Web アプリのスタックと統合後のデプロイ方式（Docker か launchd + venv か）
- data ブランチ運用か、同一ブランチの専用ディレクトリ運用か
