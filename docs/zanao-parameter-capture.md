# 赞噢本校参数获取指南

本项目只监测你自己学校的赞噢校内集市。下面的步骤用于从你自己的账号、自己的设备上观察赞噢小程序发出的请求，提取后续采集器需要的配置。

## 安全边界

- 只使用自己的微信账号和自己的设备。
- 不抓取、保存或分享他人的登录态、Token、Cookie。
- 不绕过证书校验、设备风控、加密保护或小程序安全机制。
- 不把真实 Token、Webhook、密钥提交到 Git。
- 第一次只做少量 dry-run 请求，确认字段含义和限速，不做高频采集。

## 需要记录的字段

优先定位赞噢校内帖子列表接口，通常类似：

```text
POST https://api.x.zanao.com/thread/v2/list
```

需要记录这些请求头或配置：

```text
X-Sc-Od          用户 Token，敏感信息
X-Sc-Alias       学校 alias，用来区分学校
X-Sc-Version     小程序/客户端版本
X-Sc-Platform    平台标识
X-Sc-Appid       小程序 appid
User-Agent       请求使用的 User-Agent
Referer          通常包含 servicewechat.com 路径
```

还会看到这些动态字段：

```text
X-Sc-Nd          每次请求变化的随机数
X-Sc-Td          每次请求变化的时间戳
X-Sc-Ah          每次请求变化的签名
```

动态字段不能直接当作长期配置。原参考项目的思路是用：

```text
md5("{school_alias}_{nd}_{td}_{api_salt}")
```

生成 `X-Sc-Ah`。如果我们只能看到 `X-Sc-Ah`，但不知道 `api_salt`，短期只能做一次性的请求复现验证，不能稳定长期运行。

## 推荐工具

任选一个你熟悉的 HTTPS 调试代理：

- Fiddler Classic / Fiddler Everywhere
- Charles Proxy
- mitmproxy

这些工具的共同思路是：

1. 电脑启动代理工具。
2. 手机和电脑处于同一局域网。
3. 手机 Wi-Fi 代理指向电脑 IP 和代理端口。
4. 手机安装并信任该代理工具提供的调试证书。
5. 打开微信，进入赞噢/在学校小程序，刷新校内集市。
6. 在代理工具中筛选 `api.x.zanao.com` 请求。

如果小程序或系统拒绝被调试代理观察，不要尝试绕过。先暂停，改为寻找官方接口、导出能力或手动导入样例数据。

## 操作流程

### 1. 启动代理

在电脑上启动代理工具，确认代理端口，例如：

```text
Fiddler: 8888
Charles: 8888
mitmproxy: 8080
```

查看电脑局域网 IP，例如 Windows PowerShell：

```powershell
ipconfig
```

记录 IPv4 地址，例如：

```text
192.168.1.23
```

### 2. 配置手机代理

在手机 Wi-Fi 设置中找到当前网络，配置 HTTP 代理：

```text
服务器: 电脑局域网 IP
端口: 代理工具端口
```

然后按代理工具提示安装并信任调试证书。

### 3. 触发赞噢请求

打开微信小程序，进入本校赞噢校园集市，做这些动作：

- 刷新帖子列表。
- 点开一条帖子详情。
- 如后续需要评论，再进入评论区。

代理工具里筛选：

```text
api.x.zanao.com
```

优先找：

```text
/thread/v2/list
/thread/info
/comment/list
```

### 4. 记录请求样本

为每类接口保存一份请求样本：

```text
docs/private-capture/thread-list-request.txt
docs/private-capture/thread-info-request.txt
docs/private-capture/comment-list-request.txt
```

这些文件包含敏感信息，必须加入 `.gitignore`，不要提交。

最少记录：

```text
Request URL
Request Method
Request Headers
Form Body
Response JSON 的字段结构
```

### 5. 参数核对表

填下面这张表，真实值只放在本地 `.env`，不要写进文档：

```text
ZANAO_BASE_URL=https://api.x.zanao.com
ZANAO_SCHOOL_ALIAS=
ZANAO_USER_TOKEN=
ZANAO_API_SALT=
ZANAO_SC_VERSION=
ZANAO_SC_PLATFORM=
ZANAO_SC_APPID=
ZANAO_USER_AGENT=
ZANAO_REFERER=
```

如果暂时不知道 `ZANAO_API_SALT`，标记为未知。我们可以先做“手动导入样例 JSON/SQLite”的流程，等签名生成确认后再接实时采集。

## 判断是否拿对了请求

一个正确的校内帖子列表请求通常满足：

- URL 是 `api.x.zanao.com` 下的校内帖子列表接口。
- 请求头里有 `X-Sc-Od` 和 `X-Sc-Alias`。
- 响应 JSON 中有帖子列表。
- 帖子项里能看到帖子 ID、标题/内容、发布时间、作者信息等字段。
- `X-Sc-Alias` 对应的是你的学校，而不是参考项目作者的学校。

## 给开发阶段的交付物

拿到参数后，给项目准备这两类材料：

1. 脱敏后的接口样本
   - 隐去 `X-Sc-Od`
   - 隐去手机号、昵称等个人信息
   - 保留字段名和 JSON 结构

2. 本地 `.env`
   - 保存真实 Token 和密钥
   - 不提交 Git

下一步实现时，我们会先做：

```text
读取 .env -> 构造校内列表请求 -> dry-run 打印前 N 条帖子 -> 不入库、不推送
```

`.env` 字段逐项对照见：

```text
docs/env-fields.md
```
