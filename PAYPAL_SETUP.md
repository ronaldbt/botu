# Configuración de PayPal para BotU

## Instrucciones para configurar los pagos de suscripción

### 1. Crear cuenta PayPal Business
1. Ir a https://www.paypal.com/bizsignup
2. Crear cuenta Business
3. Verificar la cuenta con documentos de identidad

### 2. Configurar Productos de Suscripción

#### Plan Básico ($29/mes)
1. Ir a https://developer.paypal.com/ 
2. Login con tu cuenta business
3. Ir a "My Apps & Credentials"
4. Crear una App nueva para "BotU Subscriptions"
5. En la sección de Productos, crear:
   - **Nombre**: BotU Plan Básico
   - **Tipo**: Subscription
   - **Descripción**: Acceso a Bitcoin Bot con alertas Telegram
   - **Precio**: $29 USD/mes
   - **Intervalo**: Mensual

#### Plan Premium ($79/mes)
1. Crear segundo producto:
   - **Nombre**: BotU Plan Premium  
   - **Tipo**: Subscription
   - **Descripción**: Acceso completo a BTC, ETH y BNB Bots con alertas y trading automático
   - **Precio**: $79 USD/mes
   - **Intervalo**: Mensual

### 3. Obtener Plan IDs

Después de crear los productos, PayPal te dará un Plan ID para cada uno. Por ejemplo:
- Plan Básico: `P-1XX123456X1234567XXXXXXXXX`
- Plan Premium: `P-2XX789012X7890123XXXXXXXXX`

### 4. Actualizar el Frontend

Editar `/frontend/src/views/SubscriptionView.vue` línea 304-307:

```javascript
const paypalLinks = {
  basic: 'https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-TU_PLAN_ID_BASICO_REAL',
  premium: 'https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-TU_PLAN_ID_PREMIUM_REAL'
}
```

### 5. Configurar Webhook (Opcional)

Para activar automáticamente las suscripciones cuando se complete el pago:

1. En PayPal Developer, ir a "Webhooks"
2. Crear webhook con URL: `https://tu-dominio.com/users/subscription/webhook`
3. Seleccionar eventos:
   - `BILLING.SUBSCRIPTION.ACTIVATED`
   - `BILLING.SUBSCRIPTION.CANCELLED`
   - `PAYMENT.SALE.COMPLETED`

### 6. Configuración de Producción vs Sandbox

**Para Testing (Sandbox):**
```javascript
const paypalLinks = {
  basic: 'https://www.sandbox.paypal.com/webapps/billing/plans/subscribe?plan_id=P-PLAN_SANDBOX_ID',
  premium: 'https://www.sandbox.paypal.com/webapps/billing/plans/subscribe?plan_id=P-PLAN_SANDBOX_ID'
}
```

**Para Producción:**
```javascript
const paypalLinks = {
  basic: 'https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-PLAN_LIVE_ID',
  premium: 'https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-PLAN_LIVE_ID'
}
```

### 7. Proceso de Pago para el Usuario

1. Usuario hace clic en "Suscribirme"
2. Se abre modal con instrucciones
3. Usuario hace clic en "Pagar con PayPal"
4. Es redirigido a PayPal
5. Completa el pago
6. PayPal envía webhook (opcional)
7. Usuario debe contactarte para activar manualmente su cuenta

### 8. Activación Manual de Suscripciones

Mientras no tengas webhooks automáticos, los usuarios deberán:

1. Completar el pago en PayPal
2. Enviarte el comprobante por email/Telegram
3. Tú actualizas manualmente su suscripción en la base de datos:

```sql
-- Activar suscripción básica
UPDATE users 
SET 
    subscription_plan = 'basic',
    subscription_status = 'active',
    subscription_start_date = NOW(),
    subscription_end_date = NOW() + INTERVAL '1 month',
    last_payment_date = NOW(),
    paypal_subscription_id = 'I-XXXXXXXXXXXXX'
WHERE username = 'nombre_usuario';

-- Activar suscripción premium  
UPDATE users 
SET 
    subscription_plan = 'premium',
    subscription_status = 'active',
    subscription_start_date = NOW(),
    subscription_end_date = NOW() + INTERVAL '1 month',
    last_payment_date = NOW(),
    paypal_subscription_id = 'I-XXXXXXXXXXXXX'
WHERE username = 'nombre_usuario';
```

### 9. Notas Importantes

- Los links actuales en el código son placeholders
- NUNCA expongas tus Client ID/Secret en el frontend
- Usa siempre HTTPS en producción
- Considera implementar webhooks para automatización completa
- Ten un proceso claro para cancelaciones y reembolsos

### 10. Testing

Para probar los pagos:
1. Usa PayPal Sandbox primero
2. Crea cuentas de prueba de compradores
3. Verifica que los links funcionan correctamente
4. Prueba todo el flujo antes de ir a producción