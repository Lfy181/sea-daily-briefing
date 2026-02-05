# AGENTS.md - 菲律宾简报机器人开发指南

## 项目概述

Python 钉钉机器人项目，每日自动抓取马尼拉天气（7天预报）和汇率，推送至钉钉群。

## 开发环境

- Python 3.9+
- 虚拟环境: `.venv`
- 依赖管理: `requirements.txt`

## 构建与测试命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行主程序
python3 main.py

# 测试API（独立测试脚本）
python3 test_api.py

# 运行单个测试函数
python3 -c "from test_api import test_send_message; test_send_message()"

# 语法检查
python3 -m py_compile main.py dingtalk_client.py

# 查看日志
tail -f /var/log/daily-briefing/briefing.log
```

## 代码风格指南

### 导入顺序

1. 标准库 (`os`, `sys`, `json`, `logging`, `requests`)
2. 第三方库 (`dotenv`)
3. 本地模块（按字母顺序）

```python
import json
import logging
import os
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv
```

### 命名约定

- **类**: `PascalCase` - `DingTalkRobot`, `DingTalkClient`
- **函数/变量**: `snake_case` - `get_weather_forecast()`, `exchange_rate`
- **常量**: `UPPER_SNAKE_CASE` - `WEATHER_API_URL`, `MANILA_LAT`
- **私有方法**: 前缀 `_` - `_get_access_token()`
- **类型注解**: 函数参数和返回值必须标注类型

```python
class DingTalkRobot:
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, app_key: str, app_secret: str, robot_code: str) -> None:
        self.app_key = app_key

    def send_markdown_message(self, open_conversation_id: str, title: str, text: str) -> bool:
        ...
```

### 格式化

- 行长度: 最大 120 字符
- 缩进: 4 空格（不使用 Tab）
- 字符串引号: 双引号优先
- 模块级 docstring: 使用 `"""三重双引号"""`
- 函数 docstring: Google Style

```python
def get_weather_forecast() -> dict:
    """
    获取马尼拉7天天气预报。

    Returns:
        dict: 包含 forecast 列表和 success 状态的字典
    """
    ...
```

### 错误处理

- 使用 `try/except` 捕获具体异常
- 始终记录或抛出错误
- API 调用设置 `timeout` 参数
- 区分用户错误和系统错误

```python
try:
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()
except requests.exceptions.Timeout:
    logger.error("API请求超时")
    return None
except requests.exceptions.RequestException as e:
    logger.error(f"API请求失败: {e}")
    raise
```

### 日志与消息输出

- 使用 `logger` 而非 `print`（main.py）
- 控制台输出使用统一格式
- 消息前缀规范: `[模块名] 操作描述 状态`

**日志格式（main.py）:**
```python
logger.info("[钉钉] AccessToken获取成功")
logger.error(f"[钉钉] 发送消息失败: {error_code} - {error_msg}")
```

**控制台输出格式（工具脚本）:**
```python
print(f"[INFO] 正在获取天气数据...")
print(f"[SUCCESS] 成功获取{len(forecast)}天预报")
print(f"[ERROR] 获取天气数据失败: {e}")
```

### 文件结构

```
.
├── main.py              # 主程序（简报生成+群发）
├── dingtalk_client.py   # 钉钉API封装
├── get_group_id.py      # 群ID查询工具
├── test_api.py          # API测试脚本
├── send_bulletin.py     # 简报发送脚本
├── groups.json          # 群配置
├── .env                 # 环境变量
├── requirements.txt     # 依赖
└── AGENTS.md            # 本文件
```

### API 调用规范

- HTTP 请求必须设置 `timeout`
- 环境变量使用 `os.getenv()` 读取，提供默认值
- 敏感配置从 `.env` 加载
- API 响应检查 `success`/`error_code` 字段

```python
def get_exchange_rate() -> dict:
    api_key = os.getenv("JUHE_API_KEY")
    if not api_key:
        logger.error("未配置JUHE_API_KEY环境变量")
        return {"rate": None, "success": False}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.json().get("error_code") == 0:
            return {"rate": result, "success": True}
    except Exception as e:
        logger.error(f"获取汇率失败: {e}")
```

### Markdown 消息格式

钉钉消息使用 `sampleMarkdown` 类型，参数格式：

```python
msgParam = json.dumps({
    "title": "标题",
    "text": "Markdown内容",
    "single_title": "查看更多",
    "single_url": "https://example.com"
}, ensure_ascii=False)
```

### 部署命令

```bash
# 部署到ECS
chmod +x deploy.sh
./deploy.sh

# 手动运行
python3 main.py >> /var/log/daily-briefing/briefing.log 2>&1
```

### 注意事项

- 切勿提交 `.env` 和 `groups.json` 到版本控制
- 测试时使用测试群 ID，正式环境更换生产配置
- API 密钥和 Token 不得硬编码在代码中
