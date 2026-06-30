# QQ Bot Integration

当前项目已经有飞书推送。QQ 机器人可以作为下一种通知通道，但需要先确认机器人侧暴露的接口。

不要直接假设对方机器人协议。请先向另一部门确认：

- 是否有 HTTP 接口。
- 接口地址和鉴权方式。
- 发送目标是群号还是用户号。
- 请求体格式。
- 成功/失败响应格式。
- 是否限流。

## 推荐抽象

项目侧建议统一成一个通知接口：

```text
send(text) -> success/failure
```

后续可以有多个实现：

- Feishu webhook。
- QQ webhook。
- OneBot/LLBot HTTP API。
- AstrBot 自定义插件入口。

## 方案 A: 机器人提供 HTTP Webhook

这是最简单的方式。机器人侧提供一个接口，例如：

```http
POST http://bot-host:port/notify
Authorization: Bearer <token>
Content-Type: application/json
```

请求体：

```json
{
  "target_type": "group",
  "target_id": "123456789",
  "text": "赞噢需求提醒..."
}
```

项目只需要配置：

```text
QQ_BOT_WEBHOOK_URL=
QQ_BOT_TOKEN=
QQ_BOT_TARGET_TYPE=group
QQ_BOT_TARGET_ID=
```

## 方案 B: LLBot / OneBot HTTP API

如果 LLBot 暴露 OneBot v11 风格 HTTP API，常见群消息接口类似：

```http
POST http://127.0.0.1:3000/send_group_msg
Authorization: Bearer <access_token>
Content-Type: application/json
```

请求体类似：

```json
{
  "group_id": 123456789,
  "message": "赞噢需求提醒..."
}
```

私聊接口通常是：

```http
POST /send_private_msg
```

请求体类似：

```json
{
  "user_id": 123456789,
  "message": "赞噢需求提醒..."
}
```

实际字段以 LLBot 配置和版本为准。

## 方案 C: AstrBot OpenAPI IM

当前测试环境的 AstrBot 对插件扩展 POST 路由返回 `405 Method Not Allowed`，所以项目侧优先使用 AstrBot 官方 IM 接口：

```http
POST http://127.0.0.1:6185/api/v1/im/message
X-API-Key: <AstrBot API Key>
Content-Type: application/json
```

请求体：

```json
{
  "umo": "unified_msg_origin",
  "message": "赞噢需求提醒..."
}
```

仍保留一个独立插件仓库，不放在主项目 Git 仓库中，用于在 QQ 会话中显示当前会话的 `UMO`：

```text
E:\Workplace\Projects\zanao-astrbot-notify-plugin
```

在接收通知的 QQ 群或私聊里发送：

```text
/zanao_bind
```

插件会返回当前会话的 `UMO`，填入主项目 `.env`：

```text
ASTRBOT_ENABLED=true
ASTRBOT_IM_ENABLED=true
ASTRBOT_BASE_URL=http://127.0.0.1:6185
ASTRBOT_API_KEY=AstrBot 面板 OpenAPI Key
ASTRBOT_UMO=/zanao_bind 返回的 UMO
ASTRBOT_TIMEOUT_SECONDS=10
```

旧的插件 webhook 字段只在 AstrBot 支持插件扩展 POST 时使用：

```text
ASTRBOT_WEBHOOK_URL=
ASTRBOT_TOKEN=
```

## 建议

当前优先推荐方案 A 或 C：让 QQ 机器人侧提供一个简单 HTTP webhook。

这样另一部门不需要暴露内部实现，我们这边也不会绑定某个 QQ 框架。等对方给出接口后，再在项目里加一个 `qq_bot.py` 通知实现，并通过 `.env` 控制是否启用。
