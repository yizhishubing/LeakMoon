"""
误报过滤器
作用：降低检测引擎的误报率，排除明显不是真实泄露的情况
"""

import re


class FalsePositiveFilter:
    # 已知假数据模式
    KNOWN_FAKE_PATTERNS = [
        r"^13800138000$",
        r"^13900139000$",
        r"^13700137000$",
        r"^11111111111$",
        r"^00000000000$",
        r"example\.com",
        r"^test@",
    ]

    def __init__(self):
        # 精确匹配：手机号、测试号（必须完全等于）
        self._exact_patterns = [
            r"^13800138000$", r"^13900139000$", r"^13700137000$",
            r"^11111111111$", r"^00000000000$",
        ]
        # 子串匹配：示例域名、测试邮箱前缀
        self._substring_patterns = [r"example\.com", r"^test@"]
        self._exact_regexes = [re.compile(p) for p in self._exact_patterns]
        self._substring_regexes = [re.compile(p) for p in self._substring_patterns]

    def is_false_positive(self, matched_text: str, rule: dict) -> bool:
        """判断是否为误报，True=误报（应忽略）"""
        # 策略1：精确匹配已知假数据
        for regex in self._exact_regexes:
            if regex.search(matched_text):
                return True

        # 策略2：子串匹配示例/测试标识
        for regex in self._substring_regexes:
            if regex.search(matched_text):
                return True

        # 策略3：同一数字出现超过70%（大概率不是真实数据）
        if len(set(matched_text)) <= 2 and len(matched_text) >= 5:
            return True

        # 策略4：身份证号最后一位不能全是X
        if rule.get("data_type") == "id_card":
            if matched_text[-1] == "X" and matched_text.count("X") > 1:
                return True

        return False
