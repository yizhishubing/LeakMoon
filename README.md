# LeakMoon — 校园网站敏感信息泄露巡检与告警平台

基于 Python + Vue 3 的校园网站敏感信息泄露自动化巡检与告警系统。通过爬虫采集网页内容，利用可配置的正则规则引擎检测身份证、手机号、邮箱等敏感信息，发现后自动发送邮件告警并提供 Web 管理界面。

## 环境要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Python | ≥ 3.10 | 后端运行环境 |
| Node.js | ≥ 18 | 前端构建工具 |
| MySQL | ≥ 8.0 | 关系型数据库 |
| Redis | ≥ 7.0 | 缓存（可选） |

## 快速启动

### 一键启动

**Windows：** 双击 `start.bat`
**Linux / WSL：** `bash start.sh`

脚本会自动：
1. 检查 MySQL / Redis 是否运行，未运行则尝试启动
2. 启动后端（自动寻找空闲端口，默认 8000）
3. 启动前端开发服务器（5173）

### 手动启动

```bash
# 后端
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## 配置说明

### 后端配置 (`backend/.env`)

```ini
# 数据库
DATABASE_URL=mysql+pymysql://root:root123456@localhost:3306/leakmoon

# Redis
REDIS_URL=redis://localhost:6379/0

# 告警邮件（QQ 邮箱示例）
ALERT_EMAIL_HOST=smtp.qq.com
ALERT_EMAIL_PORT=465
ALERT_EMAIL_USER=your@qq.com
ALERT_EMAIL_PASSWORD=your-smtp-auth-code    # QQ 邮箱授权码
ALERT_EMAIL_FROM=your@qq.com
ALERT_EMAIL_TO=admin@your.com
```

> QQ 邮箱 SMTP 授权码获取：登录 QQ 邮箱 → 设置 → 账户 → 开启 SMTP → 生成授权码

### 前端配置 (`frontend/.env.development`)

```ini
VITE_API_BASE_URL=http://localhost:8000/api
```

Vite 已配置 `/api` 代理到后端，通常无需修改。

## 项目结构

```
LeakMoon/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口（自动找端口 + 定时调度）
│   │   ├── config.py            # 配置管理（pydantic-settings）
│   │   ├── database.py          # 数据库连接
│   │   ├── core/
│   │   │   ├── rules.yaml       # 检测规则（YAML 可热重载）
│   │   │   └── filters.py       # 误报过滤器
│   │   ├── models/              # SQLAlchemy 数据模型（5 张表）
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── routers/             # API 路由（5 个模块）
│   │   └── services/            # 业务逻辑（爬虫/检测/告警/规则）
│   ├── tests/
│   ├── .env                     # 环境变量
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/               # 页面（仪表盘/巡检/泄露/告警/规则/报表）
│   │   ├── router/              # 路由配置
│   │   └── App.vue              # 侧边栏布局
│   └── vite.config.js
├── start.bat                    # Windows 一键启动
└── start.sh                     # Linux/WSL 一键启动
```

## API 端点

| 模块 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 健康检查 | `/api/health` | GET | 服务状态 |
| 网站管理 | `/api/websites/` | GET | 获取网站列表 |
| | | POST | 新增网站 |
| | `/api/websites/{id}` | PUT | 更新网站 |
| | | DELETE | 删除网站 |
| 爬虫控制 | `/api/crawlers/run/{id}` | POST | 手动触发爬取+检测 |
| 告警管理 | `/api/alerts/` | GET | 获取告警列表 |
| | `/api/alerts/{id}/ack` | PUT | 确认告警 |
| | `/api/alerts/{id}/resolve` | PUT | 处理告警 |
| 规则管理 | `/api/rules/` | GET | 获取检测规则 |
| | `/api/rules/reload` | POST | 重载 YAML 规则 |
| 报表管理 | `/api/reports/` | GET | 报表列表（占位） |

API 文档（Swagger）：http://localhost:8000/docs

## 检测规则

规则定义在 `backend/app/core/rules.yaml`，支持热重载（无需重启）：

| 级别 | 类型 | 示例 |
|------|------|------|
| high | 身份证号 | 110101199001011234 |
| high | 手机号 | 13812345678 |
| high | 银行卡号 | 6222021234567890 |
| high | 密码泄露 | password=xxx |
| medium | 邮箱 | admin@school.edu.cn |
| medium | 学号 | 1234567890 |
| medium | 教职工号 | 教工-0012345 |
| low | 座机电话 | 010-12345678 |
| low | 内网 IP | 192.168.1.1 |

## 工作流程

```
定时任务（每日 2:00）
  → 查询启用的网站
  → 递归爬取页面（同域限制、深度控制）
  → 正则匹配敏感信息
  → 误报过滤（测试号/示例数据）
  → 脱敏入库
  → 高风险记录触发邮件告警
```

## 测试

```bash
cd backend
source venv/Scripts/activate
pytest tests/ -v
```

## License

MIT
