# AI Review

当前项目默认使用关键词规则识别需求信息，不启用 AI。

AI 功能是可选的二级判断：

```text
赞噢帖子 -> 规则命中 -> AI 二次判断 -> 飞书推送/跳过
```

只有规则先命中的候选才会发给远端 AI 平台。AI 不会收到赞噢登录态、飞书 webhook、salt 等敏感配置。

## 配置

`.env` 示例：

```text
AI_ENABLED=false
AI_PROVIDER=openai-compatible
AI_BASE_URL=https://example.com/v1
AI_API_KEY=你的 API Key
AI_MODEL=你的模型名
AI_CONFIDENCE_THRESHOLD=0.7
AI_TIMEOUT_SECONDS=10
```

启用后：

```text
AI_ENABLED=true
```

要求平台兼容 OpenAI Chat Completions：

```text
POST {AI_BASE_URL}/chat/completions
Authorization: Bearer {AI_API_KEY}
```

模型需要返回 JSON：

```json
{
  "is_target": true,
  "category": "course_resource",
  "intent": "request",
  "confidence": 0.86,
  "reason": "用户明确在求题库和实验报告"
}
```

只有 `is_target=true` 且 `confidence >= AI_CONFIDENCE_THRESHOLD` 的候选才会继续推送。

## 失败行为

- AI 未启用：沿用纯规则筛选。
- AI 返回低置信度或 `is_target=false`：记录为 `ai_rejected`，不推送。
- AI 超时、网络错误、返回格式错误：记录为 `ai_error`，不推送。

可以用下面命令查看最近记录：

```bash
python -m zanao_monitor.cli list-recent-matches --state data/monitor_state.db --limit 20
```
