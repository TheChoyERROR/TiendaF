# Alembic configuration file
# Alembic is a lightweight database migration tool for usage with SQLAlchemy
# This file is used for configuration and environment settings

from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
import os
import sys
from dotenv import load_dotenv

# Añadir la ruta del proyecto al path de Python
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

# Importar los modelos
from app.models.models import Base

# Cargar variables de entorno
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Configuración de Alembic
config = context.config

# Interpretar el archivo de configuración para Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Establecer la URL de la base de datos desde variables de entorno
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Objetivo de la migración: todos los modelos de SQLAlchemy
target_metadata = Base.metadata

def run_migrations_offline():
    """
    Ejecutar migraciones en modo 'offline'.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """
    Ejecutar migraciones en modo 'online'.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()