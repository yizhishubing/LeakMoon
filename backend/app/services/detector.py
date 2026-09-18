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

# 用于匹配 base64 编码数据块的正则（模块级预编译，避免重复创建）
_BASE64_PATTERN = re.compile(r'data:[^;]*;base64,[A-Za-z0-9+/=]{40,}')
_LONG_BASE64_SEQUENCE = re.compile(r'[A-Za-z0-9+/]{64,}={0,2}')
_IMG_SRC_BASE64 = re.compile(r'<img\b[^>]*\bsrc\s*=\s*["\']data:[^"\']*base64[^"\']*["\'][^>]*>', re.IGNORECASE)

# Unicode 代理对及替换字符正则：U+D800-U+DFFF（代理区）、U+FFFD（替换字符）
# 这些字符通常由二进制文件（如图片）被错误解析为文本时产生，需清理后存入数据库
_UNICODE_SANITIZE_PATTERN = re.compile(
    r'[\ud800-\udfff�]'
)


def _sanitize_text(text: str) -> str:
    """
    清理文本中的非法 Unicode 字符（代理对、替换字符等）

    场景：图片二进制数据被错误解析为文本时会产生 U+FFFD（�）或随机代理字符，
    这些字符写入数据库后在 JSON 序列化时会引发 Invalid \escape 错误。
    此处统一清洗，确保入库文本均为合法 Unicode。
    """
    if not text:
        return text
    return _UNICODE_SANITIZE_PATTERN.sub('', text)


class SensitiveInfoDetector:
    def __init__(self, db: Session):
        self.db = db
        self.rule_engine = RuleEngine()
        self.false_positive_filter = FalsePositiveFilter()

    async def detect(self, page_data: dict) -> list:
        """
        检测单个页面的敏感信息

        优化：
        - 预编译规则列表，避免每次循环访问 tuple
        - 减少中间变量分配
        - 去重：同一页面的相同匹配文本只保留一次
        """
        url = page_data["url"]
        text = page_data["text"]

        # 清理文本中的 base64 编码数据，防止图片编码被误判为敏感信息
        text = self._clean_base64_from_text(text)
        # 清理非法 Unicode 字符（如二进制数据被误解析产生的替换字符）
        text = _sanitize_text(text)

        if not text:
            return []

        # 检查是否为SPA页面（文本过短且内容主要是导航）
        if self._is_likely_spider_trap(text, url):
            return []

        records = []
        # 预提取规则列表，避免重复访问 self.rule_engine.compiled_rules
        rules = self.rule_engine.compiled_rules
        is_fp = self.false_positive_filter.is_false_positive
        mask_fn = self._mask_sensitive

        # 用于去重：同一URL的相同匹配文本只保留一次
        seen_matches = set()

        for compiled_regex, rule in rules:
            for match in compiled_regex.finditer(text):
                matched_text = match.group(0)

                # 去重：跳过已处理过的匹配
                dedup_key = (matched_text, rule["name"])
                if dedup_key in seen_matches:
                    continue
                seen_matches.add(dedup_key)

                # 误报过滤
                if is_fp(matched_text, rule):
                    continue

                # 脱敏处理
                masked_text = mask_fn(matched_text, rule)

                # 提取上下文
                start = match.start()
                end = match.end()
                context_before = text[max(0, start - 50):start]
                context_after = text[end:min(len(text), end + 50)]

                records.append(LeakRecord(
                    website_id=None,
                    detected_at=datetime.now(),
                    rule_name=_sanitize_text(rule["name"]),
                    severity=rule["severity"],
                    data_type=rule["data_type"],
                    matched_text=_sanitize_text(masked_text),
                    source_url=_sanitize_text(url),
                    context_before=_sanitize_text(context_before[:500]),
                    context_after=_sanitize_text(context_after[:500]),
                    is_verified=0,
                ))

        return records

    @staticmethod
    def _is_likely_spider_trap(text: str, url: str) -> bool:
        """
        检测页面是否为SPA或仅包含导航菜单的陷阱页面

        策略：
        1. 文本过短（<500字符）且包含大量导航关键词
        2. URL包含典型的SPA路由模式（如 /info/xxx/xxx.htm）
        3. 文本中只包含列表项而没有实际内容段落
        """
        # 如果文本太短，可能是SPA或未完全加载
        if len(text) < 500:
            # 检查是否包含大量导航/菜单关键词
            nav_keywords = ['学校概况', '学校新闻', '机构设置', '师资队伍',
                           '教务处', '科学研究', '招生简章', '通知公告']
            nav_count = sum(1 for kw in nav_keywords if kw in text)
            if nav_count >= 3:
                return True

        # 检查URL模式：某些路径可能是SPA动态路由
        spa_patterns = ['/info/', '/xxgk/', '/jwc/', '/kyc/']
        if any(pattern in url for pattern in spa_patterns):
            # 如果文本很短且没有实质性内容，可能是SPA
            if len(text) < 1000:
                # 检查是否有实质性段落（连续非空字符超过20个）
                import re
                paragraphs = re.findall(r'[^\n]{20,}', text)
                if len(paragraphs) < 3:
                    return True

        return False

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
        # 1. 移除 <img src="data:...base64,..."> 标签
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

        注意：此方法逐条 commit，性能不如批量 detect + 统一 commit。
        推荐在 crawlers.py 中使用 detect 批量处理。
        """
        records = await self.detect(page_data)
        for record in records:
            record.website_id = website_id
            self.db.add(record)
        self.db.commit()
        return records
