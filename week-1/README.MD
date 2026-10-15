# Linux & DevOps Learning Project

A hands-on project to practise Linux administration, Bash scripting, monitoring, logging, and automation.

## Project Structure

```text
week-1/
├── files/
├── logs/
└── scripts/
    ├── file_read.sh
    ├── log_reports.sh
    ├── server_monitor.sh
    └── strict_mode.sh
```

## Features

- Linux system monitoring: CPU, memory, disk, and uptime.
- Threshold-based alerts and HTTPS checks.
- Daily logging and automatic log retention.
- Cron scheduling for recurring monitoring.
- Log analysis and Bash error handling.
- Exit codes for automation: `0` = PASS, `1` = FAIL, `2` = INCOMPLETE.

## Usage

Run the monitoring script from the repository root:

```bash
bash week-1/scripts/server_monitor.sh cron
```

Test an alert with a low memory threshold:

```bash
MEMORY_THRESHOLD=1 bash week-1/scripts/server_monitor.sh cron
```

## Learning Outcomes

Practised Linux commands, Bash scripting, log processing, permissions, cron, monitoring, and Git.

## Future Improvements

- Email or webhook notifications.
- Automated tests.
- Improved alert reporting.
