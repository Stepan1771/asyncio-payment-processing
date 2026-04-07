import asyncio
import os
from logging.config import fileConfig

from alembic import context


_DB_URL = "postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}".format(
    user=os.environ.get("DB_CONFIG__DB__USER", "postgres"),
    password=os.environ.get("DB_CONFIG__DB__PASSWORD", "postgres"),
    host=os.environ.get("DB_CONFIG__DB__HOST", "localhost"),
    port=os.environ.get("DB_CONFIG__DB__PORT", "5432"),
    name=os.environ.get("DB_CONFIG__DB__NAME", "db"),
)

from models.base import Base
import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=_DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(_DB_URL)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

