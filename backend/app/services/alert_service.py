"""
告警服务
作用：
1. 发现高严重级别泄露后，自动发送邮件告警
2. 同时生成站内消息
3. 记录告警发送状态，支持重试和追溯
做法：
1. 构造告警内容（包含泄露类型、位置、严重程度）
2. 通过 SMTP 发送邮件给管理员
3. 在数据库中创建 AlertLog 记录
4. 标记告警状态为 sent/pending
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from app.models.leak import LeakRecord
from app.models.alert import AlertLog, AlertStatus
from app.config import get_settings


class AlertService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    async def send_alert(self, leak: LeakRecord):
        """发送告警（仅高严重级别）"""
        if leak.severity != "high":
            return

        subject = f"[敏感信息告警] {leak.data_type} - {leak.severity.upper()}"
        body = self._build_alert_body(leak)

        # 如果 leak 还没有 ID（新创建的记录），先保存它
        if leak.id is None:
            self.db.add(leak)
            self.db.flush()

        success = await self._send_email_alert(subject, body, leak)

        if success:
            alert_log = AlertLog(
                leak_record_id=leak.id,
                channel="email",
                status=AlertStatus.SENT,
                recipient=self.settings.ALERT_EMAIL_TO,
                content=subject,
            )
            self.db.add(alert_log)
            self.db.commit()

    def _build_alert_body(self, leak: LeakRecord) -> str:
        """构造告警邮件正文（HTML格式）"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #e74c3c;">敏感信息泄露告警</h2>
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
                <tr><td><strong>检测时间</strong></td><td>{leak.detected_at}</td></tr>
                <tr><td><strong>泄露类型</strong></td><td>{leak.data_type}</td></tr>
                <tr><td><strong>严重程度</strong></td><td style="color: red;">{leak.severity.upper()}</td></tr>
                <tr><td><strong>来源URL</strong></td><td>{leak.source_url}</td></tr>
                <tr><td><strong>匹配内容</strong></td><td>{leak.matched_text}</td></tr>
                <tr><td><strong>上下文</strong></td><td>{leak.context_before}...{leak.context_after}</td></tr>
            </table>
            <p style="margin-top: 20px; color: #666; font-size: 12px;">请及时处理此告警。</p>
        </body>
        </html>
        """

    async def _send_email_alert(self, subject: str, body: str, leak: LeakRecord) -> bool:
        """通过 SMTP 发送邮件，返回是否成功"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.settings.ALERT_EMAIL_FROM
            msg["To"] = self.settings.ALERT_EMAIL_TO
            msg.attach(MIMEText(body, "html", "utf-8"))

            server = smtplib.SMTP_SSL(self.settings.ALERT_EMAIL_HOST, 465)
            server.login(self.settings.ALERT_EMAIL_USER, self.settings.ALERT_EMAIL_PASSWORD)
            server.sendmail(self.settings.ALERT_EMAIL_FROM, [self.settings.ALERT_EMAIL_TO], msg.as_string())
            server.quit()
            return True

        except Exception as e:
            error_log = AlertLog(
                leak_record_id=leak.id,
                channel="email",
                status=AlertStatus.PENDING,
                recipient=self.settings.ALERT_EMAIL_TO,
                content=subject,
                error_message=str(e),
            )
            self.db.add(error_log)
            self.db.commit()
            print(f"[AlertService] Email send failed: {e}")
            return False
