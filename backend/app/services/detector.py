"""
敏感信息检测引擎
作用：
1. 对爬取到的页面文本运行所有检测规则
2. 过滤误报（如示例/测试数据）
3. 将真实泄露记录入库
4. 返回检测结果的摘要统计
做法：
1. 清理文本中的 base64 编码和图片相关数据，防止误判
2. 加载 RuleEngine 中的所有已编译正则
3. 对每段文本逐一匹配
4. 对匹配结果调用 FalsePositiveFilter 进行二次过滤
5. 将确认的泄露创建 LeakRecord 对象存入数据库
"""

import re
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.leak import LeakRecord
from app.services.rule_engine import RuleEngine
from app.core.filters import FalsePositiveFilter

# 用于匹配 base64 编码数据块的正则
# 匹配形如 "data:image/png;base64,xxxxx" 或长串 base64 内容（≥80字符）
_BASE64_PATTERN = re.compile(
    r'data:[^;]*;base64,[A-Za-z0-9+/=]{40,}'
)
# 匹配超长连续 base64 字符序列（≥64字符，且包含至少一个非字母数字的特殊base64字符）
_LONG_BASE64_SEQUENCE = re.compile(
    r'[A-Za-z0-9+/]{64,}={0,2}'
)
# 匹配 img src 属性中的 base64 数据（如 src="data:image/...")
_IMG_SRC_BASE64 = re.compile(
    r'<img\b[^>]*\bsrc\s*=\s*["\']data:[^"\']*base64[^"\']*["\'][^>]*>',
    re.IGNORECASE
)


class SensitiveInfoDetector:
    def __init__(self, db: Session):
        self.db = db
        self.rule_engine = RuleEngine()
        self.false_positive_filter = FalsePositiveFilter()

    async def detect(self, page_data: dict) -> list:
        """
        检测单个页面的敏感信息

        参数：
            page_data: {'url', 'title', 'text', 'links'}

        返回：
            list[LeakRecord]: 检测到的泄露记录
        """
        url = page_data["url"]
        text = page_data["text"]

        # 清理文本中的 base64 编码数据，防止图片编码被误判为敏感信息
        text = self._clean_base64_from_text(text)

        records = []

        for compiled_regex, rule in self.rule_engine.compiled_rules:
            for match in compiled_regex.finditer(text):
                matched_text = match.group(0)

                # 误报过滤
                if self.false_positive_filter.is_false_positive(matched_text, rule):
                    continue

                # 脱敏处理
                masked_text = self._mask_sensitive(matched_text, rule)

                # 提取上下文
                start = match.start()
                end = match.end()
                context_before = text[max(0, start - 50):start]
                context_after = text[end:min(len(text), end + 50)]

                records.append(LeakRecord(
                    website_id=None,
                    detected_at=datetime.now(),
                    rule_name=rule["name"],
                    severity=rule["severity"],
                    data_type=rule["data_type"],
                    matched_text=masked_text,
                    source_url=url,
                    context_before=context_before[:500],
                    context_after=context_after[:500],
                    is_verified=0,
                ))

        return records

    @staticmethod
    def _clean_base64_from_text(text: str) -> str:
        """
        清理文本中的 base64 编码数据，防止图片/文件编码被误判为敏感信息

        策略：
        1. 移除 HTML 中的 <img src="data:image/...;base64,..."> 标签
        2. 移除 data URI 格式的 base64 数据（如 "data:image/png;base64,xxxxx"）
        3. 替换超长连续 base64 字符序列为空白（≥64字符的 base64 串几乎不可能是正常文本）

        注意：短 base64 字符串（如 <64字符）可能出现在正常文本中，予以保留
        """
        # 1. 移除 <img src="data:...base64,..."> 标签（从原始HTML残留中提取的文本中可能出现）
        text = _IMG_SRC_BASE64.sub('', text)

        # 2. 移除 data URI 格式的 base64 数据
        text = _BASE64_PATTERN.sub(' ', text)

        # 3. 替换超长连续 base64 字符序列
        text = _LONG_BASE64_SEQUENCE.sub(' ', text)

        # 4. 压缩多余空白
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {3,}', ' ', text)

        return text

    def _mask_sensitive(self, text: str, rule: dict) -> str:
        """
        对敏感信息进行脱敏显示

        做法：根据规则类型采用不同掩码策略
        - 身份证号：保留前3位和后4位
        - 手机号：保留前3位和后4位
        - 邮箱：保留用户名首字母和@后的域名
        - 其他：保留首尾各2字符
        """
        data_type = rule["data_type"]

        if data_type == "id_card" and len(text) >= 7:
            return text[:3] + "***" + text[-4:]
        elif data_type == "phone" and len(text) == 11:
            return text[:3] + "****" + text[-4:]
        elif data_type == "email" and "@" in text:
            parts = text.split("@")
            return parts[0][0] + "***@" + parts[1]
        elif len(text) >= 4:
            return text[:2] + "*" * (len(text) - 4) + text[-2:]
        return "***"

    async def detect_and_save(self, page_data: dict, website_id: int) -> list:
        """
        检测并保存结果的便捷方法（异步版本）

        返回：
            list[LeakRecord]: 检测到的泄露记录列表
        """
        records = await self.detect(page_data)
        for record in records:
            record.website_id = website_id
            self.db.add(record)
        self.db.commit()
        return records
