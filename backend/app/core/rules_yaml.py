"""
默认检测规则（用于初始化数据库）
"""

DEFAULT_RULES = [
    # ========== 高敏感级别 ==========
    {
        'name': '中国大陆居民身份证号',
        'pattern': r'(?<!\d)[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)',
        'data_type': 'id_card',
        'severity': 'high',
        'description': '18位身份证号码',
        'is_active': True,
    },
    {
        'name': '手机号',
        'pattern': r'(?<!\d)1[3-9]\d{9}(?!\d)',
        'data_type': 'phone',
        'severity': 'high',
        'description': '中国大陆11位手机号码',
        'is_active': True,
    },
    {
        'name': '银行卡号',
        'pattern': r'(?<!\d)[625]\d{15,18}(?!\d)',
        'data_type': 'bank_card',
        'severity': 'high',
        'description': '16-19位银行卡号（以62/25/51开头）',
        'is_active': True,
    },
    # ========== 中敏感级别 ==========
    {
        'name': '邮箱地址',
        'pattern': r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',
        'data_type': 'email',
        'severity': 'medium',
        'description': '标准邮箱格式',
        'is_active': True,
    },
    # ========== 低敏感级别 ==========
    {
        'name': '座机电话',
        'pattern': r'(?<!\d)0\d{2,3}-?\d{7,8}(?!\d)',
        'data_type': 'landline',
        'severity': 'low',
        'description': '带区号的固定电话',
        'is_active': True,
    },
    {
        'name': '内网IP地址',
        'pattern': r'(?<!\d)10\.\d{1,3}\.\d{1,3}\.\d{1,3}(?!\d)|(?<!\d)192\.168\.\d{1,3}\.\d{1,3}(?!\d)',
        'data_type': 'internal_ip',
        'severity': 'low',
        'description': '内网IP地址段',
        'is_active': True,
    },
    # ========== 通用关键字组合 ==========
    {
        'name': '密码泄露关键字',
        'pattern': r'(?i)(password|passwd|pwd|密码|口令)\s*[::=]\s*\S+',
        'data_type': 'password',
        'severity': 'high',
        'description': '明文密码配置或记录',
        'is_active': True,
    },
]
