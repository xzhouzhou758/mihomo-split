#!/usr/bin/env python3
"""把 TAG 机场的节点导入配置。

TAG 的订阅链接只有 15 分钟有效期，没法让 Clash 自己定时去拉。
这个脚本趁链接还有效，把节点拉下来存一份快照：

  python3 tag.py "TAG链接"
      节点直接写进同目录的 config.yaml（不需要服务器）

  python3 tag.py "TAG链接" --substore https://你的域名/秘密路径
      节点存进你自己的 Sub-Store，config.yaml 改成从 Sub-Store 拉，
      以后 TAG 换节点只要重跑这条命令，各设备刷新订阅就行

只用 Python 自带的库，不用装别的东西。
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

UA = "clash.meta"
FILE_NAME = "tag"  # 存在 Sub-Store 里的文件名
KEEP = "日本家宽"  # 要和 config.yaml 里 🏷️ TAG 组的 filter 一致
BEGIN, END = "  # >>> TAG", "  # <<< TAG"


def die(msg):
    sys.exit("出错了：" + msg)


def fetch(src):
    if Path(src).is_file():
        return Path(src).read_text(encoding="utf-8")
    if "target=" not in src:
        src += ("&" if "?" in src else "?") + "target=clashmeta"
    req = urllib.request.Request(src, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        die(f"TAG 链接打不开（HTTP {e.code}），可能已经过期，重新拿一个")
    except Exception as e:
        die(f"TAG 链接打不开：{e}")


def proxies_block(text):
    """取出 proxies: 下面的节点列表（原样的几行文本，不解析 YAML）。"""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^proxies:\s*$", line):
            break
    else:
        die("内容里没有节点。链接要是 Clash/mihomo 格式（带 target=clashmeta）")
    block = []
    for line in lines[i + 1:]:
        if line.strip() and not line[0].isspace() and not line.startswith("-"):
            break
        block.append(line)
    while block and not block[-1].strip():
        block.pop()
    items = [l for l in block if re.match(r"^\s*- ", l)]
    if not items:
        die("节点列表是空的")
    base = min(len(l) - len(l.lstrip()) for l in items)
    return [l[base:] if l.strip() else "" for l in block], base


def node_names(block):
    names = []
    for l in block:
        if l.startswith("- "):
            m = re.search(r"""name:\s*(?:"([^"]*)"|'([^']*)'|([^,}\n]+))""", l)
            if m:
                name = (m.group(1) or m.group(2) or m.group(3)).strip()
                if m.group(1):  # 双引号里的 \U0001F1EF 这类转义还原成国旗
                    name = re.sub(r"\\(?:U([0-9a-fA-F]{8})|u([0-9a-fA-F]{4}))",
                                  lambda e: chr(int(e.group(1) or e.group(2), 16)), name)
                names.append(name)
    return names


def replace_tag_section(config, new_lines):
    text = config.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        die(f"{config} 里找不到 TAG 段的标记（# >>> TAG 和 # <<< TAG），别删掉这两行")
    a = text.index(BEGIN) + len(BEGIN)
    b = text.index(END)
    config.write_text(text[:a] + "\n" + "\n".join(new_lines) + "\n" + text[b:], encoding="utf-8")


def substore(base, path=""):
    return base.rstrip("/") + path


def upload(base, name, display, content):
    """把一段文本存成 Sub-Store 里的「文件」，已有就覆盖。"""
    def call(method, path, body):
        req = urllib.request.Request(
            substore(base, path), data=json.dumps(body).encode(), method=method,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)

    try:
        with urllib.request.urlopen(substore(base, "/api/files"), timeout=30) as r:
            exists = any(f.get("name") == name for f in json.load(r).get("data", []))
    except Exception as e:
        die(f"连不上 Sub-Store（{e}），检查地址，形如 https://域名/秘密路径")
    if exists:
        res = call("PATCH", f"/api/file/{name}", {"content": content})
    else:
        res = call("POST", "/api/files", {"name": name, "displayName": display,
                                          "source": "local", "content": content})
    if res.get("status") != "success":
        die(f"上传失败：{res}")


def main():
    ap = argparse.ArgumentParser(description="把 TAG 机场的节点导入配置")
    ap.add_argument("link", help="TAG 的订阅链接（15 分钟内有效），也可以是下载好的文件")
    ap.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")),
                    help="要改的配置文件，默认是同目录的 config.yaml")
    ap.add_argument("--substore", help="你的 Sub-Store 后端地址，形如 https://域名/秘密路径")
    args = ap.parse_args()

    text = fetch(args.link)
    block, _ = proxies_block(text)
    names = node_names(block)
    kept = [n for n in names if KEEP in n]
    config = Path(args.config)
    today = date.today().isoformat()

    if args.substore:
        upload(args.substore, FILE_NAME, "TAG 节点快照", text)
        replace_tag_section(config, [
            f"  # {today} 存进 Sub-Store 的快照；TAG 换节点后重跑 tag.py",
            "  TAG:",
            "    type: http",
            "    proxy: DIRECT",
            "    interval: 86400",
            f'    url: "{substore(args.substore, "/api/file/" + FILE_NAME)}"',
            "    path: ./providers/tag.yaml",
        ])
        where = "Sub-Store"
    else:
        replace_tag_section(config, [
            f"  # {today} 导入的快照；TAG 换节点后重跑 tag.py",
            "  TAG:",
            "    type: inline",
            "    payload:",
        ] + [("      " + l) if l else "" for l in block])
        where = str(config)

    print(f"导入了 {len(names)} 个 TAG 节点，写进了 {where}")
    if kept:
        print(f"🏷️ TAG 组会显示其中 {len(kept)} 个「{KEEP}」节点：")
        for n in kept:
            print("  ", n)
    else:
        print(f"注意：没有名字带「{KEEP}」的节点，🏷️ TAG 组会是空的。")
        print("   打开 config.yaml，把 🏷️ TAG 那行的 filter 改成你想留的关键词，或者删掉 filter 全部显示。")
    if not args.substore:
        print("下一步：把 config.yaml 重新导入 Clash。")
    else:
        print("下一步：python3 publish.py --substore 同一个地址，把改好的 config.yaml 发上去，各设备刷新订阅。")


if __name__ == "__main__":
    main()
