# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import models
from app.db.database import engine
from app.api.v1 import u_routes, auth_routes, ordenes_routes, alertas_routes, users_routes, bitcoin_bot_routes, telegram_routes, eth_bot_routes, bnb_bot_routes, profile_routes

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

# Routers
app.include_router(u_routes.router)             # Ya tiene prefix="/signals"
app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(ordenes_routes.router)       # Ya tiene prefix="/ordenes"
app.include_router(alertas_routes.router)       # Ya tiene prefix="/alertas"
app.include_router(users_routes.router)         # Ya tiene prefix="/users"
app.include_router(bitcoin_bot_routes.router, tags=["bitcoin-bot"])  # Bitcoin Bot endpoints
app.include_router(eth_bot_routes.router, tags=["eth-bot"])      # Ethereum Bot endpoints
app.include_router(bnb_bot_routes.router, tags=["bnb-bot"])      # BNB Bot endpoints
app.include_router(profile_routes.router, tags=["profile"])      # Profile and subscription endpoints
app.include_router(telegram_routes.router)      # Ya tiene prefix="/telegram"
