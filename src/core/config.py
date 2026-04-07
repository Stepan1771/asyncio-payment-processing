from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


BASE_DIR = Path(__file__).parent.parent.parent
APP_ENV_PATH = BASE_DIR / ".env.app"
DB_ENV_PATH = BASE_DIR / ".env.db"
BROKER_ENV_PATH = BASE_DIR / ".env.broker"
PUBLISHER_ENV_PATH = BASE_DIR / ".env.publisher"
CONSUMER_ENV_PATH = BASE_DIR / ".env.consumer"
HTTPX_ENV_PATH = BASE_DIR / ".env.httpx"


class AppConfig(BaseModel):
    service_name: str
    host: str
    port: int


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    payments: str = "/payments"


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class AuthConfig(BaseModel):
    api_key: str


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=APP_ENV_PATH,
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    app: AppConfig
    api: ApiPrefix = ApiPrefix()
    auth: AuthConfig


class DatabaseConfig(BaseModel):
    service_name: str
    user: str
    password: str
    name: str
    host: str
    port: int
    echo: bool
    echo_pool: bool
    max_overflow: int
    pool_size: int

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=DB_ENV_PATH,
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="DB_CONFIG__",
    )
    db: DatabaseConfig


class RabbitMQConfig(BaseModel):
    service_name: str
    host: str
    port: int
    user: str
    password: str
    vhost: str

    payments_exchange: str
    payments_dlx_exchange: str

    payments_queue: str
    payments_dead_queue: str

    payments_queue_routing_key: str
    payments_dead_queue_routing_key: str

    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/{self.vhost}"


class BrokerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BROKER_ENV_PATH,
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="BROKER_CONFIG__",
    )
    broker: RabbitMQConfig



class PublisherConfig(BaseModel):
    service_name: str


class OutboxWorkerConfig(BaseModel):
    poll_interval: float = 2.0
    error_backoff: float = 5.0
    batch_size: int = 100


class PublisherSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PUBLISHER_ENV_PATH,
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="PUBLISHER_CONFIG__",
    )
    publisher: PublisherConfig
    outbox_worker: OutboxWorkerConfig = OutboxWorkerConfig()


class ConsumerConfig(BaseModel):
    service_name: str
    max_retries: int


class ConsumerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=CONSUMER_ENV_PATH,
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="CONSUMER_CONFIG__",
    )
    consumer: ConsumerConfig


class HTTPXConfig(BaseModel):
    max_concurrency: int
    max_connections: int
    max_keepalive: int
    timeout_connect: float
    timeout_read: float
    timeout_write: float
    timeout_pool: float


class HttpxSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=HTTPX_ENV_PATH,
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="HTTPX_CONFIG__",
    )
    httpx: HTTPXConfig


from functools import lru_cache


@lru_cache(maxsize=1)
def _get_app_settings() -> "AppSettings":
    return AppSettings()


@lru_cache(maxsize=1)
def _get_db_settings() -> "DatabaseSettings":
    return DatabaseSettings()


@lru_cache(maxsize=1)
def _get_broker_settings() -> "BrokerSettings":
    return BrokerSettings()


@lru_cache(maxsize=1)
def _get_publisher_settings() -> "PublisherSettings":
    return PublisherSettings()


@lru_cache(maxsize=1)
def _get_consumer_settings() -> "ConsumerSettings":
    return ConsumerSettings()


@lru_cache(maxsize=1)
def _get_httpx_settings() -> "HttpxSettings":
    return HttpxSettings()


_SETTINGS_MAP = {
    "app_settings": _get_app_settings,
    "db_settings": _get_db_settings,
    "broker_settings": _get_broker_settings,
    "publisher_settings": _get_publisher_settings,
    "consumer_settings": _get_consumer_settings,
    "httpx_settings": _get_httpx_settings,
}


def __getattr__(name: str):
    """Ленивая инициализация — настройки создаются только при первом обращении."""
    if name in _SETTINGS_MAP:
        return _SETTINGS_MAP[name]()
    raise AttributeError(f"module 'core.config' has no attribute {name!r}")
