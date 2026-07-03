# LeakMoon — 校园网站敏感信息泄露巡检与告警平台

基于 Python + Vue 的校园网站敏感信息泄露自动化巡检与告警系统。

## 快速启动

**Windows：** 双击 `start.bat`  
**Linux / WSL：** `bash start.sh`

自动检测并启动 MySQL、Redis、后端（FastAPI）、前端（Vue 3）。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Element Plus + ECharts |
| 后端 | Python FastAPI + SQLAlchemy |
| 数据库 | MySQL 8.0 |
| 缓存 | Redis |
| 爬虫 | httpx + BeautifulSoup4 |
| 调度 | APScheduler |

## 项目结构

```
LeakMoon/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── main.py           # 入口（自动找端口）
│   │   ├── config.py         # 配置管理
│   │   ├── database.py       # 数据库连接
│   │   ├── models/           # 数据模型
│   │   ├── routers/          # API 路由
│   │   ├── services/         # 业务逻辑
│   │   └── core/             # 规则引擎、误报过滤
│   └── tests/
├── frontend/         # Vue 3 前端
│   └── src/
│       ├── views/            # 页面组件
│       ├── router/           # 路由
│       └── api/              # API 封装
├── start.bat           # Windows 一键启动
└── start.sh            # Linux/WSL 一键启动
```

## 功能模块

- **风险仪表盘** — 统计概览、趋势图表、风险分布
- **巡检管理** — 网站增删改查、手动/定时爬取
- **泄露记录** — 敏感信息检测、确认/误报标记
- **告警中心** — 邮件 + 站内消息、状态追踪
- **规则管理** — 可配置检测规则（YAML）、动态重载
- **报表中心** — 巡检报告生成

## 本地开发

```bash
# 后端
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## License

MIT
