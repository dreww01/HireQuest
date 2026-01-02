from telegram import Bot
from telegram.error import TelegramError, InvalidToken
from django.conf import settings
import logging
import asyncio
from utils.validators import validate_telegram_credentials
from utils.exceptions import MissingAPIKeyError, InvalidAPIKeyError, APIConnectionError

logger = logging.getLogger(__name__)


class TelegramClient:
    # Telegram Bot client wrapper

    def __init__(self):
        logger.info("Initializing Telegram client")

        try:
            validate_telegram_credentials(
                bot_token=settings.TELEGRAM_BOT_TOKEN,
                chat_id=settings.TELEGRAM_CHAT_ID
            )
        except MissingAPIKeyError:
            logger.error("Telegram client initialization failed: missing credentials")
            raise

        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID

        try:
            self.bot = Bot(token=self.bot_token)
            logger.info("Telegram client initialized successfully")
        except InvalidToken as e:
            logger.error(f"Invalid Telegram bot token: {str(e)}")
            raise InvalidAPIKeyError(
                'Telegram',
                'The TELEGRAM_BOT_TOKEN is invalid. Please verify you copied the complete token from @BotFather.'
            )
        except Exception as e:
            logger.error(f"Error initializing Telegram bot: {str(e)}")
            raise APIConnectionError('Telegram', e)

    def send_alert(self, job_post, qualification=None, draft=None, dashboard_url=None):
        # Send job alert to Telegram with dashboard link
        logger.info(f"Sending Telegram alert for job: {job_post.title}")

        # Build simple message
        message_parts = [
            "🚨 *NEW JOB ALERT*",
            "",
            f"*{self._escape_markdown(job_post.title)}*",
            "",
            "📍 *Source:* " + job_post.source.get_type_display(),
            "",
            "*📋 Job Description*",
            self._escape_markdown(job_post.body[:500] + "..." if len(job_post.body) > 500 else job_post.body),
        ]

        if dashboard_url:
            message_parts.append("")
            message_parts.append(f"[View Full Details on Dashboard →]({dashboard_url})")

        message = "\n".join(message_parts)

        try:
            result = asyncio.run(self._send_message_async(message))
            logger.info(f"Successfully sent Telegram alert, message ID: {result.message_id}")
            return result.message_id
        except TelegramError as e:
            logger.error(f"Telegram API error: {str(e)}")
            error_msg = str(e).lower()
            
            if 'unauthorized' in error_msg or 'token' in error_msg:
                raise InvalidAPIKeyError(
                    'Telegram',
                    'Bot token is invalid or the bot was deleted. Please verify TELEGRAM_BOT_TOKEN.'
                )
            elif 'chat not found' in error_msg or 'chat_id' in error_msg:
                raise InvalidAPIKeyError(
                    'Telegram',
                    f'Chat ID {self.chat_id} is invalid or the bot cannot access this chat. '
                    'Please verify TELEGRAM_CHAT_ID and ensure you have sent a message to the bot first.'
                )
            raise APIConnectionError('Telegram', e)
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram alert: {str(e)}")
            raise APIConnectionError('Telegram', e)

    async def _send_message_async(self, message):
        return await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    def send_simple_alert(self, job_post):
        return self.send_alert(job_post, None, None)

    def _escape_markdown(self, text):
        # Escape special markdown characters
        if not text:
            return ""

        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

        for char in special_chars:
            text = text.replace(char, f'\\{char}')

        return text
