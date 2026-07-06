"""
误报过滤器测试
作用：验证 FalsePositiveFilter 能否正确识别和过滤误报数据
"""

from app.core.filters import FalsePositiveFilter


class TestFalsePositiveFilter:
    def setup_method(self):
        self.fp = FalsePositiveFilter()

    def test_known_fake_phone_numbers(self):
        """测试号应被过滤"""
        assert self.fp.is_false_positive("13800138000", {}) is True
        assert self.fp.is_false_positive("13900139000", {}) is True
        assert self.fp.is_false_positive("13700137000", {}) is True

    def test_repetitive_digits(self):
        """全重复数字应被过滤"""
        assert self.fp.is_false_positive("11111111111", {}) is True
        assert self.fp.is_false_positive("00000000000", {}) is True

    def test_test_email_prefix(self):
        """测试邮箱前缀应被过滤"""
        assert self.fp.is_false_positive("test@test.com", {}) is True

    def test_real_phone_not_filtered(self):
        """真实手机号不应被过滤"""
        assert self.fp.is_false_positive("13812345678", {}) is False

    def test_real_id_card_not_filtered(self):
        """真实身份证号不应被过滤"""
        assert self.fp.is_false_positive("110101199001011234", {}) is False

    def test_real_email_not_filtered(self):
        """真实邮箱不应被过滤"""
        assert self.fp.is_false_positive("admin@school.edu.cn", {}) is False

    def test_repetitive_digits_short(self):
        """短重复数字（<5位）不应被过滤"""
        assert self.fp.is_false_positive("111", {}) is False
