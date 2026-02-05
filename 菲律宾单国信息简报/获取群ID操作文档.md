# 获取钉钉群 openConversationId 操作文档

## 方法一：使用 JSAPI Explorer（推荐）

这是最快捷的方法，可以直接在浏览器中获取群的 openConversationId。

### 前置条件

1. 你是该钉钉群的成员
2. 手机已安装钉钉 APP 并登录

### 操作步骤

#### 步骤 1：访问 JSAPI Explorer

打开浏览器，访问以下链接：

```
https://n.dingtalk.com/dingding/open-platform-jsapi-explorer-terminal/index.html
```

#### 步骤 2：选择 API

在页面左侧导航栏中，依次选择：

```
API 即时通信IM → 会话管理 → chooseChat
```

或者直接在搜索框中输入 `chooseChat` 搜索。

#### 步骤 3：配置参数

在右侧的参数配置区域，输入：

| 参数名 | 值 | 说明 |
|--------|-----|------|
| corpId | 你的CorpId | 在钉钉开放平台首页获取 |

**如何获取 CorpId：**
1. 访问 [钉钉开放平台](https://open.dingtalk.com/)
2. 登录后进入首页
3. 在页面顶部或企业信息区域找到 **CorpId**

#### 步骤 4：运行调试

1. 点击页面上的 **"运行调试"** 按钮
2. 页面会显示一个 **二维码**
3. 使用**手机钉钉**扫描二维码

#### 步骤 5：选择群组

1. 扫描成功后，手机钉钉会显示群列表
2. 选择你要配置的群（如："简报信息"）
3. 点击确认

#### 步骤 6：获取结果

返回浏览器，在页面下方的 **"返回结果"** 区域可以看到：

```json
{
  "chatId": "chatxxxxxxxxxxxxxxxxxxxx",
  "title": "简报信息",
  "openConversationId": "cidxxxxxxxxxxxxxxxxxxxx"
}
```

**记录下 `openConversationId` 的值**，这就是配置文件中需要的群ID。

---

## 方法二：使用 API 调试工具（开发者适用）

如果你需要批量获取或有更多自定义需求，可以使用 API 方式。

### 步骤 1：获取 AccessToken

```bash
curl -X POST 'https://api.dingtalk.com/v1.0/oauth2/accessToken' \
  -H 'Content-Type: application/json' \
  -d '{
    "appKey": "YOUR_APP_KEY",
    "appSecret": "YOUR_APP_SECRET"
  }'
```

### 步骤 2：转换 chatId 为 openConversationId

如果你已经有 `chatId`，可以通过以下接口转换：

```bash
curl -X POST 'https://api.dingtalk.com/v1.0/im/chat/{chatId}/convertToOpenConversationId' \
  -H 'x-acs-dingtalk-access-token: YOUR_ACCESS_TOKEN'
```

---

## 配置到项目

获取到 `openConversationId` 后，更新 `groups.json` 文件：

```json
{
  "groups": [
    {
      "name": "简报信息",
      "open_conversation_id": "cidxxxxxxxxxxxxxxxxxxxx"
    }
  ]
}
```

---

## 常见问题

### Q1: 扫码后提示"没有权限"

**原因**：你可能不是该群的管理员或成员

**解决**：
- 确保你是群的成员
- 或者联系群管理员将你添加为群成员

### Q2: 获取到的 openConversationId 无法使用

**原因**：
1. 机器人应用没有被添加到群中
2. 机器人没有发送消息的权限

**解决**：
1. 在钉钉群设置中添加机器人应用
2. 确保机器人有"群消息发送"权限

### Q3: 如何验证 openConversationId 是否正确

运行健康检查脚本：

```bash
python3 health_check.py --api
```

如果显示"钉钉API连接成功"，说明配置正确。

---

## 下一步

获取到 `openConversationId` 后，请提供给我，我会更新 `groups.json` 配置文件。

目前配置状态：

| 国家 | Client ID | Client Secret | Robot Code | 群 openConversationId |
|------|-----------|---------------|------------|----------------------|
| 菲律宾 | 待提供 | 待提供 | 待提供 | 待获取 |
| 越南 | ✅ | ✅ | ✅ | 待获取 |
| 马来 | ✅ | ✅ | ✅ | 待获取 |
| 印尼 | ✅ | ✅ | ✅ | 待获取 |

请提供：
1. **菲律宾的钉钉应用配置**（Client ID, Client Secret, RobotCode）
2. **简报信息群的 openConversationId**（通过上述方法获取）
