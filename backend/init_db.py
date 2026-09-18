import sys
sys.path.insert(0, '.')
from app.database import engine, Base
from app.models import website, leak, alert, rule, report  # noqa: F401

# 创建所有表
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")

# 插入默认检测规则（如果不存在）
from app.database import SessionLocal
from app.models.rule import DetectionRule
from app.core.rules_yaml import DEFAULT_RULES

db = SessionLocal()
try:
    for rule_data in DEFAULT_RULES:
        existing = db.query(DetectionRule).filter(DetectionRule.name == rule_data['name']).first()
        if not existing:
            db.add(DetectionRule(
                name=rule_data['name'],
                pattern=rule_data['pattern'],
                data_type=rule_data['data_type'],
                severity=rule_data['severity'],
                description=rule_data.get('description', ''),
                is_active=rule_data.get('is_active', True),
            ))
            print(f"Added rule: {rule_data['name']}")

    db.commit()
    total = db.query(DetectionRule).count()
    print(f"Default rules initialized. Total: {total} rules.")
finally:
    db.close()
