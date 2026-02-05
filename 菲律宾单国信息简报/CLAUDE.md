# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

菲律宾每日简报机器人 - A Python-based DingTalk bot that sends daily briefings with Manila weather (7-day forecast) and CNY→PHP exchange rates to DingTalk groups.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main briefing bot
python3 main.py

# Query group open_conversation_id by chat_id
python3 get_group_id.py <chat_id>

# Test API connectivity
python3 test_api.py

# Send a test bulletin
python3 send_bulletin.py

# Syntax check
python3 -m py_compile main.py dingtalk_client.py

# View logs (when deployed)
tail -f /var/log/daily-briefing/briefing.log
```

## Architecture

### Core Components

1. **main.py** - Main entry point. Fetches weather from Open-Meteo API, exchange rate from Juhe.cn, builds Markdown message, and sends to all groups in `groups.json`.

2. **dingtalk_client.py** - DingTalk API client with token management. Provides `DingTalkClient` class for getting access tokens and sending messages via DingTalk's v1.0 API.

3. **get_group_id.py** - Utility script to convert `chat_id` to `open_conversation_id` using DingTalk's interconnection API. Saves results to `groups.json`.

### Data Flow

1. Weather API (Open-Meteo) → 7-day forecast with WMO weather codes
2. Exchange API (Juhe.cn) → CNY→PHP rate
3. `build_message()` → Markdown table format with extreme weather alerts (>60km/h wind or >30mm rain)
4. `DingTalkRobot.send_markdown_message()` → DingTalk group via `open_conversation_id`

### Configuration Files

- **.env** - Environment variables:
  - `JUHE_API_KEY` - Juhe.cn API key for exchange rates
  - `DINGTALK_CLIENT_ID` - DingTalk app AppKey
  - `DINGTALK_CLIENT_SECRET` - DingTalk app AppSecret
  - `DING_ROBOT_CODE` - DingTalk robot code (usually same as AppKey)

- **groups.json** - Group configuration:
  ```json
  {
    "groups": [
      {
        "name": "简报信息",
        "chat_id": "chat6437e92380126a3932600eb22d9b0671",
        "open_conversation_id": "cidjqh5//NCDSwyIjzWWCnRWw=="
      }
    ]
  }
  ```

### Key Classes

- `DingTalkRobot` (main.py:103) - Self-contained robot class with token refresh logic
- `DingTalkClient` (dingtalk_client.py:20) - Alternative client with token caching

### Deployment

- **deploy.sh** - Ubuntu/ECS deployment script. Sets up `/opt/daily-briefing` with crontab for daily UTC 00:00 (Beijing 08:00) execution.

## Code Style (from AGENTS.md)

- Imports: stdlib → third-party → local modules
- Naming: `PascalCase` classes, `snake_case` functions/variables, `UPPER_SNAKE_CASE` constants
- Type annotations required on function signatures
- Max line length: 120 characters, 4-space indent
- Use `logger` in main.py, `print` with `[INFO]`/`[ERROR]` prefixes in utility scripts
- All API calls must include `timeout` parameter
