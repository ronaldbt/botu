# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import models
from app.db.database import engine
from app.api.v1 import u_routes, auth_routes, estados_u_routes, tickers_routes, ordenes_routes, alertas_routes, users_routes, test_tools_simple

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

# Inicializar FastAPI
app = FastAPI(
    title="BotU API",
    description="API para BotU - Monitoreo de patrones U",
    version="1.0.0",
)

# Configurar CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint raíz (ping)
@app.get("/")
def read_root():
    return {"message": "BotU API running 🚀"}

# Endpoint de prueba para tickers
@app.get("/test-tickers")
def test_tickers():
    from app.db.database import SessionLocal
    from app.db import crud_tickers
    session = SessionLocal()
    try:
        tickers = crud_tickers.get_all_tickers(session)
        return {"count": len(tickers), "tickers": [t.ticker for t in tickers[:5]]}
    finally:
        session.close()

# Routers
app.include_router(u_routes.router)             # Ya tiene prefix="/signals"
app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])  # Aquí sí → no tenía prefix
app.include_router(estados_u_routes.router)     # Ya tiene prefix="/estados_u"
app.include_router(tickers_routes.router)       # Ya tiene prefix="/tickers"
app.include_router(ordenes_routes.router)       # Ya tiene prefix="/ordenes"
app.include_router(alertas_routes.router)       # Ya tiene prefix="/alertas"
app.include_router(users_routes.router)         # Ya tiene prefix="/users"
app.include_router(test_tools_simple.router)    # Ya tiene prefix="/test-tools"
