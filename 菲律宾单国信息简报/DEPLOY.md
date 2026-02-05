# 多城市简报机器人 - 部署文档

## 项目概述

本项目支持4个东南亚城市的每日简报推送：
- 🇵🇭 菲律宾 - 马尼拉 (Manila)
- 🇻🇳 越南 - 胡志明市 (Ho Chi Minh City)
- 🇮🇩 印尼 - 雅加达 (Jakarta)
- 🇲🇾 马来西亚 - 吉隆坡 (Kuala Lumpur)

每个机器人每天自动推送天气和汇率信息到钉钉群。

---

## 快速开始

### 方式一：全新安装（推荐）

```bash
# 1. 上传项目到服务器
scp -r ./菲律宾单国信息简报 root@your-server:/opt/philippines-briefing/

# 2. 登录服务器并运行安装脚本
cd /opt/philippines-briefing/菲律宾单国信息简报
sudo ./install.sh

# 3. 配置环境变量
vim .env

# 4. 配置钉钉群组
python3 interactive_setup.py

# 5. 运行健康检查
python3 health_check.py

# 6. 部署
./deploy.sh --test
```

### 方式二：更新部署

```bash
# 1. 上传更新后的代码
scp -r ./菲律宾单国信息简报/* root@your-server:/opt/philippines-briefing/菲律宾单国信息简报/

# 2. 登录服务器并运行部署脚本
cd /opt/philippines-briefing/菲律宾单国信息简报
./deploy.sh
```

---

## 目录结构

```
菲律宾单国信息简报/
├── main.py                   # 主入口程序
├── bots/                     # 机器人模块
│   ├── __init__.py
│   ├── base_bot.py          # 基础机器人类（含汇率监控）
│   ├── city_bot.py          # 城市机器人实现
│   ├── bot_factory.py       # 机器人工厂
│   └── exchange_monitor.py  # 汇率监控独立模块
├── config/                   # 配置文件
│   └── bots.json            # 机器人配置（4个城市）
├── systemd/                  # systemd服务文件
│   ├── daily-briefing.service
│   └── daily-briefing.timer
├── logrotate/                # 日志轮转配置
│   └── daily-briefing
├── data/                     # 数据目录
│   └── exchange_history.json # 汇率历史记录
├── groups.json              # 钉钉群配置
├── .env                     # 环境变量（需手动创建）
├── requirements.txt         # Python依赖
├── install.sh               # 首次安装脚本
├── deploy.sh                # 部署脚本
├── health_check.py          # 健康检查脚本
├── interactive_setup.py     # 交互式群配置工具
└── DEPLOY.md               # 本文档
```

---

## 部署方式对比

| 特性 | crontab | systemd |
|------|---------|---------|
| 配置复杂度 | 简单 | 中等 |
| 日志管理 | 需手动配置 | 集成journald |
| 时区支持 | 需手动设置 | 原生支持 |
| 失败重试 | 不支持 | 支持Persistent |
| 随机延迟 | 不支持 | 支持RandomizedDelaySec |
| 查看状态 | 需查看日志 | systemctl status |

**推荐**：生产环境使用systemd，简单场景使用crontab。

---

## 详细部署步骤

### 1. 上传代码到服务器

```bash
# 本地执行（在项目目录）
scp -r ./* root@your-ecs-ip:/opt/philippines-briefing/菲律宾单国信息简报/
```

### 2. 运行安装脚本（首次安装）

```bash
# 登录服务器
cd /opt/philippines-briefing/菲律宾单国信息简报
chmod +x install.sh
sudo ./install.sh
```

安装脚本会自动完成：
- 安装系统依赖（Python3、pip、git、logrotate）
- 创建专用用户 `briefing`
- 创建应用目录和日志目录
- 创建Python虚拟环境
- 安装Python依赖
- 配置日志轮转

### 3. 配置环境变量

创建 `.env` 文件：

```bash
cd /opt/philippines-briefing/菲律宾单国信息简报
vim .env
```

添加以下内容：

```
# 钉钉机器人配置
DINGTALK_CLIENT_ID=your_client_id
DINGTALK_CLIENT_SECRET=your_client_secret
DING_ROBOT_CODE=your_robot_code

# Juhe汇率API密钥
JUHE_API_KEY=your_juhe_api_key
```

### 4. 配置钉钉群

#### 方式一：使用交互式工具（推荐）

```bash
python3 interactive_setup.py
```

按提示操作：
1. 访问 https://open.dingtalk.com/tools/explorer/jsapi?id=11654
2. 扫码登录获取 AccessToken
3. 调用"查询群信息"API获取 chatId 和 openConversationId
4. 将JSON数据粘贴到交互式工具中

#### 方式二：手动配置

编辑 `groups.json`：

```json
{
  "groups": [
    {
      "name": "简报信息",
      "chat_id": "your_chat_id",
      "open_conversation_id": "your_open_conversation_id"
    }
  ]
}
```

### 5. 运行健康检查

```bash
# 完整检查
python3 health_check.py

# 仅检查配置
python3 health_check.py --config

# 仅测试API连接
python3 health_check.py --api
```

### 6. 运行部署脚本

```bash
# 标准部署
./deploy.sh

# 部署并测试运行
./deploy.sh --test

# 仅检查环境
./deploy.sh --check

# 配置systemd定时器（需要root权限）
sudo ./deploy.sh --systemd
```

### 7. 配置定时任务

#### 方式A：使用systemd（推荐）

```bash
# 配置systemd定时器
sudo ./deploy.sh --systemd

# 查看定时器状态
systemctl status daily-briefing.timer

# 查看服务日志
journalctl -u daily-briefing.service -f

# 手动触发运行
systemctl start daily-briefing.service

# 停止定时器
systemctl stop daily-briefing.timer

# 禁用开机启动
systemctl disable daily-briefing.timer
```

#### 方式B：使用crontab

```bash
# 编辑crontab
crontab -e

# 添加以下行（每天上海时间8:30运行）
30 8 * * * cd /opt/philippines-briefing/菲律宾单国信息简报 && /usr/bin/python3 main.py >> /var/log/daily-briefing/briefing.log 2>&1

# 查看crontab
crontab -l
```

---

## 配置文件说明

### bots.json

机器人配置文件，位于 `config/bots.json`：

```json
{
  "bots": [
    {
      "name": "菲律宾简报机器人",
      "country": "PH",
      "city": "Manila",
      "latitude": 14.5995,
      "longitude": 120.9842,
      "currency": "PHP",
      "currency_name": "菲律宾比索",
      "target_currency": "CNY",
      "exchange_api": "juhe",
      "groups": ["简报信息"],
      "schedule": "08:30",
      "timezone": "Asia/Shanghai"
    }
  ]
}
```

### groups.json

群配置文件，位于项目根目录：

```json
{
  "groups": [
    {
      "name": "简报信息",
      "chat_id": "cid...",
      "open_conversation_id": "cid..."
    }
  ]
}
```

---

## 汇率异常监控

系统已集成汇率异常监控功能，当以下情况发生时会发送钉钉告警：

### 监控场景

1. **API返回空数据** - 汇率API返回空结果
2. **汇率值为0或负数** - 汇率值异常
3. **汇率波动超过阈值** - 单日波动超过5%（可配置）
4. **API调用失败** - 网络错误或API服务异常

### 告警内容

告警消息包含以下信息：
- 异常类型
- 货币对（如 CNY/PHP）
- 当前汇率
- 上次汇率
- 波动幅度
- 时间戳

### 配置选项

在 `bots/base_bot.py` 中可以调整以下参数：

```python
# 汇率波动阈值 (%)
EXCHANGE_RATE_CHANGE_THRESHOLD = 5.0

# 汇率合理范围
EXCHANGE_RATE_MIN = 0.01
EXCHANGE_RATE_MAX = 10000.0
```

### 历史记录

汇率历史记录存储在 `data/exchange_history.json`，用于波动检测。

---

## 消息格式示例

推送的消息格式如下：

```
菲律宾马尼拉 今日简报

📅 日期：2026-02-05
💱 汇率：1 CNY = 7.85 PHP

## 📊 7天天气预报

| 日期  | 星期 | 天气   | 温度    | 降雨 | 风速   |
| ---- | ---- | ---- | ---- | ---- | ---- |
| 02/05 | 周二 | ☀️晴  | 24~32℃ | 无雨 | 🍃静风 |
| 02/06 | 周三 | 🌤️多云 | 25~33℃ | 小雨 | 🌿微风 |
...

*数据来自Open-Meteo和Juhe.cn*
```

### 天气定性描述

**风速等级：**
- 🍃 静风 (0-5 km/h)
- 🌿 微风 (5-20 km/h)
- 🍃 轻风 (20-40 km/h)
- 🌾 和风 (40-60 km/h)
- 💨 强风 (60-80 km/h)
- 🌪️ 大风 (>80 km/h)

**降雨等级：**
- 无雨 (0 mm)
- 🌦️ 小雨 (0.1-5 mm)
- 🌧️ 中雨 (5-20 mm)
- 🌧️ 大雨 (20-50 mm)
- ⛈️ 暴雨 (>50 mm)

**极端天气预警：**
当风速 >60km/h 或 日降雨 >30mm 时，会在消息末尾显示预警信息。

---

## 常见问题排查

### 1. 健康检查失败

```bash
# 运行健康检查查看具体问题
python3 health_check.py

# 常见问题和解决方案：
# - Python版本过低: 升级Python到3.8+
# - 依赖缺失: pip3 install -r requirements.txt
# - 环境变量未配置: 创建.env文件
# - 配置文件错误: 检查JSON格式
```

### 2. 消息发送失败

```bash
# 检查钉钉配置
python3 health_check.py --api

# 常见原因：
# - Client ID/Secret 错误
# - 机器人未添加到群组
# - open_conversation_id 错误
# - AccessToken过期（会自动刷新）
```

### 3. 汇率数据获取失败

```bash
# 测试汇率API
python3 health_check.py --api

# 常见原因：
# - JUHE_API_KEY 未配置或错误
# - API额度用完
# - 网络问题
```

### 4. 定时任务不执行

**systemd方式：**
```bash
# 检查定时器状态
systemctl status daily-briefing.timer

# 检查定时器是否启用
systemctl is-enabled daily-briefing.timer

# 查看定时器触发时间
systemctl list-timers daily-briefing.timer

# 手动测试运行
systemctl start daily-briefing.service
journalctl -u daily-briefing.service
```

**crontab方式：**
```bash
# 检查crontab配置
crontab -l

# 检查cron服务状态
service cron status
# 或
systemctl status crond

# 查看cron日志
tail -f /var/log/cron
# 或
grep CRON /var/log/syslog
```

### 5. 日志文件过大

```bash
# 手动清理日志
cd /var/log/daily-briefing
ls -lh

# 清空当前日志
> briefing.log

# 或使用logrotate手动轮转
logrotate -f /etc/logrotate.d/daily-briefing
```

### 6. 如何查看运行日志

```bash
# systemd方式
journalctl -u daily-briefing.service -f

# crontab方式
tail -f /var/log/daily-briefing/briefing.log

# 查看最近100行
tail -n 100 /var/log/daily-briefing/briefing.log

# 查看包含错误的日志
grep ERROR /var/log/daily-briefing/briefing.log
```

---

## 更新/回滚指南

### 更新代码

```bash
cd /opt/philippines-briefing/菲律宾单国信息简报

# 备份当前配置
cp .env .env.backup
cp groups.json groups.json.backup

# 上传新代码
# scp -r ./* root@your-server:/opt/philippines-briefing/菲律宾单国信息简报/

# 运行部署脚本
./deploy.sh

# 运行健康检查
python3 health_check.py
```

### 回滚

```bash
cd /opt/philippines-briefing/菲律宾单国信息简报

# 恢复配置
mv .env.backup .env
mv groups.json.backup groups.json

# 重新部署
./deploy.sh
```

---

## 监控和告警配置

### 系统监控

建议配置以下监控：

1. **磁盘空间监控** - 防止日志占满磁盘
2. **内存监控** - 确保系统有足够内存
3. **定时任务监控** - 确保任务按时执行

### 钉钉告警

汇率异常时系统会自动发送告警到配置的钉钉群。

如需添加更多告警场景，可以修改 `bots/base_bot.py` 中的 `send_exchange_alert` 方法。

---

## 添加新城市

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
  "timezone": "Asia/Shanghai"
}
```

---

## 技术栈

- Python 3.8+
- requests - HTTP请求
- python-dotenv - 环境变量管理
- pytz - 时区处理
- Open-Meteo API - 天气数据
- Juhe.cn API - 汇率数据
- 钉钉开放平台 API - 消息推送

---

## 维护说明

- 定期检查 `.env` 文件中的API密钥是否过期
- 监控日志文件大小，必要时进行轮转
- 如需修改消息格式，编辑 `bots/city_bot.py` 中的 `build_message` 方法
- 汇率监控阈值可在 `bots/base_bot.py` 中调整
