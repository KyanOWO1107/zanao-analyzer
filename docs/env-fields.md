# `.env` 字段填写对照

本项目优先使用小程序接口：

```text
POST https://api.x.zanao.com/thread/v2/list
```

请从 `@private/mini/thread_v2_list_...txt` 这类小程序列表请求里复制字段。不要从 `@private/app/` 的请求里混用字段，因为 App 和小程序的鉴权头不同。

## 必填字段

### `ZANAO_BASE_URL`

来源：请求 URL 的协议和域名。

抓包中看到：

```text
POST https://api.x.zanao.com/thread/v2/list
```

填写：

```text
ZANAO_BASE_URL=https://api.x.zanao.com
```

### `ZANAO_SCHOOL_ALIAS`

来源：请求头 `X-Sc-Alias`。

你的抓包中当前看到的是：

```text
X-Sc-Alias: tyut
```

所以如果这是你本校账号对应的请求，就填：

```text
ZANAO_SCHOOL_ALIAS=tyut
```

如果之后发现你的学校 alias 不是这个值，以实际抓包为准。

### `ZANAO_USER_TOKEN`

来源：请求头 `X-Sc-Od`。

填写整个值，原样复制，不要加引号，不要换行：

```text
ZANAO_USER_TOKEN=这里填 X-Sc-Od 的完整值
```

这是敏感登录态，不能提交 Git，也不要发到聊天里。

### `ZANAO_SC_VERSION`

来源：请求头 `X-Sc-Version`。

示例：

```text
ZANAO_SC_VERSION=4.5.6
```

### `ZANAO_SC_PLATFORM`

来源：请求头 `X-Sc-Platform`。

小程序 Windows 抓包通常类似：

```text
ZANAO_SC_PLATFORM=windows
```

### `ZANAO_SC_APPID`

来源：请求头 `X-Sc-Appid`。

示例：

```text
ZANAO_SC_APPID=wx3921ddb0258ff14f
```

### `ZANAO_USER_AGENT`

来源：请求头 `User-Agent`。

复制完整值。它很长，保持一行：

```text
ZANAO_USER_AGENT=Mozilla/5.0 ... XWEB/19921
```

### `ZANAO_REFERER`

来源：请求头 `Referer`。

示例：

```text
ZANAO_REFERER=https://servicewechat.com/wx3921ddb0258ff14f/133/page-frame.html
```

## 暂时不确定的字段

### `ZANAO_API_SALT`

用途：生成动态请求头 `X-Sc-Ah`。

参考项目里的推测生成方式是：

```text
X-Sc-Ah = md5("{alias}_{nd}_{td}_{api_salt}")
```

其中：

- `alias` 来自 `ZANAO_SCHOOL_ALIAS`
- `nd` 是每次请求随机生成的 `X-Sc-Nd`
- `td` 是每次请求的 `X-Sc-Td`
- `api_salt` 就是 `ZANAO_API_SALT`

如果你不知道 salt，先留空：

```text
ZANAO_API_SALT=
```

后续我们会做一个签名验证工具：用抓包中的 `X-Sc-Nd`、`X-Sc-Td`、`X-Sc-Ah` 和候选 salt 校验是否能复现签名。

当前本地样本已验证：参考项目中的候选 salt 可以复现小程序抓包里的 `X-Sc-Ah`，因此本地 `.env` 已补齐该字段。不要把真实 `.env` 提交到 Git。

## 不要填进 `.env` 的动态字段

下面这些每次请求都会变化，不应该固定写进 `.env`：

```text
X-Sc-Nd
X-Sc-Td
X-Sc-Ah
Content-Length
```

后续客户端会自动生成它们。

## App 字段不要混用

App 请求使用的是：

```text
X-Sc-Token
X-Sc-Client: app
X-Sc-Device
http://api.app.zanao.com
```

小程序请求使用的是：

```text
X-Sc-Od
X-Sc-Appid
https://api.x.zanao.com
```

当前项目优先接小程序接口，因此 `.env` 先不要填 App 的 `X-Sc-Token` 或 `X-Sc-Device`。

## 推荐最小 `.env`

```text
ZANAO_BASE_URL=https://api.x.zanao.com
ZANAO_SCHOOL_ALIAS=从 X-Sc-Alias 复制
ZANAO_USER_TOKEN=从 X-Sc-Od 复制
ZANAO_API_SALT=
ZANAO_SC_VERSION=从 X-Sc-Version 复制
ZANAO_SC_PLATFORM=从 X-Sc-Platform 复制
ZANAO_SC_APPID=从 X-Sc-Appid 复制
ZANAO_USER_AGENT=从 User-Agent 复制完整一行
ZANAO_REFERER=从 Referer 复制完整一行
```
