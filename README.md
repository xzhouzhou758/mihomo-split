# mihomo-split

一份开箱能用的 mihomo（Clash Meta）分流配置，电脑、手机、OpenWrt 通用。

- AI 分得细：OpenAI、Claude、Gemini、其他 AI 各一组，可以分别选节点
- Claude 防风控：Claude 桌面版整个程序，加上它用到的人机验证、付款、客服、统计，都走同一个出口，不会一会儿日本一会儿香港
- 支持 TAG 这类 15 分钟就过期的 AI 机场：用 `tag.py` 存一份节点快照
- 多机场合并：地区组（港台日新美）和自动选择会从所有机场里挑，但**超过 1x 的高倍率节点不会进去**，免得悄悄费流量
- Google、YouTube、Netflix、Telegram、Discord、GitHub、游戏、微软、苹果各自成组，国内直连，广告拦截
- 规则每天自动更新（MetaCubeX 规则库）

## 两种用法

| | 不用服务器 | 用自己的服务器 |
|---|---|---|
| 适合 | 只有一两台设备 | 电脑、手机、OpenWrt 都要用，改一次处处生效 |
| 怎么用 | 改好 `config.yaml`，直接导入 Clash | 装 Sub-Store 托管配置，各设备填同一条订阅链接 |
| 需要 | 电脑上有 Python 3（导入 TAG 时用） | 一台 Linux 服务器 + 一个域名 |

机场订阅都是设备自己去拉，所以只许大陆访问的机场也能用。服务器只存配置文件和 TAG 快照。

## 第一步：填机场

打开 `config.yaml`，找「改这里」：

1. 把 `https://换成你的订阅链接-1` 这几个换成你的机场订阅链接（Clash / mihomo 格式）。
2. 机场不是三家的话，增删 `机场1 / 机场2 / 机场3`：`x-airports` 名单、`proxy-providers` 里那一段、`✈️ 机场N` 那个组要一起改。名字可以改成机场的真名。
3. 想让自己的服务器直连（省流量），把规则里的 `example.com` 换成你的域名。

## 第二步：导入 TAG（没有 TAG 就跳过）

TAG 的订阅链接 15 分钟就失效，Clash 没法定时更新它。拿到新链接后，**15 分钟内**在这个目录运行：

```bash
python3 tag.py "TAG的订阅链接"
```

节点会直接写进 `config.yaml`，脚本会列出 🏷️ TAG 组里有哪些节点。默认只留名字带「日本家宽」的，想要别的就改 🏷️ TAG 那一行的 `filter`。

TAG 换节点了，再拿一个新链接重跑一次就行。

**没有 TAG 的话**：🧠 Claude 和 🦾 其他AI 默认选的是 🏷️ TAG，它是空的，会变成直连，Claude 打不开。导入后在 Clash 里把这两组切到 🇺🇸 美国。

## 第三步：用起来

### 不用服务器

把 `config.yaml` 导入 Clash Verge / ClashX Meta / mihomo 客户端（「导入本地文件」），完事。以后改了配置就重新导入一次。

### 用自己的服务器

1. 把 `install.sh` 传到服务器上，用 root 运行：

   ```bash
   bash install.sh
   ```

   如果域名已经解析到这台服务器，而且 80/443 端口空着，可以让脚本顺便装 Caddy、自动配 HTTPS：

   ```bash
   DOMAIN=sub.你的域名.com bash install.sh
   ```

   装完会打印一个「后端地址」，形如 `https://域名/一串随机字符`。**这就是管理员钥匙，别发给任何人。**
   没用 `DOMAIN` 的话，照脚本最后的提示在 1Panel / 宝塔 / nginx 里加一段反代。

2. 回到电脑上，导入 TAG 时带上这个地址（TAG 快照存进服务器，以后各设备自动同步）：

   ```bash
   python3 tag.py "TAG的订阅链接" --substore https://域名/秘密路径
   ```

3. 把配置发上去：

   ```bash
   python3 publish.py --substore https://域名/秘密路径
   ```

   它会打印一条订阅链接，填进电脑、手机、OpenWrt 的 Clash 里。以后改了 `config.yaml`，或者重跑了 `tag.py`，就再跑一次 `publish.py`，各设备刷新订阅即可。

## 分组说明

| 分组 | 默认 | 说明 |
|---|---|---|
| 🚀 节点选择 | ♻️ 自动选择 | 大部分外网流量走这里 |
| ♻️ 自动选择 | 自动挑最快 | 只挑港/台/日/新/美的 1x 及以下节点 |
| 🇭🇰 🇹🇼 🇯🇵 🇸🇬 🇺🇸 🌍 | 自动挑最快 | 按地区，同样不含高倍率节点 |
| 📋 全部节点 / ✈️ 机场N | 手动 | 所有节点，高倍率的也在，想用就手动选 |
| 🏷️ TAG | 手动 | TAG 的日本家宽。**挑一个固定用，别来回换**，换节点等于换了一户人家的 IP |
| 🧠 Claude / 🦾 其他AI | 🏷️ TAG | |
| 🤖 OpenAI / ✨ Gemini | 🇸🇬 新加坡 | 香港、俄罗斯的节点会被 OpenAI 和 Gemini 拒绝 |
| 🖥️ 我的服务器 | 直连 | 卡了再切到美国节点 |
| 🏠 国内 / Ⓜ️ 微软 / 🍎 苹果 | 直连 | |
| 🐟 漏网之鱼 | 🚀 节点选择 | 没匹配到任何规则的流量 |

## 注意

- 订阅链接、Sub-Store 的秘密路径都相当于密码，别贴到群里，也别提交到 GitHub。
- 「Claude 桌面版整个程序走 Claude 组」这条按程序名识别，只在电脑上有效，手机和 OpenWrt 上会被忽略。
- `install.sh` 适用于 Debian / Ubuntu。没装 Docker 的话，它会用 Docker 官方脚本自动安装。
