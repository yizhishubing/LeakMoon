"""
检测引擎测试
作用：验证 SensitiveInfoDetector 能否正确检测敏感信息并脱敏
"""

import asyncio
from app.services.detector import SensitiveInfoDetector
from app.database import SessionLocal


class TestSensitiveInfoDetector:
    def setup_method(self):
        self.db = SessionLocal()
        self.detector = SensitiveInfoDetector(self.db)

    def teardown_method(self):
        self.db.close()

    def test_detect_id_card(self):
        """检测身份证号"""
        records = asyncio.run(self.detector.detect({
            "url": "http://test.com",
            "text": "身份证号: 110101199001011234",
            "title": "",
            "links": [],
        }))
        id_cards = [r for r in records if r.data_type == "id_card"]
        assert len(id_cards) == 1
        assert id_cards[0].matched_text == "110***1234"

    def test_detect_phone(self):
        """检测手机号"""
        records = asyncio.run(self.detector.detect({
            "url": "http://test.com",
            "text": "电话: 13812345678",
            "title": "",
            "links": [],
        }))
        phones = [r for r in records if r.data_type == "phone"]
        assert len(phones) == 1
        assert phones[0].matched_text == "138****5678"

    def test_detect_email(self):
        """检测邮箱"""
        records = asyncio.run(self.detector.detect({
            "url": "http://test.com",
            "text": "邮箱: admin@school.edu.cn",
            "title": "",
            "links": [],
        }))
        emails = [r for r in records if r.data_type == "email"]
        assert len(emails) == 1
        assert emails[0].matched_text == "a***@school.edu.cn"

    def test_no_match_safe_text(self):
        """安全文本不应产生检测记录"""
        records = asyncio.run(self.detector.detect({
            "url": "http://test.com",
            "text": "这是一个安全的页面，没有任何敏感信息。",
            "title": "",
            "links": [],
        }))
        assert len(records) == 0

    def test_mask_sensitive_id_card(self):
        """身份证号脱敏"""
        result = self.detector._mask_sensitive("110101199001011234", {"data_type": "id_card"})
        assert result == "110***1234"

    def test_mask_sensitive_phone(self):
        """手机号脱敏"""
        result = self.detector._mask_sensitive("13812345678", {"data_type": "phone"})
        assert result == "138****5678"

    def test_mask_sensitive_email(self):
        """邮箱脱敏"""
        result = self.detector._mask_sensitive("zhangsan@example.com", {"data_type": "email"})
        assert result == "z***@example.com"
