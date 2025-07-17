import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# Agregar la carpeta raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar tu engine y Base
from Database.getConnection import engine
from Database.getConnection import Base  # tu Base declarative_base()
from models import order  # importa tus modelos aquí

# Configuración de Alembic
config = context.config
# fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise Exception("No usamos modo offline.")
else:
    run_migrations_online()