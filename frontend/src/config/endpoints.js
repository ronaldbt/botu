// Endpoints de la API
export const ENDPOINTS = {
  // Auth
  LOGIN: '/token',
  
  // Users
  USERS: '/users',
  USER_PROFILE: '/users/profile',
  
  // Signals
  SIGNALS: '/signals',
  
  // Bitcoin Bot
  BITCOIN_STATUS: '/bitcoin-bot/status',
  BITCOIN_ANALYSIS: '/bitcoin-bot/analysis', 
  BITCOIN_ALERTS: '/bitcoin-bot/alerts',
  BITCOIN_STATS: '/bitcoin-bot/statistics',
  
  // Ethereum Bot
  ETHEREUM_STATUS: '/ethereum-bot/status',
  ETHEREUM_ANALYSIS: '/ethereum-bot/analysis',
  ETHEREUM_ALERTS: '/ethereum-bot/alerts', 
  ETHEREUM_STATS: '/ethereum-bot/statistics',
  
  // BNB Bot
  BNB_STATUS: '/bnb-bot/status',
  BNB_ANALYSIS: '/bnb-bot/analysis',
  BNB_ALERTS: '/bnb-bot/alerts',
  BNB_STATS: '/bnb-bot/statistics',
  
  // Telegram
  TELEGRAM_STATUS: '/telegram/status',
  
  // Estados U
  ESTADOS_U: '/estados_u',
  
  // Alertas
  ALERTAS_SUMMARY: '/alertas/trading/summary',
  ALERTAS_OPERATIONS: '/alertas/trading/operations',
  
  // Trading
  TRADING: '/trading'
}