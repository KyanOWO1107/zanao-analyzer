# Monitor MVP

## Scope

第一阶段只做 CPU 友好的最小闭环：

1. 输入一批帖子数据。
2. 用规则识别资料、题库、课设资源、实验报告、答案、二手书、教材等需求信号。
3. 使用本地 SQLite 记录已推送帖子，避免重复推送。
4. 支持飞书自定义机器人 webhook 推送。
5. 默认提供 dry-run 模式，未配置 webhook 时不发真实消息。
6. 真实推送默认限制为 1 条，并提供单独的飞书机器人测试命令。

## Deferred

- 拼车、租房、泛二手物品等其他需求类别。
- Redis 队列。
- LLM、向量模型、GPU 推理。
- 前端页面。

## Current Match Scope

当前只推送学习资料和教材书籍相关内容：

- 资料、复习资料、题库、课件。
- 课设/课程设计相关资料、报告、代码。
- 实验报告、答案、习题答案。
- 真题、往年题、试卷。
- 二手书、教材、课本、电子教材。

以下内容暂时不推送：拼车、租房、普通二手物品、泛学习咨询、考试吐槽。

## Current Real-API Flow

当前优先使用小程序接口拉取本校校内列表：

```bash
python -m zanao_monitor.cli fetch-mini-list --limit 20 --match
```

确认预览结果无误后，再开启真实飞书推送：

```bash
python -m zanao_monitor.cli test-feishu
python -m zanao_monitor.cli fetch-mini-list --limit 20 --match --send --send-limit 1
```

定时任务或云端 cron 应使用安静的一次性入口：

```bash
python -m zanao_monitor.cli run-mini-monitor --limit 20 --send --send-limit 1 --state data/monitor_state.db
```

该命令只输出 `scanned/matched/sent/duplicates` 汇总，便于日志观察；默认不传 `--send` 时不会发飞书，也不会写入去重状态。

## Observability

每次监控运行会记录：

- 扫描数量。
- 命中数量。
- 推送数量。
- 重复跳过数量。
- 命中候选的标题、作者、类别、关键词和状态。

查看最近命中：

```bash
python -m zanao_monitor.cli list-recent-matches --state data/monitor_state.db --limit 20
```

命中状态包括：

- `preview`: dry-run 中会被推送的候选。
- `sent`: 已真实推送并写入去重状态。
- `duplicate`: 已推送过，本次跳过。
- `limited`: 命中但超过本次 `--send-limit`，本次未推送。
