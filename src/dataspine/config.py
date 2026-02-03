"""Configuration management for dataspine."""

import os
import sys
from typing import Any

from dotenv import load_dotenv


def load_config() -> dict[str, Any]:
    """
    Load configuration from environment variables.

    Raises:
        SystemExit: If required environment variables are missing.

    Returns:
        Dict containing configuration values.
    """
    load_dotenv()

    required_vars = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASS",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
        sys.exit(1)

    config = {
        "db_host": os.getenv("DB_HOST"),
        "db_port": int(os.getenv("DB_PORT", "5432")),
        "db_name": os.getenv("DB_NAME"),
        "db_user": os.getenv("DB_USER"),
        "db_pass": os.getenv("DB_PASS"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "app_env": os.getenv("APP_ENV", "development"),
    }

    return config
