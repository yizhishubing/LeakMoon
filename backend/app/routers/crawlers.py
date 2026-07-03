"""
爬虫控制 API
作用：手动触发爬取任务
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.crawler import SiteCrawler
from app.services.detector import SensitiveInfoDetector
from app.models.website import Website

router = APIRouter()


@router.post("/run/{website_id}")
async def run_crawl_now(website_id: int, db: Session = Depends(get_db)):
    """手动触发对指定网站的爬取"""
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
    total_leaks = 0
    for page in pages:
        total_leaks += detector.detect_and_save(page, website.id)

    return {
        "website": website.name,
        "pages_crawled": len(pages),
        "leaks_detected": total_leaks,
    }
