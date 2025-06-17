import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv

# Add the project root directory to sys.path
# This allows Alembic to find the auth_service modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()  # Load .env file

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from database.session import Base  # Import Base from our session module
# Import models to ensure they are registered with Base
import models.user_model
import models.otp_model
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Load database URL from environment variables or use config setting
def get_url():
    # First try to get from DATABASE_URL environment variable
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Fallback to individual components
    user = os.getenv("POSTGRES_USER", "user")
    password = os.getenv("POSTGRES_PASSWORD", "password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "auth_service_dev")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()  # Use the function to get URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Construct the dictionary for engine_from_config
    # ensuring sqlalchemy.url is set from environment variables
    configuration = config.get_section(config.config_ini_section, {})
    configuration['sqlalchemy.url'] = get_url()

    connectable = engine_from_config(
        configuration,  # Use the modified configuration
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
