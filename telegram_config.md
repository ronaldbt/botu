# 🤖 Configuración del Bot de Telegram

## Paso 1: Crear el Bot en Telegram

1. **Abrir Telegram** y buscar `@BotFather`
2. **Iniciar conversación** con BotFather
3. **Enviar comando**: `/newbot`
4. **Elegir nombre**: `Botu Trading Alerts`
5. **Elegir username**: `botu_trading_alerts_bot`
6. **Copiar el TOKEN** que te da BotFather

## Paso 2: Configurar Variables de Entorno

Agregar estas variables al archivo `.env`:

```bash
# Configuración del Bot de Telegram
TELEGRAM_BOT_TOKEN=TU_TOKEN_AQUI
TELEGRAM_ALERTS_ENABLED=true

# Configuración de API Keys de Binance (para el usuario admin)
BINANCE_API_KEY=tu_api_key_de_binance
BINANCE_SECRET_KEY=tu_secret_key_de_binance
```

## Paso 3: Conectar Usuarios al Bot

1. **Ir a la página "Integraciones"** en el frontend
2. **Hacer clic en "Conectar Telegram"**
3. **Escanear el código QR** con la app de Telegram
4. **Enviar el comando** `/start` al bot
5. **El bot confirmará** la conexión

## Paso 4: Configurar Alertas Automáticas

El sistema enviará alertas automáticamente cuando:
- Se ejecute una **compra** (BUY)
- Se ejecute una **venta** (SELL)
- Se alcance **Take Profit** o **Stop Loss**

## Paso 5: Probar el Sistema

1. **Hacer clic en "Probar Alerta"** en la página de Integraciones
2. **Verificar** que recibes el mensaje de prueba
3. **Activar el trading automático** para que envíe alertas reales

## Características del Bot

- ✅ **Un solo bot** para todas las criptomonedas
- ✅ **Un chat por usuario** (privado)
- ✅ **Alertas agrupadas** (una por tipo de operación)
- ✅ **Rate limiting** (máximo 1 mensaje cada 0.5 segundos)
- ✅ **Reintentos automáticos** si falla el envío
- ✅ **Panel de administración** para gestionar conexiones
