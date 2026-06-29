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

## 方案 C: AstrBot 插件

如果 AstrBot 方便扩展，建议在 AstrBot 侧写一个小插件，暴露本地 HTTP 入口：

```http
POST http://127.0.0.1:port/zanao-notify
```

插件收到请求后调用 AstrBot 自己的消息发送能力。这样本项目不需要知道 AstrBot 内部事件和适配器细节，只对一个稳定 HTTP 接口发消息。

## 建议

当前优先推荐方案 A 或 C：让 QQ 机器人侧提供一个简单 HTTP webhook。

这样另一部门不需要暴露内部实现，我们这边也不会绑定某个 QQ 框架。等对方给出接口后，再在项目里加一个 `qq_bot.py` 通知实现，并通过 `.env` 控制是否启用。
