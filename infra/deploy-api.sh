#!/bin/sh
# 読み取り API を Pi に入れる・更新する。git pull のあとに、このリポジトリの場所で実行する:
#   git pull && sh infra/deploy-api.sh
# 何度実行してもよい（初回は systemd に登録、2回目以降は再起動して新しいコードにする）。
# sudo のパスワードを聞かれる。
set -eu

cd "$(dirname "$0")/.."
unit=temp-humidity-api

# 1. 待ち受けるアドレス（Tailscale の IP）を .env に書く。すでにあれば変えない
if ! grep -q '^API_HOST=' .env 2>/dev/null; then
  ip=$(tailscale ip -4 | head -1)
  [ -n "$ip" ] || { echo "Tailscale の IP が取れない（tailscale up 済みか確かめる）" >&2; exit 1; }
  echo "API_HOST=$ip" >> .env
  echo ".env に API_HOST=$ip を足した"
fi

# 2. systemd に登録して起動（登録済みなら、ユニットを更新して再起動）
sudo cp "infra/systemd/$unit.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "$unit" >/dev/null 2>&1
sudo systemctl restart "$unit"

# 3. 動いているか確かめる
host=$(grep '^API_HOST=' .env | tail -1 | cut -d= -f2)
port=$(grep '^API_PORT=' .env 2>/dev/null | tail -1 | cut -d= -f2)
port=${port:-8600}
i=0
until python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://$host:$port/health', timeout=2).status == 200 else 1)" 2>/dev/null; do
  i=$((i + 1))
  if [ "$i" -ge 10 ]; then
    echo "API が応答しない。ログ: journalctl -u $unit -n 50" >&2
    exit 1
  fi
  sleep 1
done
echo "API は動いている: http://$host:$port/health"
echo "Mac mini の取り込み用ユーザーの .env に ROOM_API_URL=http://$host:$port を書く"
