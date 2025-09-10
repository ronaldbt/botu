-- Migración para actualizar tabla users con nuevas columnas
-- Ejecutar en la base de datos de producción

BEGIN;

-- Agregar nuevas columnas de perfil personal
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS country VARCHAR;

-- Crear índice para email si no existe
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- Migrar datos existentes de telegram a las nuevas columnas específicas por crypto
-- Primero agregar las nuevas columnas
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id_btc VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id_eth VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id_bnb VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_token_btc VARCHAR UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_token_eth VARCHAR UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_token_bnb VARCHAR UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_subscribed_btc BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_subscribed_eth BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_subscribed_bnb BOOLEAN DEFAULT FALSE;

-- Migrar datos existentes de las columnas antiguas a las nuevas (BTC por defecto)
UPDATE users 
SET telegram_chat_id_btc = telegram_chat_id,
    telegram_token_btc = telegram_token,
    telegram_subscribed_btc = telegram_subscribed
WHERE telegram_chat_id IS NOT NULL OR telegram_token IS NOT NULL OR telegram_subscribed = TRUE;

-- Crear índices para las nuevas columnas
CREATE INDEX IF NOT EXISTS ix_users_telegram_chat_id_btc ON users(telegram_chat_id_btc);
CREATE INDEX IF NOT EXISTS ix_users_telegram_chat_id_eth ON users(telegram_chat_id_eth);
CREATE INDEX IF NOT EXISTS ix_users_telegram_chat_id_bnb ON users(telegram_chat_id_bnb);
CREATE INDEX IF NOT EXISTS ix_users_telegram_token_btc ON users(telegram_token_btc);
CREATE INDEX IF NOT EXISTS ix_users_telegram_token_eth ON users(telegram_token_eth);
CREATE INDEX IF NOT EXISTS ix_users_telegram_token_bnb ON users(telegram_token_bnb);

-- Agregar columnas de suscripción y pagos
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS payment_method VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS paypal_subscription_id VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMP;

-- Actualizar valores por defecto para usuarios existentes
UPDATE users SET subscription_plan = 'free' WHERE subscription_plan IS NULL;

-- Eliminar columnas antiguas de telegram (opcional - comentado por seguridad)
-- ALTER TABLE users DROP COLUMN IF EXISTS telegram_chat_id;
-- ALTER TABLE users DROP COLUMN IF EXISTS telegram_token;
-- ALTER TABLE users DROP COLUMN IF EXISTS telegram_subscribed;

COMMIT;