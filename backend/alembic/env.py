from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.core.config import settings
from app.db.base import Base

# Import all models so Alembic sees the complete SQLAlchemy metadata.
from app.models.financial import (
    Merchant,
    Order,
    Payment,
    Settlement,
    Refund,
    Fee,
    Adjustment,
)

from app.models.reconciliation import (
    ReconciliationRun,
    ReconciliationResult,
    ExceptionRecord,
    Evidence,
    Investigation,
    HumanReview,
    AuditLog,
)


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the application's DATABASE_URL rather than a hardcoded
# database connection from alembic.ini.
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url.replace("%", "%%"),
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()