"""
FastAPI 主入口
作用：
1. 创建 FastAPI 应用实例
2. 配置 CORS 中间件
3. 注册所有 API 路由
4. 提供健康检查端点
5. 自动寻找空闲端口启动（即开即用）
6. 集成 APScheduler 定时爬取
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import websites, crawlers, alerts, rules, reports
from app.services.crawler import SiteCrawler
from app.services.detector import SensitiveInfoDetector
from app.services.alert_service import AlertService
from app.database import SessionLocal
from app.models.website import Website
import uvicorn
import asyncio
import socket

app = FastAPI(title="校园网站敏感信息泄露巡检平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websites.router, prefix="/api/websites", tags=["网站管理"])
app.include_router(crawlers.router, prefix="/api/crawlers", tags=["爬虫控制"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["告警管理"])
app.include_router(rules.router, prefix="/api/rules", tags=["规则管理"])
app.include_router(reports.router, prefix="/api/reports", tags=["报表管理"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "leakmoon-backend"}


def find_free_port(start_port: int = 8000, end_port: int = 9000) -> int:
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port in range ({start_port}-{end_port})")


async def run_crawl_job():
    """定时爬取任务：每天凌晨2点执行"""
    db = SessionLocal()
    try:
        websites = db.query(Website).filter(
            Website.is_active == True,
            Website.status == "active",
        ).all()

        for website in websites:
            crawler = SiteCrawler(delay=1.0)
            pages = await crawler.crawl(
                start_url=website.url,
                max_depth=website.depth,
                max_pages=website.max_pages,
            )

            detector = SensitiveInfoDetector(db)
            for page in pages:
                await detector.detect_and_save(page, website.id)

            print(f"[Scheduler] Crawled {len(pages)} pages from {website.name}")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Scheduler] Error: {e}")
    finally:
        db.close()


def run_server():
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_crawl_job, "cron", hour=2, minute=0)
    scheduler.start()

    port = find_free_port()
    print(f"[LeakMoon] 后端服务启动在端口 {port}")
    print(f"[LeakMoon] API 文档: http://localhost:{port}/docs")
    print(f"[LeakMoon] 健康检查: http://localhost:{port}/api/health")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    run_server()
