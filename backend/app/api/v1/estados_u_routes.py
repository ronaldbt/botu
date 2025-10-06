# app/api/v1/estados_u_routes.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud_estados_u
from app.schemas.estados_u_schema import EstadoUSchema, EstadoUCreate, EstadoUWithTickerSchema

router = APIRouter(prefix="/estados_u", tags=["estados_u"])

# Listar todos los estados_u con JOIN con tickers + filtros
@router.get("/", response_model=dict[str, list[EstadoUWithTickerSchema]])
def read_estados_u(
    tipo: str = Query(None),
    sub_tipo: str = Query(None),
    pais: str = Query(None),
    estado_actual: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1),
    db: Session = Depends(get_db)
):
    estados = crud_estados_u.get_all_estados_with_tickers(
        db=db,
        tipo=tipo,
        sub_tipo=sub_tipo,
        pais=pais,
        estado_actual=estado_actual,
        skip=skip,
        limit=limit
    )
    return {"estados": estados}

# Obtener un estado_u por ticker
@router.get("/{ticker}", response_model=EstadoUSchema)
def read_estado_u(ticker: str, db: Session = Depends(get_db)):
    estado = crud_estados_u.get_estado_u(db, ticker)
    if not estado:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    return estado

# Crear o actualizar un estado_u
@router.post("/", response_model=EstadoUSchema)
def create_or_update_estado_u(estado_data: EstadoUCreate, db: Session = Depends(get_db)):
    return crud_estados_u.upsert_estado_u(db, estado_data)

# Eliminar un estado_u
@router.delete("/{ticker}")
def delete_estado_u(ticker: str, db: Session = Depends(get_db)):
    crud_estados_u.delete_estado_u(db, ticker)
    return {"ok": True}
