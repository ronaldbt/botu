# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

**BotU** is a cryptocurrency trading pattern detection system with three main components:

1. **Backend API** (`backend/`) - FastAPI application for data management and API endpoints
2. **Frontend Web UI** (`frontend/`) - Vue 3 + Tailwind CSS interface for monitoring and management
3. **Trading Scripts** (`src/`) - Standalone Python modules for pattern scanning and Binance integration

## Development Commands

### Backend (FastAPI)
```bash
cd backend
source venv/bin/activate  # or `venv/bin/activate` on Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Vue 3 + Vite)
```bash
cd frontend
npm install
npm run dev     # Development server on port 5173
npm run build   # Production build
npm run preview # Preview production build
```

### Trading Scripts
```bash
# Activate virtual environment in root
source venv/bin/activate
pip install -r requirements.txt
cd src
python main.py  # Main trading scanner
python binance_backtest.py  # Backtesting
```

## Code Architecture

### Backend Structure
- **FastAPI app** in `backend/app/main.py` with CORS configured for localhost:5173
- **Database models** in `app/db/models.py` using SQLAlchemy ORM
- **CRUD operations** in `app/db/crud_*.py` files
- **API routes** organized in `app/api/v1/` by feature:
  - `u_routes.py` - U-pattern signals
  - `tickers_routes.py` - Ticker management
  - `auth_routes.py` - Authentication
  - `users_routes.py` - User management
  - `ordenes_routes.py` - Order management
  - `alertas_routes.py` - Alert management
  - `test_tools_simple.py` - Testing endpoints
- **Schemas** in `app/schemas/` for request/response validation

### Frontend Structure
- **Vue 3** with Composition API and `<script setup>` syntax
- **Pinia** for state management
- **Vue Router** configured in `src/router/index.js`
- **Tailwind CSS 4.x** for styling with Vite plugin
- **Axios** for API communication
- **Main views** in `src/views/`:
  - `DashboardView.vue` - Main dashboard
  - `TickersView.vue` - Ticker management
  - `AlertasView.vue` - Alert management
  - `OrdenesView.vue` - Order management
  - `TestToolsView.vue` - Testing interface
  - `LoginView.vue` - Authentication

### Trading Scripts Structure
- **Main scanner** (`main.py`) - Entry point for U-pattern detection
- **Binance integration**:
  - `binance_client.py` - API client wrapper
  - `binance_scanner.py` - Live market scanning
  - `binance_trader.py` - Trading execution
  - `binance_ws.py` - WebSocket connections
  - `binance_backtest.py` - Historical backtesting
- **Pattern detection** (`scanner.py`) - Core U-pattern algorithm
- **Utilities**:
  - `estado_u_utils.py` - State management for scanning
  - `telegram.py` - Telegram notifications
  - `utils.py` - General utilities

## Database Configuration

PostgreSQL database configured via environment variables:
- Uses SQLAlchemy with automatic table creation on startup
- Models include: Signal, User, UserLogin, Ticker, EstadoU, Orden, Alerta
- Connection configured in `backend/app/db/database.py`

## Environment Setup

### Backend Environment Variables
Create `backend/.env`:
```
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key
```

### Root Environment Variables  
Create `.env` in root:
```
BINANCE_API_KEY=your-api-key
BINANCE_SECRET_KEY=your-secret-key
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

## Type Checking

Python type checking configured with:
- **basedpyright** - Main type checker (config in `.basedpyright.json` and `pyproject.toml`)
- **pyright** - Fallback type checker
- Multiple execution environments for `backend/` and `src/` directories
- Python 3.12 target with proper path configuration

## Key Integration Points

- Frontend connects to backend API at `localhost:8000`
- Trading scripts can access backend database via shared SQLAlchemy models
- U-pattern signals stored in database and displayed in frontend dashboard
- Binance WebSocket data feeds live market updates
- Telegram integration for trade notifications

## Development Notes

- Frontend uses Vue 3 composition API consistently
- Backend follows FastAPI best practices with dependency injection
- Trading scripts are designed for standalone execution but share database models
- All Python code is type-annotated for better IDE support