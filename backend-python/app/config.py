import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_list(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _resolve_path(raw_path: str) -> Path:
    # Allow env vars to use either absolute paths or repo-relative paths.
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    api_host: str
    api_port: int
    cors_origins: list[str]
    trusted_hosts: list[str]
    data_source: str
    data_csv_path: Path
    mysql_url: str | None
    seed_demo_data: bool
    admin_user_id: str
    admin_name: str
    admin_email: str
    admin_password: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Cache settings so every import in the app reads the same resolved config.
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    return Settings(
        app_name=os.getenv("APP_NAME", "Sustainability Analytics API").strip(),
        app_version=os.getenv("APP_VERSION", "1.0.0").strip(),
        environment=environment,
        api_host=os.getenv("API_HOST", "0.0.0.0").strip(),
        api_port=int(os.getenv("API_PORT", "8000")),
        cors_origins=_csv_list(
            os.getenv("CORS_ORIGINS"),
            ["*"] if environment != "production" else ["https://dashboard.example.com"],
        ),
        trusted_hosts=_csv_list(
            os.getenv("TRUSTED_HOSTS"),
            ["*"] if environment != "production" else ["dashboard.example.com"],
        ),
        # The app can load metrics from a CSV for local demos or MySQL in deployment.
        data_source=os.getenv("DATA_SOURCE", "csv").strip().lower(),
        data_csv_path=_resolve_path(
            os.getenv("DATA_CSV_PATH", "backend-python/data/sample_data.csv")
        ),
        mysql_url=os.getenv("MYSQL_URL"),
        seed_demo_data=_as_bool(
            os.getenv("SEED_DEMO_DATA"),
            default=environment != "production",
        ),
        admin_user_id=os.getenv("ADMIN_USER_ID", "admin").strip(),
        admin_name=os.getenv("ADMIN_NAME", "Platform Admin").strip(),
        admin_email=os.getenv("ADMIN_EMAIL", "admin@example.com").strip(),
        admin_password=os.getenv("ADMIN_PASSWORD", "ChangeMe123!").strip(),
    )
