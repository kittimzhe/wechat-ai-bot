# 微信 AI 定时推送机器人

给**自己的微信**定时推送 AI 生成内容的机器人。

## 工作原理

```
定时器（APScheduler）
   ↓ 到点触发
Python 脚本
   ↓ 调用大模型 API（DeepSeek / 智谱，OpenAI 兼容接口）
生成内容（晨间推送、每日一题、提醒……）
   ↓ 企业微信应用消息 API
你的微信收到「企业微信通知」
```

## 为什么用企业微信而不是公众号？

给"自己/少数人"做定时推送时，企业微信应用消息比公众号更合适：

| | 公众号（个人订阅号） | 企业微信应用消息 |
|---|---|---|
| 注册门槛 | 个人可注册，但无法认证 | 个人免费注册，无需营业执照 |
| 定时主动推送 | ❌ 没有权限 | ✅ 直接推 |
| 消息到达 | 关注公众号的人 | 你自己的微信 |

公众号适合"面向不特定关注者"的场景，以后想做公开的 AI 问答号再扩展（见文末「后续扩展」）。

## 准备工作（约 15 分钟，全部免费）

### 第 1 步：注册企业微信

1. 打开 https://work.weixin.qq.com ，点「立即注册」
2. 选「组织」类型，**个人身份即可，不需要营业执照**，名称随意（如"我的个人助手"）

### 第 2 步：创建自建应用

1. 进入管理后台 →「应用管理」→「自建」→「创建应用」
   名称如"AI 助手"，logo 随意，可见范围选你自己
2. 进入应用详情页，记下：
   - **AgentId**（一串数字）
   - **Secret**（点「查看」会发到手机）
3. 再到「我的企业」→「企业信息」记下**企业ID**（CorpID）
4. 回到应用详情页，找到「**企业可信IP**」，把你电脑的公网出口 IP 加进去
   （浏览器搜"我的 IP"可查；不加的话调用 API 会报 **60020** 错误）

### 第 3 步：让消息出现在微信里

两种方式任选：

- **不装 App（推荐）**：管理后台 →「我的企业」→「微信插件」，用你的个人微信扫码关注。
  之后应用消息会通过微信里的「企业微信通知」送达
- 或直接装「企业微信」App，消息在 App 里收

另外记下你自己的**成员账号（userid）**：后台「通讯录」→ 点开你自己 →「账号」字段。

### 第 4 步：申请 AI Key（二选一）

| 平台 | 地址 | 说明 |
|---|---|---|
| **DeepSeek**（推荐） | https://platform.deepseek.com | 注册后充值几块钱够用很久，`deepseek-chat` 便宜好用 |
| **智谱**（免费） | https://open.bigmodel.cn | 创建 API Key，用免费的 `glm-4-flash` 模型 |

## 运行

需要 Python 3.9+。

```bash
cd wechat-ai-bot

# 1. 安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 配置
cp .env.example .env
# 编辑 .env，填入 企业ID / Secret / AgentId / userid / AI Key

# 3. 先验证微信链路（不调用 AI）
python send_test.py
# → 微信里应收到一条测试消息

# 4. 再验证 AI 链路
python main.py --run 晨间推送
# → 微信里应收到 AI 生成的内容

# 5. 启动定时服务（保持窗口运行）
python main.py
```

## 自动化测试

测试不会调用真实企业微信或 AI 接口：

```bash
pip install -r requirements-dev.txt
pytest -q
```

## 云函数部署

如果使用腾讯云函数、阿里云函数等 Serverless 平台，把入口设置为：

```text
cloud_handler.handler
```

定时器事件可以传入任务名：

```json
{"job": "晨间推送"}
```

不传 `job` 时会执行第一个启用的任务。云函数环境变量配置与 `.env` 中的变量相同。云函数只负责一次触发，不需要启动 `main.py` 常驻进程。

## 项目结构

```
wechat-ai-bot/
├── main.py             # 入口：定时服务 / 手动执行任务
├── cloud_handler.py    # 云函数定时触发入口
├── jobs.py             # 任务定义（改这里定制推送内容和时间）
├── wecom.py            # 企业微信发消息
├── ai_client.py        # 调用大模型
├── config.py           # 读取 .env 配置
├── send_test.py        # 第一步验证脚本
├── tests/              # 不调用真实 API 的自动化测试
├── .env.example        # 配置模板（复制为 .env 后填写）
└── requirements.txt
```

## 自定义推送内容和时间

所有任务在 `jobs.py` 里定义：

```python
{
    "name": "晨间推送",          # 任务名，--run 和 --list 用它
    "enabled": True,             # False 表示停用
    "cron": {"hour": 8, "minute": 0},   # 每天 8:00
    "msgtype": "markdown",       # "markdown" 或 "text"
    "system": "你是……（模型人设）",
    "prompt": "请生成……（让模型生成什么）",
}
```

`cron` 字段和 Linux crontab 一致，可用的键：`minute`、`hour`、`day`、`day_of_week`（`"mon"` ~ `"sun"`）、`month`，省略即 `*`。例如每周一 9 点：`{"day_of_week": "mon", "hour": 9, "minute": 0}`。

## 可靠性配置

`.env.example` 里提供了可选的可靠性参数：

- `AI_MAX_RETRIES`：AI 临时错误的最大重试次数
- `AI_RETRY_BASE_DELAY` / `AI_RETRY_MAX_DELAY`：指数退避范围
- `TIMEZONE=Asia/Shanghai`：固定使用北京时间
- `LOG_FILE` / `LOG_LEVEL`：结构化日志配置
- `ALERT_ON_FAILURE=true`：任务失败时给自己发送企业微信告警

调度器已配置任务防重入、错过任务合并和 5 分钟宽限期。默认消息接收人建议填写明确的企业微信成员 `userid`，不要依赖 `@all`。

## 让它一直跑

`main.py` 需要常驻运行，三种选择：

1. **Mac 本机**：`nohup python main.py > bot.log 2>&1 &`
   （电脑合盖/休眠时会停，只适合先体验）
2. **云函数**：腾讯云/阿里云函数 + 定时触发器，有免费额度，无需服务器，推荐
3. **便宜 VPS**：用 systemd 挂后台，最稳，且 IP 固定（不用维护可信 IP）

## 常见问题

| 现象 | 原因 / 解决 |
|---|---|
| 报错 `60020 not allow to access from your ip` | 没配「企业可信IP」，回第 2 步；家里宽带 IP 变了也要更新 |
| 发送成功但微信没收到 | 检查第 3 步「微信插件」是否已关注，或装企业微信 App |
| markdown 消息在微信里格式丢失 | 把该任务的 `msgtype` 改成 `"text"` |
| 内容太长发送失败 | markdown 上限 4096 字节、text 上限 2048 字节，在 prompt 里限制字数 |
| access_token 失效 | 代码已自动缓存并重试，一般无需处理 |

## 后续扩展

- **推送真实数据（天气/新闻）**：模型本身不知道实时信息，需先接数据源（天气 API、RSS 等），
  在 `main.py` 的 `run_job` 里先抓数据、拼进 prompt 再生成
- **推给多人**：把对方微信拉进你的企业微信通讯录，`.env` 里 `WECOM_TO_USER` 用 `|` 分隔多个 userid
- **面向公众的公众号版**：注册订阅号，做"用户发消息 → AI 回复"的触发式机器人
  （个人未认证号也能做），需要加一个 Web 服务接微信消息回调，届时可以在此项目上扩展
