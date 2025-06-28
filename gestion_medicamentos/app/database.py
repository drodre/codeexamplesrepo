from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base # Importar Base desde models.py

DATABASE_URL = "sqlite:///./data/medicamentos.db"
# El /// indica una ruta relativa desde donde se ejecute el script.
# Si ejecutamos desde la raíz de gestion_medicamentos, se creará en gestion_medicamentos/data/medicamentos.db

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} # Necesario para SQLite si se usa en threads diferentes (ej. en web apps)
)

# La SessionLocal será la factoría para crear sesiones de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    """
    Crea el archivo de base de datos y todas las tablas definidas en los modelos.
    Esta función debe llamarse una vez al inicio de la aplicación o mediante un script.
    """
    # Asegurarse de que el directorio data exista
    import os
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data') # gestion_medicamentos/data
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Directorio '{data_dir}' creado.")

    # Crear todas las tablas en el motor. Esto es equivalente a "Create Table"
    # en SQL crudo.
    Base.metadata.create_all(bind=engine)
    print(f"Base de datos y tablas creadas en {DATABASE_URL.replace('sqlite:///./', '')}")

def get_db():
    """
    Función generadora para obtener una sesión de base de datos.
    Útil para inyección de dependencias en aplicaciones web (ej. FastAPI).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    # Esto permite ejecutar este archivo directamente para crear la BD y tablas.
    # python -m app.database (si estás en el directorio gestion_medicamentos)
    # o python gestion_medicamentos/app/database.py (si estás en la raíz del repo)
    print("Inicializando la creación de la base de datos y tablas...")
    create_db_and_tables()
