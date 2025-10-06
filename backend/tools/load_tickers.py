# tools/load_tickers.py

import csv
import os
import sys

# Añadimos el path de backend para poder importar app.*
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import crud_tickers
from app.schemas.tickers_schema import TickerCreate

# Carpeta con archivos CSV
DATA_FOLDER = "tickers_data"

def load_csv(file_path: str, session: Session):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ticker_data = TickerCreate(
                ticker=row["ticker"].strip(),
                tipo=row["tipo"].strip(),
                sub_tipo=row.get("sub_tipo", "").strip() or None,
                pais=row.get("pais", "").strip() or None,
                nombre=row.get("nombre", "").strip() or None,
                activo=row.get("activo", "TRUE").strip().lower() == "true"
            )
            crud_tickers.create_or_update_ticker(session, ticker_data)
    print(f"✔️ Cargado: {file_path}")

def main():
    session = SessionLocal()
    try:
        # Si paso archivos como argumentos → los cargo
        if len(sys.argv) > 1:
            files = sys.argv[1:]
            for file in files:
                file_path = os.path.join(DATA_FOLDER, file)
                if os.path.exists(file_path):
                    load_csv(file_path, session)
                else:
                    print(f"❌ Archivo no encontrado: {file_path}")
        else:
            # Si no paso nada → cargo todos los .csv
            for file in os.listdir(DATA_FOLDER):
                if file.endswith(".csv"):
                    load_csv(os.path.join(DATA_FOLDER, file), session)
    finally:
        session.close()

if __name__ == "__main__":
    main()
