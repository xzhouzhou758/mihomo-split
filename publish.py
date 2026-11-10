#!/usr/bin/env python3
"""把 config.yaml 发到你自己的 Sub-Store，各设备用同一条订阅链接。

  python3 publish.py --substore https://你的域名/秘密路径

发完会打印订阅链接，填进电脑、手机、OpenWrt 的 Clash 里。
以后改了 config.yaml，重跑一次，各设备刷新订阅就生效。
"""
import argparse
import urllib.request
from pathlib import Path

from tag import die, substore, upload

NAME = "mihomo"


def main():
    ap = argparse.ArgumentParser(description="把 config.yaml 发到 Sub-Store")
    ap.add_argument("--substore", required=True, help="Sub-Store 后端地址，形如 https://域名/秘密路径")
    ap.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")))
    args = ap.parse_args()

    text = Path(args.config).read_text(encoding="utf-8")
    if "换成你的订阅链接" in text:
        die("config.yaml 里还有没填的机场链接（「换成你的订阅链接」），填好或删掉再发")
    upload(args.substore, NAME, "mihomo 分流配置", text)
    url = substore(args.substore, f"/api/file/{NAME}")
    with urllib.request.urlopen(url, timeout=30) as r:
        if r.read().decode("utf-8") != text:
            die("发上去了，但读回来的内容对不上，再试一次")
    print("发好了。订阅链接（别发给别人）：")
    print("  " + url)


if __name__ == "__main__":
    main()
