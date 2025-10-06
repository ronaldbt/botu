# app/db/database.py

from dotenv import load_dotenv
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ✅ Cargar variables del archivo .env
load_dotenv()

# ✅ Leer la URL de conexión de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Usar SQLite como fallback si no hay DATABASE_URL
    DATABASE_URL = "sqlite:///./botu.db"
    print("⚠️  Usando SQLite como base de datos (DATABASE_URL no configurado)")

# ✅ Crear engine SQLAlchemy
engine = create_engine(DATABASE_URL)

# ✅ Configurar sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Base para los modelos ORM
Base = declarative_base()

# ✅ Dependency para obtener una sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
