from logging.config import fileConfig
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from src.config import get_settings
from src.core.database import Base
from src.models import data_models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def _get_alembic_database_url(database_url: str) -> str:
    sync_url = database_url.replace("+asyncpg", "", 1)
    parsed = urlparse(sync_url)
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    normalized_pairs: list[tuple[str, str]] = []

    for key, value in query_pairs:
        if key == "ssl":
            normalized_pairs.append(("sslmode", value))
        else:
            normalized_pairs.append((key, value))

    return urlunparse(parsed._replace(query=urlencode(normalized_pairs)))


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
settings = get_settings()
config.set_main_option("sqlalchemy.url", _get_alembic_database_url(settings.DATABASE_URL))

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
