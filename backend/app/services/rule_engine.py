"""
可配置规则引擎
作用：
1. 从数据库加载检测规则
2. 编译正则表达式为高效匹配对象
3. 支持动态添加/删除/启用规则
"""

import re
from app.models.rule import DetectionRule
from app.database import SessionLocal


class RuleEngine:
    def __init__(self):
        self.rules = []
        self.compiled_rules = []
        self.load_rules()

    def load_rules(self):
        """从数据库加载规则"""
        db = SessionLocal()
        try:
            self.rules = [
                {
                    'name': r.name,
                    'pattern': r.pattern,
                    'data_type': r.data_type,
                    'severity': r.severity,
                    'description': r.description,
                    'is_active': r.is_active,
                }
                for r in db.query(DetectionRule).all()
            ]
            self._compile_rules()
        finally:
            db.close()

    def _compile_rules(self):
        """将所有启用的规则预编译为正则表达式"""
        self.compiled_rules = []
        for rule in self.rules:
            if rule.get("is_active", True):
                try:
                    compiled = re.compile(rule["pattern"])
                    self.compiled_rules.append((compiled, rule))
                except re.error as e:
                    print(f"[RuleEngine] Failed to compile rule '{rule['name']}': {e}")

    def reload(self):
        """重新加载规则（从数据库）"""
        self.load_rules()

    def add_rule(self, name: str, pattern: str, data_type: str, severity: str, description: str = "", is_active: bool = True) -> bool:
        """动态添加一条新规则"""
        db = SessionLocal()
        try:
            existing = db.query(DetectionRule).filter(DetectionRule.name == name).first()
            if existing:
                return False
            rule = DetectionRule(
                name=name,
                pattern=pattern,
                data_type=data_type,
                severity=severity,
                description=description,
                is_active=is_active,
            )
            db.add(rule)
            db.commit()
            self.load_rules()
            return True
        finally:
            db.close()

    def remove_rule(self, rule_id: int) -> bool:
        """按ID移除规则"""
        db = SessionLocal()
        try:
            rule = db.query(DetectionRule).filter(DetectionRule.id == rule_id).first()
            if rule:
                db.delete(rule)
                db.commit()
                self.load_rules()
                return True
            return False
        finally:
            db.close()

    def update_rule(self, rule_id: int, **kwargs) -> bool:
        """更新规则"""
        db = SessionLocal()
        try:
            rule = db.query(DetectionRule).filter(DetectionRule.id == rule_id).first()
            if not rule:
                return False
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            db.commit()
            self.load_rules()
            return True
        finally:
            db.close()

    def get_all_rules(self) -> list:
        """返回所有规则"""
        return self.rules
