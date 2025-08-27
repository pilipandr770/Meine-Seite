import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

def get_url():
    url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URI')
    if not url:
        raise RuntimeError('DATABASE_URL not set for Alembic')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    # force pg8000 if psycopg2 likely missing
    if url.startswith('postgresql://') and 'postgresql+pg8000://' not in url:
        try:
            import psycopg2  # noqa
        except Exception:
            url = url.replace('postgresql://', 'postgresql+pg8000://', 1)
    return url

schema = os.getenv('POSTGRES_SCHEMA', 'rozoom_schema')

def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        version_table_schema=schema,
        output_buffer=None,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section) or {}
    configuration['sqlalchemy.url'] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        connection.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=schema,
            version_table=f"alembic_version_{schema}",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
