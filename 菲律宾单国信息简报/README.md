# 多城市每日简报机器人

每日自动抓取东南亚4个国家的天气（7天预报）和汇率，推送至钉钉群。

## 支持国家

| 国家 | 城市 | 货币 |
|------|------|------|
| 🇵🇭 菲律宾 | 马尼拉 (Manila) | PHP 比索 |
| 🇻🇳 越南 | 胡志明市 (Ho Chi Minh City) | VND 盾 |
| 🇮🇩 印尼 | 雅加达 (Jakarta) | IDR 卢比 |
| 🇲🇾 马来西亚 | 吉隆坡 (Kuala Lumpur) | MYR 林吉特 |

## 功能特点

- **7天天气预报**: 使用 Open-Meteo API 获取天气数据
- **实时汇率**: 使用 Juhe.cn API 获取汇率（CNY→当地货币）
- **汇率异常监控**: API异常、汇率波动过大(>5%)时自动告警
- **极端天气预警**: 风速>60km/h 时自动预警
- **多钉钉应用**: 每个国家使用独立的钉钉应用发送消息
- **多群支持**: 支持向多个钉钉群发送简报

## 文件结构

```
菲律宾单国信息简报/
├── main.py                      # 主程序入口
├── bots/                        # 机器人模块
│   ├── __init__.py
│   ├── base_bot.py             # 基础机器人类（含汇率监控）
│   ├── city_bot.py             # 城市机器人实现
│   ├── bot_factory.py          # 机器人工厂
│   └── exchange_monitor.py     # 汇率监控模块
├── config/
│   └── bots.json               # 机器人配置（4个国家+钉钉应用）
├── systemd/                     # systemd服务文件
│   ├── daily-briefing.service
│   └── daily-briefing.timer
├── logrotate/
│   └── daily-briefing          # 日志轮转配置
├── data/
│   └── exchange_history.json   # 汇率历史记录
├── groups.json                  # 钉钉群配置
├── .env                         # 环境变量（Juhe API密钥）
├── requirements.txt             # Python依赖
├── install.sh                   # 首次安装脚本
├── deploy.sh                    # 部署脚本
├── health_check.py              # 健康检查脚本
├── test_dingtalk.py             # 钉钉连接测试
├── 获取群ID操作文档.md          # 获取群ID教程
└── README.md                    # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# Juhe汇率API密钥（所有国家共用）
JUHE_API_KEY=你的聚合数据API密钥
```

### 3. 配置钉钉应用

编辑 `config/bots.json`，为每个国家配置独立的钉钉应用：

```json
{
  "name": "菲律宾简报机器人",
  "country": "PH",
  "city": "Manila",
  ...
  "dingtalk": {
    "client_id": "dingxxxxxxxxxxxxxxxx",
    "client_secret": "xxxxxxxxxxxxxxxx",
    "robot_code": "dingxxxxxxxxxxxxxxxx"
  }
}
```

### 4. 配置钉钉群

编辑 `groups.json`：

```json
{
  "groups": [
    {
      "name": "简报信息",
      "open_conversation_id": "cidxxxxxxxxxxxxxxxx"
    }
  ]
}
```

**获取 open_conversation_id 的方法**：详见 `获取群ID操作文档.md`

### 5. 健康检查

```bash
python health_check.py
```

### 6. 测试运行

```bash
# 列出所有机器人
python main.py --list

# 运行单个国家
python main.py --country PH    # 菲律宾
python main.py --country VN    # 越南
python main.py --country ID    # 印尼
python main.py --country MY    # 马来西亚

# 运行所有国家
python main.py
```

### 7. 部署到服务器

首次安装：

```bash
sudo ./install.sh
```

更新部署：

```bash
./deploy.sh
```

## 定时任务配置

### 方式一：systemd（推荐）

```bash
sudo ./deploy.sh --systemd

# 查看定时器状态
systemctl status daily-briefing.timer

# 查看日志
journalctl -u daily-briefing.service -f
```

### 方式二：crontab

```bash
crontab -e

# 添加（每天北京时间8:30运行）
30 8 * * * cd /opt/philippines-briefing/菲律宾单国信息简报 && /usr/bin/python3 main.py >> /var/log/daily-briefing/briefing.log 2>&1
```

## 消息格式示例

```
菲律宾马尼拉 今日简报

📅 日期：2026-02-05
💱 汇率：1 CNY = 8.47 PHP

## 📊 7天天气预报

| 日期 | 星期 | 天气 | 温度 | 风速 |
| ---- | ---- | ---- | ---- | ---- |
| 02/05 | 周二 | ☀️晴 | 24~32℃ | 🍃静风 |
| 02/06 | 周三 | 🌤️多云 | 25~33℃ | 🌿微风 |
| 02/07 | 周四 | 🌧️小雨 | 24~30℃ | 🌿微风 |
| 02/08 | 周五 | 🌧️中雨 | 23~29℃ | 🍃轻风 |
| 02/09 | 周六 | ⛈️暴雨 | 22~28℃ | 🌾和风 |
| 02/10 | 周日 | ☀️晴 | 24~31℃ | 🌿微风 |
| 02/11 | 周一 | 🌤️多云 | 25~33℃ | 🍃静风 |

## 🚨 极端天气预警

⚠️ **02/09 周六**: 风速达65.2km/h，请注意防风安全

*数据来自Open-Meteo和Juhe.cn*
```

## 天气描述说明

**风速等级：**
- 🍃 静风 (0-5 km/h)
- 🌿 微风 (5-20 km/h)
- 🍃 轻风 (20-40 km/h)
- 🌾 和风 (40-60 km/h)
- 💨 强风 (60-80 km/h)
- 🌪️ 大风 (>80 km/h)

## 汇率异常监控

系统会自动监控汇率异常情况：

1. **API返回空数据** - 发送告警
2. **汇率值为0或负数** - 发送告警
3. **汇率波动>5%** - 发送告警（对比历史记录）
4. **API调用失败** - 发送告警

告警消息示例：
```
🚨 汇率异常告警

监控器: 菲律宾简报机器人
货币对: CNY/PHP
异常类型: 汇率波动过大: 6.23% (从 7.85 到 8.34, 阈值 5%)
当前汇率: 8.34
波动幅度: +6.23%
上次汇率: 7.85

时间: 2026-02-05 08:30:15

请检查汇率API或联系管理员。
```

## 故障排查

### 健康检查

```bash
# 完整检查
python health_check.py

# 仅检查配置
python health_check.py --config

# 仅测试API连接
python health_check.py --api

# 测试钉钉发送
python test_dingtalk.py
```

### 钉钉连接失败

1. 检查 Client ID / Client Secret 是否正确
2. 确认钉钉应用已添加到目标群
3. 检查应用权限：
   - ✅ `qyapi_robot_sendmsg` - 机器人发送消息
   - ✅ `InterConnect.Common.ReadWrite` - 群管理权限

### 汇率获取失败

1. 检查 `JUHE_API_KEY` 是否配置正确
2. 确认 API 调用次数未超限
3. 检查网络连接

### 定时任务不执行

**systemd方式：**
```bash
systemctl status daily-briefing.timer
systemctl list-timers daily-briefing.timer
journalctl -u daily-briefing.service
```

**crontab方式：**
```bash
crontab -l
tail -f /var/log/cron
grep CRON /var/log/syslog
```

## 添加新国家

编辑 `config/bots.json`，添加新的机器人配置：

```json
{
  "name": "新加坡简报机器人",
  "country": "SG",
  "city": "Singapore",
  "latitude": 1.3521,
  "longitude": 103.8198,
  "currency": "SGD",
  "currency_name": "新加坡元",
  "target_currency": "CNY",
  "exchange_api": "juhe",
  "groups": ["简报信息"],
  "schedule": "08:30",
  "timezone": "Asia/Shanghai",
  "dingtalk": {
    "client_id": "dingxxxxxxxxxxxxxxxx",
    "client_secret": "xxxxxxxxxxxxxxxx",
    "robot_code": "dingxxxxxxxxxxxxxxxx"
  }
}
```

## 日志查看

```bash
# systemd方式
journalctl -u daily-briefing.service -f

# crontab方式
tail -f /var/log/daily-briefing/briefing.log

# 查看最近100行
tail -n 100 /var/log/daily-briefing/briefing.log

# 查看错误日志
grep ERROR /var/log/daily-briefing/briefing.log
```

## 技术栈

- Python 3.8+
- requests - HTTP请求
- python-dotenv - 环境变量管理
- pytz - 时区处理
- Open-Meteo API - 天气数据
- Juhe.cn API - 汇率数据
- 钉钉开放平台 API - 消息推送

## 文档索引

- `DEPLOY.md` - 详细部署文档
- `获取群ID操作文档.md` - 获取钉钉群ID教程
- `CLAUDE.md` - 开发规范
- `AGENTS.md` - 架构设计
