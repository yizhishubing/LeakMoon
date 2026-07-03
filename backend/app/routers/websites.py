from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.website import Website
from app.schemas.website import WebsiteCreate, WebsiteUpdate, WebsiteResponse

router = APIRouter()


@router.get("/", response_model=list[WebsiteResponse])
def list_websites(db: Session = Depends(get_db)):
    """获取所有网站列表"""
    return db.query(Website).all()


@router.post("/", response_model=WebsiteResponse)
def create_website(data: WebsiteCreate, db: Session = Depends(get_db)):
    """新增一个巡检网站"""
    if db.query(Website).filter(Website.url == str(data.url)).first():
        raise HTTPException(status_code=400, detail="该URL已存在")

    website = Website(
        name=data.name,
        url=str(data.url),
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
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])

    for key, value in update_data.items():
        setattr(website, key, value)

    db.commit()
    db.refresh(website)
    return website


@router.delete("/{website_id}")
def delete_website(website_id: int, db: Session = Depends(get_db)):
    """删除网站"""
    website = db.query(Website).filter(Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")

    db.delete(website)
    db.commit()
    return {"message": "删除成功"}
