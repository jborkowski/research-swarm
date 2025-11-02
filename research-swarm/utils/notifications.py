import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
from typing import Optional, Dict, Any
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    """Handles sending notifications via email and Discord"""

    def __init__(self):
        self.email_enabled = bool(settings.email_from and settings.email_to)
        self.discord_enabled = bool(settings.discord_webhook)

    async def send_completion_notification(self, idea_id: str, report: Dict[str, Any]) -> None:
        """Send notification when research workflow completes"""
        subject = f"Research Swarm: Idea {idea_id} {'Completed' if report.get('status') == 'completed' else 'Failed'}"

        message = self._format_completion_message(idea_id, report)

        if self.email_enabled:
            await self._send_email(subject, message)

        if self.discord_enabled:
            await self._send_discord_notification(subject, message)

    async def send_error_notification(self, idea_id: str, error: str) -> None:
        """Send notification when workflow encounters an error"""
        subject = f"Research Swarm: Error in Idea {idea_id}"

        message = f"Error occurred while processing idea {idea_id}:\n\n{error}"

        if self.email_enabled:
            await self._send_email(subject, message)

        if self.discord_enabled:
            await self._send_discord_notification(subject, message)

    def _format_completion_message(self, idea_id: str, report: Dict[str, Any]) -> str:
        """Format completion message for notifications"""
        status = report.get('status', 'unknown')
        summary = report.get('summary', 'No summary available')

        message = f"""Research workflow completed for idea {idea_id}

Status: {status.upper()}
Summary: {summary}

Details:
- Iterations used: {report.get('iterations_used', 'N/A')}
- Errors: {len(report.get('errors', []))}
"""

        if report.get('test_results'):
            test_results = report['test_results']
            message += f"- Tests passed: {test_results.get('passed', 'N/A')}\n"
            message += f"- Coverage: {test_results.get('coverage', 'N/A')}\n"

        if report.get('implementation'):
            artifacts = report['implementation']
            message += f"- Code artifacts: {len(artifacts) if isinstance(artifacts, list) else 'N/A'}\n"

        return message

    async def _send_email(self, subject: str, message: str) -> None:
        """Send email notification"""
        if not settings.email_from or not settings.email_to:
            logger.warning("Email settings not configured, skipping email notification")
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = settings.email_from
            msg['To'] = settings.email_to
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP(settings.email_smtp_server, 587)
            server.starttls()
            # Note: In production, use proper authentication
            # server.login(settings.email_username, settings.email_password)
            server.sendmail(settings.email_from, settings.email_to, msg.as_string())
            server.quit()

            logger.info(f"Email notification sent for subject: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    async def _send_discord_notification(self, title: str, message: str) -> None:
        """Send Discord webhook notification"""
        if not settings.discord_webhook:
            logger.warning("Discord webhook not configured, skipping Discord notification")
            return

        try:
            embed = {
                "title": title,
                "description": message,
                "color": 3066993 if "Completed" in title else 15158332,  # Green for success, red for failure
                "footer": {
                    "text": "Research Swarm"
                }
            }

            payload = {
                "embeds": [embed]
            }

            response = requests.post(
                settings.discord_webhook,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 204:
                logger.info(f"Discord notification sent for: {title}")
            else:
                logger.error(f"Failed to send Discord notification: {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

# Global notification manager instance
notification_manager = NotificationManager()