# 菲律宾每日简报机器人 - 企业机器人版

每日自动抓取马尼拉天气（7天预报）和汇率，推送至钉钉群。

## 功能特点

- **7天天气预报**: 使用Open-Meteo API获取马尼拉天气数据
- **实时汇率**: 使用Juhe.cn API获取CNY→PHP汇率
- **极端天气预警**: 风速>60km/h 或 日降雨>30mm时自动预警
- **多群支持**: 支持向多个钉钉群发送简报
- **企业机器人**: 使用钉钉企业机器人API（非webhook方式）

## 文件结构

```
.
├── main.py                 # 主程序（菲律宾简报+群发）
├── dingtalk_client.py      # 钉钉API封装（含群ID查询）
├── get_group_id.py         # 一次性脚本：根据chatId获取open_conversation_id
├── groups.json             # 群ID配置文件（包含open_conversation_id）
├── .env                    # 环境变量
├── requirements.txt        # 依赖
├── deploy.sh               # 部署脚本
└── README.md               # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```
JUHE_API_KEY=你的聚合数据API密钥
DINGTALK_CLIENT_ID=钉钉应用的AppKey
DINGTALK_CLIENT_SECRET=钉钉应用的AppSecret
```

### 3. 获取群open_conversation_id

**前提**: 确保机器人已加入目标群

```bash
python3 get_group_id.py 161775015441
```

按提示输入群名称，成功后配置将保存到 `groups.json`。

### 4. 手动测试运行

```bash
python3 main.py
```

### 5. 部署到ECS

上传代码到ECS后运行：

```bash
chmod +x deploy.sh
./deploy.sh
```

## 钉钉权限配置

确保钉钉应用已开通以下权限：

- ✅ `qyapi_robot_sendmsg` - 机器人发送消息
- ✅ `InterConnect.Common.ReadWrite` - 群管理权限
- ✅ Stream模式已设置

## 定时任务配置

Crontab配置（每天北京时间8:00运行）：

```bash
0 0 * * * cd /opt/daily-briefing && /usr/bin/python3 main.py >> /var/log/daily-briefing/briefing.log 2>&1
```

## 消息格式示例

```
🇵🇭 菲律宾·马尼拉 7日简报

📅 日期：2024-02-05
💱 汇率：1 CNY = 7.85 PHP

━━━━━━━━━━━━━━━━━━━━━━
📊 7天天气预报

日期     星期   天气      温度      降雨   风速
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
02/05    周二   ☀️晴      24~32℃   无雨   12km/h
02/06    周三   🌤️多云    25~33℃   2mm    15km/h
02/07    周四   🌧️小雨    24~30℃   8mm    22km/h
02/08    周五   🌧️中雨    23~29℃   25mm   35km/h
02/09    周六   ⛈️暴雨    22~28℃   45mm   55km/h
⚠️ 02/09 周六: 日降雨量达45mm，请注意防雨
02/10    周日   ☀️晴      24~31℃   无雨   10km/h
02/11    周一   🌤️多云    25~33℃   1mm    12km/h

━━━━━━━━━━━━━━━━━━━━━━
*数据来自Open-Meteo和Juhe.cn*
```

## 扩展新群

如需添加更多群：

1. 手机钉钉 → 把机器人拉入新群
2. 获取新群的chatId
3. 运行 `python3 get_group_id.py <新群chatId>`
4. groups.json会自动追加新群配置

## 日志查看

```bash
# 实时查看日志
tail -f /var/log/daily-briefing/briefing.log
```

## 故障排查

### 获取群ID失败
- 确认机器人已加入该群
- 确认chatId正确
- 确认钉钉应用权限已开通

### 发送消息失败
- 检查AccessToken是否过期（自动刷新）
- 确认open_conversation_id正确
- 查看日志获取详细错误信息

### 天气/汇率获取失败
- 检查网络连接
- 确认API密钥配置正确
- 检查API调用次数限制
