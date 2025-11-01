#!/usr/bin/env python3
"""Initialize the research repository and verify configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from utils.repository import RepositoryManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize repository and verify setup."""
    logger.info("Initializing Research Swarm...")

    logger.info(f"Repository path: {settings.repository_path}")
    repo_manager = RepositoryManager(settings.repository_path)

    logger.info("Repository initialized successfully")

    logger.info("\nConfiguration:")
    logger.info(f"- OpenAI API Key: {'✓ Set' if settings.openai_api_key else '✗ Missing'}")
    logger.info(f"- Redis URL: {settings.redis_url}")
    logger.info(f"- Max Iterations: {settings.max_iterations}")
    logger.info(f"- Default Model: {settings.default_model}")

    logger.info(f"- Email Notifications: {'✓ Enabled' if settings.email_from else '✗ Disabled'}")
    logger.info(f"- Discord Notifications: {'✓ Enabled' if settings.discord_webhook else '✗ Disabled'}")

    logger.info("\nVerifying Redis connection...")
    try:
        from redis import Redis
        redis_client = Redis.from_url(settings.redis_url)
        redis_client.ping()
        logger.info("✓ Redis connection successful")
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        logger.error("Please ensure Redis is running")
        return 1

    logger.info("\n✓ Initialization complete!")
    logger.info("\nNext steps:")
    logger.info("1. Start the API: python -m uvicorn api.main:app --reload")
    logger.info("2. Start the worker: python orchestrator/worker.py")
    logger.info("3. Submit an idea: curl -X POST http://localhost:8000/api/v1/ideas -H 'Content-Type: application/json' -d '{\"idea\": \"Your idea here\"}'")

    return 0


if __name__ == "__main__":
    sys.exit(main())
