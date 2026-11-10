#!/usr/bin/env bash
# 在你自己的服务器上装 Sub-Store（只用来托管配置和 TAG 快照）
#
#   bash install.sh                 只装 Sub-Store，自己配反代（1Panel、宝塔等）
#   DOMAIN=sub.example.com bash install.sh
#                                   顺便装 Caddy，自动申请 HTTPS 证书
#                                   （域名要先解析到这台服务器，80/443 端口要空着）
#
# 适用于 Debian / Ubuntu，需要 root。
set -euo pipefail

DIR=/opt/sub-store
[ "$(id -u)" = 0 ] || { echo "请用 root 运行"; exit 1; }

if ! command -v docker >/dev/null; then
  echo "没装 Docker，现在用官方脚本安装……"
  curl -fsSL https://get.docker.com | sh
fi

mkdir -p "$DIR"
cd "$DIR"
if [ -f secret.txt ]; then
  SECRET=$(cat secret.txt)
  echo "已经装过，沿用原来的秘密路径"
else
  SECRET=$(head -c 12 /dev/urandom | od -An -tx1 | tr -d ' \n')
  echo "$SECRET" > secret.txt
  chmod 600 secret.txt
fi

cat > docker-compose.yml <<YML
services:
  sub-store:
    image: xream/sub-store:latest
    container_name: sub-store
    restart: unless-stopped
    ports:
      - "127.0.0.1:3001:3001"
    environment:
      - SUB_STORE_FRONTEND_BACKEND_PATH=/$SECRET
      - TZ=Asia/Shanghai
    volumes:
      - ./data:/opt/app/data
    mem_limit: 512m
YML
docker compose up -d

if [ -n "${DOMAIN:-}" ]; then
  mkdir -p caddy
  cat > caddy/Caddyfile <<CADDY
$DOMAIN {
	handle /$SECRET/* {
		reverse_proxy 127.0.0.1:3001
	}
	respond 404
}
CADDY
  docker rm -f sub-store-caddy >/dev/null 2>&1 || true
  docker run -d --name sub-store-caddy --restart unless-stopped --network host \
    -v "$DIR/caddy/Caddyfile:/etc/caddy/Caddyfile" -v "$DIR/caddy/data:/data" caddy:2 >/dev/null
  BASE="https://$DOMAIN/$SECRET"
else
  BASE="https://你的域名/$SECRET"
  cat <<NGINX

还差一步：在你的反代（1Panel / 宝塔 / nginx）里给域名加一段：

  location ^~ /$SECRET/ {
      proxy_pass http://127.0.0.1:3001;
      proxy_set_header Host \$host;
      proxy_set_header X-Real-IP \$remote_addr;
  }

只转发这个秘密路径，别的路径不要指向 3001。
NGINX
fi

cat <<DONE

装好了。下面这个地址就是管理员钥匙，别发给任何人：
  后端地址：$BASE
  管理界面：https://sub-store.vercel.app/?api=$BASE

回到电脑上，在 mihomo-split 目录里运行：
  python3 publish.py --substore $BASE
DONE
