# Zanao Monitor

轻量级赞噢校园集市需求监测项目。

第一版目标：

- 从样例或后续采集到的帖子中识别需求信息。
- 对命中内容做去重。
- 通过飞书自定义机器人推送。
- 保持 CPU 友好，不依赖本地 GPU。

当前关注范围：

- 资料、复习资料、题库、课件
- 课设/课程设计相关资料、报告、代码
- 实验报告、答案、习题答案
- 真题、往年题、试卷
- 二手书、教材、课本、电子教材

暂不推送拼车、租房、泛二手物品、普通学习咨询等内容。

当前阶段已经接入小程序列表接口，并完成“拉取、规则筛选、去重、飞书推送”的最小闭环。

获取本校赞噢请求参数前，请先阅读：

```text
docs/zanao-parameter-capture.md
```

填写 `.env` 时看字段对照：

```text
docs/env-fields.md
```

## 使用

安装开发依赖：

```bash
python -m pip install -e ".[dev]"
```

dry-run 示例：

```bash
python -m zanao_monitor.cli --posts examples/posts.sample.json --state data/monitor_state.db
```

从 `Zanao-LLM-Analyzer` 的校内帖子 SQLite 库 dry-run：

```bash
python -m zanao_monitor.cli --inschool-db Zanao-LLM-Analyzer/data/zanao_detailed_info/inschool_posts_and_comments.db --state data/monitor_state.db --limit 50
```

从当前 `.env` 配置的小程序接口 dry-run 拉取校内帖子列表：

```bash
python -m zanao_monitor.cli fetch-mini-list --limit 3
```

本命令只打印脱敏后的列表结果，不入库、不推送。

拉取后立刻执行规则筛选和飞书推送预览：

```bash
python -m zanao_monitor.cli fetch-mini-list --limit 20 --match --state data/monitor_state.db
```

未传 `--send` 时不会发飞书，也不会写入去重状态；它只是告诉你当前有哪些内容会被推送。

测试飞书机器人配置：

```bash
python -m zanao_monitor.cli test-feishu
```

本命令会从 `.env` 或进程环境变量读取 `FEISHU_WEBHOOK_URL` / `FEISHU_WEBHOOK_SECRET`，只发送一条固定测试消息。

真实飞书推送当前本校列表命中项：

```bash
python -m zanao_monitor.cli fetch-mini-list --limit 20 --match --send --send-limit 1 --state data/monitor_state.db
```

未传 `--send` 时不会发飞书，也不会写入去重状态；传入 `--send` 后才会真实推送并记录已推送内容。`--send-limit` 默认是 `1`，用于避免第一次运行时一次性推送太多。

适合定时任务的一次性监控命令：

```bash
python -m zanao_monitor.cli run-mini-monitor --limit 20 --state data/monitor_state.db
```

上面是 dry-run，不发飞书、不写去重状态。确认要用于正式定时推送时使用：

```bash
python -m zanao_monitor.cli run-mini-monitor --limit 20 --send --send-limit 1 --state data/monitor_state.db
```

它只输出汇总计数，适合写入计划任务或云端 cron 日志。

查看最近命中过的候选：

```bash
python -m zanao_monitor.cli list-recent-matches --state data/monitor_state.db --limit 20
```

每次监控运行都会在状态库里记录扫描汇总和命中候选，便于之后观察误报、漏报和推送效果。

## 定时运行

Windows 和 Linux 的定时运行方式见：

```text
docs/scheduled-run.md
```

仓库提供两个脚本：

```text
scripts/run_monitor.ps1
scripts/run_monitor.sh
```

它们默认扫描最近 20 条、真实推送、每次最多推送 1 条，并把日志追加到 `logs/monitor.log`。
