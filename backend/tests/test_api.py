"""
API 测试
作用：验证网站 CRUD 接口功能正常
"""

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.leak import LeakRecord
from app.models.alert import AlertLog
from app.models.website import Website

client = TestClient(app)
db = SessionLocal()


class TestWebsiteAPI:
    """网站管理 API 测试"""

    def _cleanup(self):
        """按 FK 依赖顺序清理测试数据"""
        test_urls = db.query(Website.url).filter(Website.url.like("%test-%")).all()
        test_url_list = [u[0] for u in test_urls]
        if test_url_list:
            db.query(AlertLog).filter(
                AlertLog.leak_record_id.in_(
                    db.query(LeakRecord.id).filter(LeakRecord.source_url.like("%test-%"))
                )
            ).delete(synchronize_session=False)
            db.query(LeakRecord).filter(LeakRecord.source_url.like("%test-%")).delete(synchronize_session=False)
            db.query(Website).filter(Website.url.in_(test_url_list)).delete(synchronize_session=False)
            db.commit()

    def setup_method(self):
        self._cleanup()

    def teardown_method(self):
        self._cleanup()

    def test_list_websites(self):
        """获取网站列表"""
        r = client.get("/api/websites/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_website(self):
        """创建网站"""
        data = {
            "name": "测试网站",
            "url": "http://test-crud.local",
            "depth": 1,
            "maxPages": 5,
            "crawl_interval": 12,
        }
        r = client.post("/api/websites/", json=data)
        assert r.status_code == 200
        assert r.json()["name"] == "测试网站"

    def test_create_duplicate_url(self):
        """重复 URL 应返回 400"""
        # 先创建一个网站
        data1 = {"name": "测试1", "url": "http://test-dup.local", "depth": 1, "maxPages": 5, "crawl_interval": 12}
        client.post("/api/websites/", json=data1)
        # 再用相同 URL 创建
        data2 = {"name": "测试2", "url": "http://test-dup.local", "depth": 1, "maxPages": 5, "crawl_interval": 12}
        r = client.post("/api/websites/", json=data2)
        assert r.status_code == 400

    def test_update_website(self):
        """更新网站"""
        data = {"name": "测试", "url": "http://test-update.local", "depth": 1, "maxPages": 5, "crawl_interval": 12}
        r = client.post("/api/websites/", json=data)
        site_id = r.json()["id"]
        r = client.put(f"/api/websites/{site_id}", json={"name": "已更新"})
        assert r.status_code == 200
        assert r.json()["name"] == "已更新"

    def test_delete_website(self):
        """删除网站"""
        data = {"name": "测试", "url": "http://test-del.local", "depth": 1, "maxPages": 5, "crawl_interval": 12}
        r = client.post("/api/websites/", json=data)
        site_id = r.json()["id"]
        r = client.delete(f"/api/websites/{site_id}")
        assert r.status_code == 200

    def test_delete_nonexistent(self):
        """删除不存在的网站应返回 404"""
        r = client.delete("/api/websites/99999")
        assert r.status_code == 404

    def test_health_check(self):
        """健康检查"""
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_rules_api(self):
        """规则管理 API"""
        r = client.get("/api/rules/")
        assert r.status_code == 200
        assert len(r.json()) > 0
        r = client.post("/api/rules/reload")
        assert r.status_code == 200

    def test_crawlers_api(self):
        """爬虫控制 API"""
        data = {"name": "测试", "url": "http://test-crawl.local", "depth": 0, "maxPages": 1, "crawl_interval": 24}
        r = client.post("/api/websites/", json=data)
        site_id = r.json()["id"]
        r = client.post(f"/api/crawlers/run/{site_id}")
        assert r.status_code == 200
        assert "pages_crawled" in r.json()
        assert "leaks_detected" in r.json()

    def test_alerts_api(self):
        """告警管理 API"""
        r = client.get("/api/alerts/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
