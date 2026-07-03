"""
爬虫控制 API
作用：手动触发爬取任务
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.website import Website

router = APIRouter()


@router.post("/run/{website_id}")
def run_crawl_now(website_id: int, db: Session = Depends(get_db)):
    """
    手动触发对指定网站的爬取

    注意：当前为占位实现，待爬虫服务开发完成后接入
    """
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")

    # TODO: 接入爬虫服务
    return {
        "website": website.name,
        "pages_crawled": 0,
        "leaks_detected": 0,
        "message": "爬虫功能开发中，此为占位响应",
    }
