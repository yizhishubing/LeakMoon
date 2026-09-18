"""
爬虫控制 API
作用：手动触发爬取任务并发送告警
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.crawler import SiteCrawler
from app.services.detector import SensitiveInfoDetector
from app.services.alert_service import AlertService
from app.models.website import Website
from app.models.alert import AlertLog, AlertStatus
from app.config import get_settings

router = APIRouter()


@router.post("/run/{website_id}")
async def run_crawl_now(website_id: int, db: Session = Depends(get_db)):
    """
    手动触发对指定网站的爬取，检测并发送告警

    优化：
    1. 爬虫共享连接池，批量并发请求
    2. 检测完成后统一 commit，减少数据库 IO
    3. 告警异步发送，不阻塞主流程
    """
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")

    crawler = SiteCrawler(delay=0.3, max_concurrent=5)
    pages = await crawler.crawl(
        start_url=website.url,
        max_depth=website.depth,
        max_pages=website.max_pages
    )

    detector = SensitiveInfoDetector(db)
    alert_svc = AlertService(db)
    total_leaks = 0
    all_records = []

    # 第一阶段：检测所有页面（暂不 commit）
    for page in pages:
        # 移除临时字段
        page.pop("_depth", None)
        records = await detector.detect(page)
        for record in records:
            record.website_id = website_id
            all_records.append(record)
        total_leaks += len(records)

    # 第二阶段：去重并批量插入
    if all_records:
        # 去重：同一 website_id + source_url + matched_text + data_type 只保留一条
        seen = set()
        unique_records = []
        for record in all_records:
            key = (record.website_id, record.source_url, record.matched_text, record.data_type)
            if key not in seen:
                seen.add(key)
                unique_records.append(record)

        db.add_all(unique_records)
        db.commit()
        total_leaks = len(unique_records)

    # 第三阶段：异步发送高严重级别告警
    high_severity_leaks = [r for r in all_records if r.severity == "high" and r.is_verified == 0]
    if high_severity_leaks:
        # 后台任务：发送告警邮件，不阻塞返回
        import asyncio
        async def _send_alerts_async():
            for leak in high_severity_leaks:
                await alert_svc.send_alert(leak)
        asyncio.create_task(_send_alerts_async())

    return {
        "website": website.name,
        "pages_crawled": len(pages),
        "leaks_detected": total_leaks,
    }
