"""
敏感信息检测引擎
作用：
1. 对爬取到的页面文本运行所有检测规则
2. 过滤误报（如示例/测试数据）
3. 将真实泄露记录入库
4. 返回检测结果的摘要统计
做法：
1. 加载 RuleEngine 中的所有已编译正则
2. 对每段文本逐一匹配
3. 对匹配结果调用 FalsePositiveFilter 进行二次过滤
4. 将确认的泄露创建 LeakRecord 对象存入数据库
"""

import re
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.leak import LeakRecord
from app.services.rule_engine import RuleEngine
from app.core.filters import FalsePositiveFilter


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

    def detect_and_save(self, page_data: dict, website_id: int) -> int:
        """
        检测并保存结果的便捷方法

        返回：
            int: 检测到的泄露数量
        """
        records = self.detect(page_data)
        for record in records:
            record.website_id = website_id
            self.db.add(record)
        self.db.commit()
        return len(records)
