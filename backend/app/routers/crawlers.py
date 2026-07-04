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

router = APIRouter()


@router.post("/run/{website_id}")
async def run_crawl_now(website_id: int, db: Session = Depends(get_db)):
    """手动触发对指定网站的爬取，检测并发送告警"""
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")

    crawler = SiteCrawler(delay=0.5)
    pages = await crawler.crawl(
        start_url=website.url,
        max_depth=website.depth,
        max_pages=website.max_pages
    )

    detector = SensitiveInfoDetector(db)
    alert_svc = AlertService(db)
    total_leaks = 0

    for page in pages:
        records = await detector.detect_and_save(page, website.id)
        total_leaks += len(records)

        # 对未确认的高风险泄露触发告警
        for leak in records:
            if leak.severity == "high" and leak.is_verified == 0:
                await alert_svc.send_alert(leak)

    return {
        "website": website.name,
        "pages_crawled": len(pages),
        "leaks_detected": total_leaks,
    }
