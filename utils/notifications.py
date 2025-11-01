import smtplib
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages email and Discord notifications."""

    @staticmethod
    async def send_completion_notification(idea_id: str, summary: Dict):
        """Send notifications when idea processing completes."""
        status = summary.get("status", "unknown")
        idea_text = summary.get("idea_text", "Unknown idea")[:100]

        subject = f"Research Swarm: {status.upper()} - {idea_text}"
        body = NotificationManager._format_summary(summary)

        await NotificationManager._send_all(subject, body, summary)

    @staticmethod
    async def send_error_notification(idea_id: str, error: str):
        """Send notification for processing errors."""
        subject = f"Research Swarm: ERROR - {idea_id}"
        body = f"Processing failed for idea {idea_id}\n\nError: {error}"

        await NotificationManager._send_all(subject, body, {"error": error})

    @staticmethod
    async def send_hitl_notification(idea_id: str, question: str, options: list):
        """Send notification requesting human input."""
        subject = f"Research Swarm: INPUT NEEDED - {idea_id}"
        body = f"Question: {question}\n\nOptions:\n" + "\n".join(f"- {opt}" for opt in options)

        await NotificationManager._send_all(subject, body, {
            "question": question,
            "options": options
        })

    @staticmethod
    async def _send_all(subject: str, body: str, data: Dict):
        """Send via all configured notification channels."""
        tasks = []

        if settings.email_from and settings.email_to:
            try:
                NotificationManager._send_email(subject, body)
                logger.info("Email notification sent")
            except Exception as e:
                logger.error(f"Email notification failed: {e}")

        if settings.discord_webhook:
            try:
                await NotificationManager._send_discord(subject, body, data)
                logger.info("Discord notification sent")
            except Exception as e:
                logger.error(f"Discord notification failed: {e}")

    @staticmethod
    def _send_email(subject: str, body: str):
        """Send email notification."""
        if not all([settings.email_from, settings.email_to, settings.email_password]):
            logger.warning("Email not configured, skipping")
            return

        msg = MIMEMultipart()
        msg['From'] = settings.email_from
        msg['To'] = settings.email_to
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(settings.email_smtp_server, settings.email_smtp_port) as server:
                server.starttls()
                server.login(settings.email_from, settings.email_password)
                server.send_message(msg)

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    @staticmethod
    async def _send_discord(subject: str, body: str, data: Dict):
        """Send Discord webhook notification."""
        if not settings.discord_webhook:
            logger.warning("Discord not configured, skipping")
            return

        color = {
            "completed": 0x00ff00,
            "failed": 0xff0000,
            "error": 0xff0000,
            "input_needed": 0xffaa00
        }.get(data.get("status", "unknown"), 0x0099ff)

        embed = {
            "title": subject,
            "description": body[:2000],
            "color": color,
            "footer": {
                "text": "Research Swarm"
            }
        }

        if data.get("result_url"):
            embed["fields"] = [
                {
                    "name": "Result",
                    "value": data["result_url"],
                    "inline": False
                }
            ]

        payload = {
            "embeds": [embed]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    settings.discord_webhook,
                    json=payload
                ) as response:
                    if response.status not in [200, 204]:
                        error_text = await response.text()
                        raise Exception(f"Discord API error: {response.status} - {error_text}")

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            raise

    @staticmethod
    def _format_summary(summary: Dict) -> str:
        """Format summary for notification."""
        lines = [
            f"Idea ID: {summary.get('idea_id', 'Unknown')}",
            f"Status: {summary.get('status', 'Unknown')}",
            "",
            f"Idea: {summary.get('idea_text', 'No description')[:200]}",
            "",
            f"Complexity: {summary.get('complexity', 'Unknown')}",
            f"Research Conducted: {'Yes' if summary.get('research_conducted') else 'No'}",
            f"Implementation Generated: {'Yes' if summary.get('implementation_generated') else 'No'}",
            f"Tests Passed: {'Yes' if summary.get('tests_passed') else 'No'}",
            "",
            f"Started: {summary.get('started_at', 'Unknown')}",
            f"Completed: {summary.get('completed_at', 'Unknown')}",
            "",
            "Message:",
            summary.get('message', 'No message available')
        ]

        if summary.get('errors'):
            lines.append("")
            lines.append("Errors:")
            for error in summary['errors']:
                lines.append(f"- {error}")

        return "\n".join(lines)
