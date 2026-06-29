# Scheduled Run

本页记录本地 Windows 和 Linux/云服务器的定时运行方式。

运行前先确认：

```bash
python -m pip install -e ".[dev]"
python -m zanao_monitor.cli test-feishu
python -m zanao_monitor.cli run-mini-monitor --limit 20 --state data/monitor_state.db
```

确认 dry-run 正常后，再启用真实推送脚本。

## Windows

PowerShell 脚本：

```powershell
.\scripts\run_monitor.ps1
```

这个脚本默认执行一次后退出，适合任务计划程序重复调用。

默认行为：

- 扫描最近 20 条。
- 真实推送。
- 每次最多推送 1 条。
- 使用 `.env`。
- 状态库为 `data\monitor_state.db`。
- 日志追加到 `logs\monitor.log`。

可以覆盖参数：

```powershell
.\scripts\run_monitor.ps1 -Limit 50 -SendLimit 1 -State "data\monitor_state.db" -EnvFile ".env"
```

保持监视状态：

```powershell
.\scripts\run_monitor.ps1 -Watch -IntervalSeconds 600
```

该命令会一直运行，每 600 秒扫描一次。检测到新的符合规则内容时，会推送给飞书机器人并写入去重状态。

测试 watch 模式但只跑两轮：

```powershell
.\scripts\run_monitor.ps1 -Watch -IntervalSeconds 5 -MaxCycles 2 -SendLimit 0
```

创建 Windows 任务计划程序任务，每 10 分钟运行一次：

```powershell
schtasks /Create /TN "ZanaoMonitor" /SC MINUTE /MO 10 /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File E:\Workplace\Projects\zanao-analyzer\scripts\run_monitor.ps1" /F
```

手动触发：

```powershell
schtasks /Run /TN "ZanaoMonitor"
```

删除任务：

```powershell
schtasks /Delete /TN "ZanaoMonitor" /F
```

## Linux

先给脚本执行权限：

```bash
chmod +x scripts/run_monitor.sh
```

直接运行：

```bash
./scripts/run_monitor.sh
```

默认执行一次后退出，适合 cron 重复调用。

可以通过环境变量覆盖参数：

```bash
LIMIT=50 SEND_LIMIT=1 STATE=data/monitor_state.db ENV_FILE=.env ./scripts/run_monitor.sh
```

保持监视状态：

```bash
WATCH=1 INTERVAL_SECONDS=600 ./scripts/run_monitor.sh
```

该命令会一直运行，每 600 秒扫描一次。检测到新的符合规则内容时，会推送给飞书机器人并写入去重状态。

测试 watch 模式但只跑两轮：

```bash
WATCH=1 INTERVAL_SECONDS=5 MAX_CYCLES=2 SEND_LIMIT=0 ./scripts/run_monitor.sh
```

### crontab

打开 crontab：

```bash
crontab -e
```

每 10 分钟运行一次：

```cron
*/10 * * * * cd /path/to/zanao-analyzer && ./scripts/run_monitor.sh
```

### systemd

`/etc/systemd/system/zanao-monitor.service`：

```ini
[Unit]
Description=Zanao monitor

[Service]
Type=oneshot
WorkingDirectory=/path/to/zanao-analyzer
ExecStart=/path/to/zanao-analyzer/scripts/run_monitor.sh
```

`/etc/systemd/system/zanao-monitor.timer`：

```ini
[Unit]
Description=Run Zanao monitor every 10 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=10min
Unit=zanao-monitor.service

[Install]
WantedBy=timers.target
```

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now zanao-monitor.timer
systemctl list-timers zanao-monitor.timer
```

查看日志：

```bash
journalctl -u zanao-monitor.service -n 100 --no-pager
tail -n 100 logs/monitor.log
```
