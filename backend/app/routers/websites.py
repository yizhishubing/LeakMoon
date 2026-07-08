from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.website import Website
from app.models.leak import LeakRecord
from app.models.alert import AlertLog
from app.schemas.website import WebsiteCreate, WebsiteUpdate, WebsiteResponse

router = APIRouter()


@router.get("/", response_model=list[WebsiteResponse])
def list_websites(db: Session = Depends(get_db)):
    """获取所有网站列表"""
    return db.query(Website).all()


@router.post("/", response_model=WebsiteResponse)
def create_website(data: WebsiteCreate, db: Session = Depends(get_db)):
    """新增一个巡检网站"""
    if db.query(Website).filter(Website.url == data.url).first():
        raise HTTPException(status_code=400, detail="该URL已存在")

    website = Website(
        name=data.name,
        url=data.url,
        depth=data.depth,
        max_pages=data.max_pages,
        crawl_interval=data.crawl_interval,
    )
    db.add(website)
    db.commit()
    db.refresh(website)
    return website


@router.put("/{website_id}", response_model=WebsiteResponse)
def update_website(website_id: int, data: WebsiteUpdate, db: Session = Depends(get_db)):
    """更新网站配置"""
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(website, key, value)

    db.commit()
    db.refresh(website)
    return website


@router.delete("/{website_id}")
def delete_website(website_id: int, db: Session = Depends(get_db)):
    """
    删除网站及其关联的泄露记录和告警记录

    级联删除顺序：
    1. AlertLog（依赖 LeakRecord.id）
    2. LeakRecord（依赖 Website.id）
    3. Website
    """
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")

    # 先删除告警记录（最外层依赖）
    db.query(AlertLog).filter(
        AlertLog.leak_record_id.in_(
            db.query(LeakRecord.id).filter(LeakRecord.website_id == website_id)
        )
    ).delete(synchronize_session=False)

    # 再删除泄露记录
    db.query(LeakRecord).filter(LeakRecord.website_id == website_id).delete(
        synchronize_session=False
    )

    # 最后删除网站
    db.delete(website)
    db.commit()
    return {"message": "删除成功"}
