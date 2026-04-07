from .base import BaseDatabaseClient

from core.config import db_settings


db_client = BaseDatabaseClient(
    url=db_settings.db.url,
    echo=db_settings.db.echo,
    echo_pool=db_settings.db.echo_pool,
    max_overflow=db_settings.db.max_overflow,
    pool_size=db_settings.db.pool_size,
)
