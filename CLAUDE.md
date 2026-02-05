# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在本仓库中工作的指导。

## 语言规范

- **思考**：内部推理和分析使用中文
- **沟通**：回复用户查询使用中文
- **代码注释**：所有代码注释使用中文
- **文档**：所有文档使用中文

## 项目概述

东南亚四国每日要闻与生活指数推送助手 - 一个每日简报自动化工具，抓取菲律宾、印度尼西亚、越南、马来西亚这四个东南亚国家的天气、汇率和新闻，并将格式化报告推送到钉钉群聊。

## 开发命令

### 环境设置
```bash
# 安装依赖
pip install -r requirements.txt

# 或以可编辑包形式安装
pip install -e .
```

### 运行程序
```bash
# 运行简报（需要带有 API 密钥的 .env 文件）
python main.py

# 或使用安装的脚本
briefing
```

### 环境变量
复制 `.env.example` 到 `.env` 并配置：
- `NEWSDATA_API_KEY` - 来自 https://newsdata.io/ 的 API 密钥
- `JUHE_API_KEY` - 来自 https://www.juhe.cn/docs/api/id/80 的 API 密钥
- `DINGTALK_WEBHOOK` - 钉钉机器人 webhook URL（需要包含安全关键词 "简报"）

## 架构

### 数据流
1. **天气**：Open-Meteo API（免费，无需密钥）- 根据坐标获取每日预报
2. **汇率**：聚合数据 API（需要密钥）- 人民币兑换当地货币
3. **新闻**：NewsData.io API（需要密钥）- 每个国家获取 3 条中文新闻
4. **输出**：钉钉 webhook - Markdown 格式消息

### 国家配置
国家在 `main.py:16` 的 `COUNTRIES` 字典中定义，包含：
- `lat/lon`：天气 API 的坐标
- `news_code`：新闻 API 的 ISO 国家代码
- `currency`：汇率 API 的货币代码

### 关键函数
- `get_weather(lat, lon)` - 从 Open-Meteo v1/forecast 端点获取数据
- `get_exchange_rate(currency)` - 从聚合数据 onebox 汇率端点获取数据
- `get_news(country_code)` - 从 NewsData.io 获取中文语言过滤的新闻
- `build_message(...)` - 格式化 Markdown 消息并附带天气提示
- `send_to_dingtalk(...)` - 将 Markdown 内容 POST 到 webhook

## 部署

GitHub Actions 工作流（`.github/workflows/daily_push.yml`）每天北京时间 08:00（UTC 00:00）运行。必须在仓库设置中配置以下 Secrets：
- `NEWSDATA_API_KEY`
- `JUHE_API_KEY`
- `DINGTALK_WEBHOOK`

也支持通过 `workflow_dispatch` 手动触发。
