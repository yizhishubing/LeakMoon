"""
可配置规则引擎
作用：
1. 从 YAML 文件加载检测规则
2. 编译正则表达式为高效匹配对象
3. 支持动态添加/删除/启用规则
"""

import yaml
import re
from pathlib import Path
from typing import Optional


class RuleEngine:
    RULES_FILE = Path(__file__).parent.parent / "core" / "rules.yaml"

    def __init__(self):
        self.rules: list[dict] = []
        self.compiled_rules: list[tuple] = []
        self.load_rules()

    def load_rules(self):
        """从 YAML 文件加载规则"""
        with open(self.RULES_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.rules = data.get("rules", [])
        self._compile_rules()

    def _compile_rules(self):
        """将所有启用的规则预编译为正则表达式"""
        self.compiled_rules = []
        for rule in self.rules:
            if rule.get("is_active", True):
                compiled = re.compile(rule["pattern"])
                self.compiled_rules.append((compiled, rule))

    def reload(self):
        """重新加载规则文件（管理员修改 YAML 后调用）"""
        self.load_rules()

    def add_rule(self, rule_dict: dict):
        """动态添加一条新规则"""
        self.rules.append(rule_dict)
        if rule_dict.get("is_active", True):
            compiled = re.compile(rule_dict["pattern"])
            self.compiled_rules.append((compiled, rule_dict))

    def remove_rule(self, rule_id: int):
        """按索引移除规则"""
        if 0 <= rule_id < len(self.rules):
            self.rules.pop(rule_id)
            self._compile_rules()

    def activate_rule(self, rule_id: int):
        """激活规则"""
        if 0 <= rule_id < len(self.rules):
            self.rules[rule_id]["is_active"] = True
            self._compile_rules()

    def deactivate_rule(self, rule_id: int):
        """停用规则"""
        if 0 <= rule_id < len(self.rules):
            self.rules[rule_id]["is_active"] = False
            self._compile_rules()

    def get_all_rules(self) -> list:
        """返回所有规则（含元数据）"""
        return self.rules
