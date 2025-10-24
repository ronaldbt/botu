# Configuración del Sistema de Alertas de Telegram

## Variables de Entorno Requeridas

```bash
# Token del bot de Telegram (obligatorio)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Username del bot (opcional, para enlaces)
TELEGRAM_BOT_USERNAME=tu_bot_username

# Feature flag para habilitar/deshabilitar alertas (opcional, default: false)
TELEGRAM_ALERTS_ENABLED=true
```

## Configuración del Bot de Telegram

1. **Crear un bot:**
   - Habla con [@BotFather](https://t.me/botfather) en Telegram
   - Usa el comando `/newbot`
   - Elige un nombre y username para tu bot
   - Copia el token que te proporciona

2. **Configurar el bot:**
   - Usa `/setcommands` en BotFather para configurar comandos
   - Usa `/setdescription` para añadir una descripción

## Cómo Funciona el Sistema

### 1. **Agrupación Inteligente**
- Los eventos se agrupan por símbolo y operación (últimos 2 minutos)
- Se envía **una sola alerta por grupo** a todos los usuarios conectados
- Ejemplo: 3 compras de BTC → 1 mensaje: "🟢 COMPRA BTCUSDT - Cantidad: 0.15 @ $45000 - Operaciones: 3"

### 2. **Cache de Usuarios**
- Los usuarios conectados se cachean por 5 minutos
- Reduce consultas a la base de datos
- Se actualiza automáticamente

### 3. **Rate Limiting**
- 0.5 segundos entre mensajes para no saturar Telegram
- Evita bloqueos del bot por spam

### 4. **Feature Flag**
- `TELEGRAM_ALERTS_ENABLED=true` para habilitar
- `TELEGRAM_ALERTS_ENABLED=false` para deshabilitar
- Útil para desarrollo y rollouts graduales

## Flujo de Trabajo

1. **Ejecutor** ejecuta compra/venta en Binance
2. **TradingEventPublisher** crea evento en `trading_events`
3. **AlertSender** procesa eventos cada 30 segundos
4. **Agrupa** eventos por símbolo/operación
5. **Envía** mensaje agrupado a todos los usuarios conectados
6. **Marca** eventos como procesados

## Endpoints Disponibles

### Usuario
- `GET /telegram/status-main` - Estado de conexión
- `POST /telegram/connect-main` - Generar QR de conexión
- `POST /telegram/validate-main` - Validar token QR
- `POST /telegram/disconnect-main` - Desconectar
- `POST /telegram/send-test-alert` - Enviar alerta de prueba

### Admin
- `GET /telegram/admin/connections` - Listar todas las conexiones
- `POST /telegram/admin/revoke/{connection_id}` - Revocar conexión
- `POST /telegram/admin/force-disconnect/{user_id}` - Forzar desconexión
- `GET /telegram/admin/alert-sender-status` - Estado del sistema

## Vista de Integraciones

Accede a `/integraciones` para:
- Ver estado de conexión
- Generar QR para conectar
- Enviar alerta de prueba
- Ver métricas del sistema

## Pruebas

```bash
# Ejecutar pruebas E2E
cd backend
source venv/bin/activate
python test_telegram_alerts.py
```

## Monitoreo

- **Logs:** Busca `📥`, `✅`, `❌` en los logs
- **Métricas:** Usa `/telegram/admin/alert-sender-status`
- **Estado:** Verifica en `/integraciones`

## Troubleshooting

### Bot no responde
- Verifica `TELEGRAM_BOT_TOKEN`
- Revisa logs de `AlertSender`
- Confirma que `TELEGRAM_ALERTS_ENABLED=true`

### Usuarios no reciben alertas
- Verifica conexión en `/integraciones`
- Revisa estado en `/telegram/admin/connections`
- Confirma que el bot está activo

### Eventos no se procesan
- Verifica `trading_events` en la BD
- Revisa logs de `AlertSender`
- Confirma que los ejecutores están publicando eventos
