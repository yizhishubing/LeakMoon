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
        r"test@",
    ]

    def __init__(self):
        self._fake_regexes = [re.compile(p) for p in self.KNOWN_FAKE_PATTERNS]

    def is_false_positive(self, matched_text: str, rule: dict) -> bool:
        """判断是否为误报，True=误报（应忽略）"""
        # 策略1：匹配已知假数据模式
        for regex in self._fake_regexes:
            if regex.search(matched_text):
                return True

        # 策略2：同一数字出现超过70%（大概率不是真实数据）
        if len(set(matched_text)) <= 2 and len(matched_text) >= 5:
            return True

        # 策略3：身份证号最后一位不能全是X
        if rule.get("data_type") == "id_card":
            if matched_text[-1] == "X" and matched_text.count("X") > 1:
                return True

        return False
