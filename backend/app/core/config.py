import os
from dotenv import load_dotenv

# Carga el archivo .env
load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")  # fallback por si no está en .env

    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 día, puedes ajustar
    ALGORITHM = "HS256"

settings = Settings()
