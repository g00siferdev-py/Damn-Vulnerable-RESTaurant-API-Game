import os
import random
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


class ENV(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


ENVIRONMENT = ENV(os.getenv("ENV", ENV.PRODUCTION.value))


# 6 digits random secrets are secure enough,
# I don't believe someone could brute-force them
def generate_random_secret():
    return "".join(random.choices("1234567890", k=6))


class Settings:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", generate_random_secret())
    CHEF_USERNAME = os.getenv("CHEF_USERNAME", "chef")

    # JWT signatures must be verified by default. Never accept unsigned
    # or tampered tokens in production.
    JWT_VERIFY_SIGNATURE: bool = os.getenv("JWT_VERIFY_SIGNATURE", "True").lower() in (
        "true",
        "1",
        "yes",
    )

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    # Do not ship with a hardcoded fallback database password. The
    # application requires an explicit credential when Postgres is used.
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", 5432)
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "restaurant")

    TITLE: str = "Damn Vulnerable RESTaurant"
    DESCRIPTION: str = (
        "An intentionally vulnerable API service designed for learning and training purposes for ethical hackers, security engineers"
        ", and developers."
    )
    VERSION: str = "1.0.0"

    # Allow switching between Postgres (default) and in-memory SQLite.
    # This keeps Postgres as the default behavior while enabling
    # self-contained in-memory runs when DB_BACKEND=memory is set.
    DB_BACKEND: str = os.getenv("DB_BACKEND", "postgres")

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_BACKEND == "memory":
            return "sqlite://"
        if not self.POSTGRES_PASSWORD:
            raise ValueError(
                "POSTGRES_PASSWORD environment variable is required when using Postgres backend"
            )
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SERVER_URL(self) -> str:
        return "http://localhost:8091/"

    @property
    def SERVERS(self) -> list[dict]:
        return [{"url": self.SERVER_URL, "description": self.SERVER_DESCRIPTION}]

    @property
    def ROOT_PATH(self) -> str:
        return ""

    @property
    def SERVER_DESCRIPTION(self) -> str:
        return "Local API server"


settings = Settings()
