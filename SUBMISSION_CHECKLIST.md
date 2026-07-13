"""Environment-based configuration for development, testing, and Render."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def env_flag(name: str, default: bool = False) -> bool:
    """Read a common truthy or falsey environment variable."""
    fallback = "1" if default else "0"
    return os.getenv(name, fallback).strip().lower() in {"1", "true", "yes", "on"}


def normalize_database_url(database_url: str) -> str:
    """Normalize Render PostgreSQL URLs for SQLAlchemy's psycopg2 driver."""
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return database_url


def parse_schemes(value: str, default: str) -> list[str]:
    """Convert a comma-separated scheme list into Swagger's list format."""
    schemes = [item.strip() for item in value.split(",") if item.strip()]
    return schemes or [default]


class BaseConfig:
    """Settings shared by all environments."""

    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "60"))

    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_ENABLED = True

    SWAGGER = {"title": "Mechanic Shop API", "uiversion": 3}
    SWAGGER_HOST = os.getenv("SWAGGER_HOST", "127.0.0.1:5000")
    SWAGGER_SCHEMES = parse_schemes(os.getenv("SWAGGER_SCHEMES", "http"), "http")

    AUTO_CREATE_DB = env_flag("AUTO_CREATE_DB", True)
    ENVIRONMENT_NAME = "base"


class DevelopmentConfig(BaseConfig):
    """Local development configuration using SQLite by default."""

    ENVIRONMENT_NAME = "development"
    DEBUG = env_flag("FLASK_DEBUG", True)
    SECRET_KEY = os.getenv("SECRET_KEY", "development-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-jwt-secret-key")
    SQLALCHEMY_DATABASE_URI = normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            f"sqlite:///{(BASE_DIR / 'instance' / 'mechanic_shop.db').as_posix()}",
        )
    )


class ProductionConfig(BaseConfig):
    """Render production configuration supplied exclusively by environment variables."""

    ENVIRONMENT_NAME = "production"
    DEBUG = False
    TESTING = False

    DATABASE_URL = os.getenv("DATABASE_URL", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "") or SECRET_KEY
    SQLALCHEMY_DATABASE_URI = normalize_database_url(DATABASE_URL)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    SWAGGER_HOST = os.getenv(
        "SWAGGER_HOST",
        os.getenv("RENDER_EXTERNAL_HOSTNAME", ""),
    )
    SWAGGER_SCHEMES = ["https"]
    AUTO_CREATE_DB = env_flag("AUTO_CREATE_DB", False)


class TestConfig(BaseConfig):
    """Isolated configuration for the automated test suite."""

    ENVIRONMENT_NAME = "testing"
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-secret-key"
    JWT_SECRET_KEY = "test-jwt-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CACHE_TYPE = "SimpleCache"
    RATELIMIT_ENABLED = False
    AUTO_CREATE_DB = False
    SWAGGER_HOST = "localhost"
    SWAGGER_SCHEMES = ["http"]
