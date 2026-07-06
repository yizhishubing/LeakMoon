"""
规则引擎测试
作用：验证 RuleEngine 加载、重载规则的正确性
"""

from app.services.rule_engine import RuleEngine


class TestRuleEngine:
    def setup_method(self):
        self.engine = RuleEngine()

    def test_load_rules(self):
        """验证规则文件加载"""
        assert len(self.engine.rules) > 0
        assert len(self.engine.compiled_rules) > 0

    def test_reload_rules(self):
        """验证规则重载"""
        original_count = len(self.engine.rules)
        self.engine.reload()
        assert len(self.engine.rules) == original_count

    def test_get_all_rules(self):
        """验证获取所有规则"""
        rules = self.engine.get_all_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0

    def test_compiled_rules_match(self):
        """验证编译后的规则能匹配文本"""
        for compiled, rule in self.engine.compiled_rules:
            assert compiled.pattern == rule["pattern"]
