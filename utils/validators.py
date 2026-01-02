# Validation utilities for API credentials and configuration

import logging
from typing import Dict, List, Optional
from .exceptions import MissingAPIKeyError

logger = logging.getLogger(__name__)


def validate_required_settings(settings_dict: Dict[str, any], service_name: str, instructions: Optional[str] = None) -> None:
    # Validate that all required settings are present and non-empty
    missing_keys = []
    placeholder_patterns = ['your-', 'placeholder', 'change-this', 'example', 'xxx', 'yyy']

    for key, value in settings_dict.items():
        if not value or (isinstance(value, str) and value.strip() == ''):
            missing_keys.append(key)
        elif isinstance(value, str):
            # Check for common placeholder patterns
            value_lower = value.lower().strip()
            if any(pattern in value_lower for pattern in placeholder_patterns):
                missing_keys.append(key)

    if missing_keys:
        logger.error(f"{service_name} validation failed. Missing/placeholder keys: {', '.join(missing_keys)}")
        raise MissingAPIKeyError(service_name, missing_keys, instructions)

    logger.info(f"{service_name} credentials validated successfully")


def validate_github_credentials(github_token: str) -> None:
    instructions = """
To obtain GitHub API token:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: public_repo, read:org (for searching public repos)
4. Copy the token and add it to your .env file as GITHUB_TOKEN
Note: Without a token, you're limited to 60 requests/hour. With token: 5,000 requests/hour.
"""

    settings_dict = {
        'GITHUB_TOKEN': github_token,
    }

    validate_required_settings(settings_dict, 'GitHub', instructions)


def validate_telegram_credentials(bot_token: str, chat_id: str) -> None:
    instructions = """
To set up Telegram Bot:
1. Open Telegram and search for @BotFather
2. Send /newbot command and follow the instructions
3. Copy the bot token provided by BotFather

To get your Chat ID:
1. Send a message to your bot
2. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
3. Look for "chat":{"id": YOUR_CHAT_ID} in the response
4. Add both the bot token and chat ID to your .env file
"""

    settings_dict = {
        'TELEGRAM_BOT_TOKEN': bot_token,
        'TELEGRAM_CHAT_ID': chat_id,
    }

    validate_required_settings(settings_dict, 'Telegram', instructions)


def validate_huggingface_credentials(api_key: str) -> None:
    instructions = """
To obtain Hugging Face API key:
1. Go to https://huggingface.co/settings/tokens
2. Create a new access token (read access is sufficient)
3. Copy the token and add it to your .env file as HUGGINGFACE_API_KEY
"""

    settings_dict = {
        'HUGGINGFACE_API_KEY': api_key,
    }

    validate_required_settings(settings_dict, 'Hugging Face', instructions)


def check_optional_service(service_name: str, required_settings: Dict[str, any]) -> bool:
    # Check if an optional service is configured
    missing_keys = []
    placeholder_patterns = ['your-', 'placeholder', 'change-this', 'example', 'xxx', 'yyy']

    for key, value in required_settings.items():
        if not value or (isinstance(value, str) and value.strip() == ''):
            missing_keys.append(key)
        elif isinstance(value, str):
            # Check for common placeholder patterns
            value_lower = value.lower().strip()
            if any(pattern in value_lower for pattern in placeholder_patterns):
                missing_keys.append(key)

    if missing_keys:
        logger.warning(
            f"{service_name} is not configured. Missing/placeholder: {', '.join(missing_keys)}. "
            f"This service will be skipped."
        )
        return False

    logger.info(f"{service_name} is configured and ready")
    return True
