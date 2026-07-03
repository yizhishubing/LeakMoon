"""
FastAPI 主入口
作用：
1. 创建 FastAPI 应用实例
2. 配置 CORS 中间件（允许前端跨域访问）
3. 注册所有 API 路由
4. 提供健康检查端点
5. 自动寻找空闲端口启动（即开即用）
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import websites, crawlers, alerts, rules, reports
import uvicorn
import socket

app = FastAPI(
    title="校园网站敏感信息泄露巡检平台",
    description="基于Python+Vue的自动化巡检与告警系统",
    version="1.0.0",
)

# 配置 CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(websites.router, prefix="/api/websites", tags=["网站管理"])
app.include_router(crawlers.router, prefix="/api/crawlers", tags=["爬虫控制"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["告警管理"])
app.include_router(rules.router, prefix="/api/rules", tags=["规则管理"])
app.include_router(reports.router, prefix="/api/reports", tags=["报表管理"])


@app.get("/api/health")
def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "leakmoon-backend"}


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "欢迎使用校园网站敏感信息泄露巡检平台",
        "docs": "/docs",
        "health": "/api/health",
    }


def find_free_port(start_port: int = 8000, end_port: int = 9000) -> int:
    """
    自动寻找一个未被占用的端口

    做法：从 start_port 开始逐个试探，找到第一个空闲端口就返回
    保证即开即用，不会因为端口被占用而启动失败
    """
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    # 全部占用时抛出异常，提示用户
    raise RuntimeError(f"未找到空闲端口（{start_port}-{end_port}）")


def run_server():
    """启动服务的统一入口"""
    port = find_free_port()
    print(f"[LeakMoon] 后端服务启动在端口 {port}")
    print(f"[LeakMoon] API 文档: http://localhost:{port}/docs")
    print(f"[LeakMoon] 健康检查: http://localhost:{port}/api/health")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    run_server()
