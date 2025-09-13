<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div>
            <h1 class="text-3xl md:text-4xl font-bold text-slate-900 mb-2 flex items-center">
              <span class="text-4xl mr-3 text-yellow-600">₿</span>
              Bitcoin Bot U-Pattern
            </h1>
            <p class="text-slate-600 text-base">Sistema avanzado de detección de patrones U para Bitcoin con backtesting probado</p>
            <div class="mt-2 flex items-center space-x-4 text-sm">
              <span class="bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full font-semibold">2022: +28% vs BTC -65%</span>
              <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-semibold">2024: +6,530% vs BTC +123%</span>
            </div>
          </div>
          
          <!-- Status Indicator -->
          <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
            <div class="text-center">
              <div class="flex items-center justify-center mb-2">
                <div :class="botStatus.isRunning ? 'bg-emerald-400' : 'bg-slate-400'" class="w-3 h-3 rounded-full mr-2"></div>
                <span class="font-semibold text-slate-700">
                  {{ getStatusText() }}
                </span>
              </div>
              <div class="text-xs text-slate-500">{{ botStatus.lastCheck || 'Nunca' }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Mode Selector -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
        <h2 class="text-xl font-semibold text-slate-900 mb-4">Seleccionar Modo de Operación</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Manual Mode -->
          <div class="relative">
            <input type="radio" id="manual" v-model="selectedMode" value="manual" class="sr-only">
            <label for="manual" :class="[
              'block p-6 border-2 rounded-lg cursor-pointer transition-all duration-200',
              selectedMode === 'manual' 
                ? 'border-blue-500 bg-blue-50 shadow-md' 
                : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
            ]">
              <div class="flex items-center mb-3">
                <div class="text-2xl mr-3">👁️</div>
                <div>
                  <div class="font-semibold text-slate-900">Modo Manual</div>
                  <div class="text-sm text-slate-600">Solo alertas - Trading manual</div>
                </div>
              </div>
              <ul class="text-sm text-slate-600 space-y-1">
                <li>• API pública de Binance</li>
                <li>• Solo notificaciones de compra/venta</li>
                <li>• Tú ejecutas las órdenes manualmente</li>
                <li>• Sin riesgo - Solo análisis</li>
              </ul>
            </label>
          </div>

          <!-- Automatic Mode -->
          <div class="relative">
            <input type="radio" id="automatic" v-model="selectedMode" value="automatic" class="sr-only">
            <label for="automatic" :class="[
              'block p-6 border-2 rounded-lg cursor-pointer transition-all duration-200',
              selectedMode === 'automatic' 
                ? 'border-emerald-500 bg-emerald-50 shadow-md' 
                : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
            ]">
              <div class="flex items-center mb-3">
                <div class="text-2xl mr-3">🤖</div>
                <div>
                  <div class="font-semibold text-slate-900">Modo Automático</div>
                  <div class="text-sm text-slate-600">Trading automático - Testnet</div>
                </div>
              </div>
              <ul class="text-sm text-slate-600 space-y-1">
                <li>• Binance Testnet (dinero virtual)</li>
                <li>• Ejecuta trades automáticamente</li>
                <li>• Stop loss y take profit</li>
                <li>• Aprendizaje sin riesgo real</li>
              </ul>
            </label>
          </div>
        </div>
      </div>

      <!-- Configuration Panel -->
      <div v-if="selectedMode" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
        <h3 class="text-lg font-semibold text-slate-900 mb-4">
          ₿ Estrategia BTC Optimizada - Modo {{ selectedMode === 'manual' ? 'Manual' : 'Automático' }}
        </h3>
        
        <div class="bg-gradient-to-r from-orange-50 to-yellow-50 border border-orange-200 rounded-lg p-4 mb-4">
          <div class="flex items-center mb-2">
            <span class="text-lg mr-2">⚙️</span>
            <h4 class="font-semibold text-slate-800">Parámetros Optimizados por Backtest 2023</h4>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-600">
            <div class="flex items-center">
              <span class="text-orange-600 font-medium mr-2">Timeframe:</span>
              <span>4 Horas (Optimizado)</span>
            </div>
            <div class="flex items-center">
              <span class="text-green-600 font-medium mr-2">Take Profit:</span>
              <span>8% (Conservador)</span>
            </div>
            <div class="flex items-center">
              <span class="text-red-600 font-medium mr-2">Stop Loss:</span>
              <span>3% (Seguro)</span>
            </div>
          </div>
          <p class="text-xs text-slate-500 mt-2">
            ✨ Los parámetros están preconfigurados según backtests históricos exitosos. Incluye detección de 4 mínimos para más oportunidades.
          </p>
        </div>

        <!-- Additional config for automatic mode -->
        <div v-if="selectedMode === 'automatic'" class="mt-6 pt-6 border-t border-gray-200">
          <!-- Trading Configuration -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">Cantidad por Trade (USDT)</label>
              <input 
                type="number" 
                v-model="config.tradeAmount" 
                min="10" 
                max="1000" 
                step="10"
                class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">Max Trades Concurrentes</label>
              <select 
                v-model="config.maxConcurrentTrades" 
                class="w-full appearance-none bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="1">1 Trade</option>
                <option value="2">2 Trades</option>
                <option value="3">3 Trades</option>
              </select>
            </div>
          </div>

          <!-- Binance API Configuration -->
          <div class="bg-slate-50 border border-slate-200 rounded-lg p-6">
            <div class="flex items-center mb-4">
              <div class="text-2xl mr-3">🔐</div>
              <div>
                <h4 class="font-semibold text-slate-900">Configuración de Binance API</h4>
                <p class="text-sm text-slate-600">Configura tus credenciales para trading automático</p>
              </div>
            </div>

            <!-- Environment Selection -->
            <div class="mb-6">
              <label class="block text-sm font-medium text-slate-700 mb-3">Entorno de Trading</label>
              <div class="flex space-x-4">
                <label class="flex items-center">
                  <input type="radio" v-model="config.environment" value="testnet" class="mr-2">
                  <span class="text-sm">
                    <span class="font-semibold text-emerald-700">Testnet</span> 
                    <span class="text-slate-600">(Dinero virtual - Recomendado para aprender)</span>
                  </span>
                </label>
                <label class="flex items-center">
                  <input type="radio" v-model="config.environment" value="mainnet" class="mr-2">
                  <span class="text-sm">
                    <span class="font-semibold text-red-700">Mainnet</span> 
                    <span class="text-slate-600">(Dinero real - Solo expertos)</span>
                  </span>
                </label>
              </div>
            </div>

            <!-- API Keys Configuration -->
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">
                  API Key {{ config.environment === 'testnet' ? '(Testnet)' : '(Mainnet)' }}
                </label>
                <input 
                  type="password" 
                  v-model="config.apiKey" 
                  placeholder="Ingresa tu API Key de Binance"
                  class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
              </div>

              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">
                  Secret Key {{ config.environment === 'testnet' ? '(Testnet)' : '(Mainnet)' }}
                </label>
                <input 
                  type="password" 
                  v-model="config.secretKey" 
                  placeholder="Ingresa tu Secret Key de Binance"
                  class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
              </div>
            </div>

            <!-- API Status -->
            <div v-if="apiStatus" class="mt-4 p-3 rounded-lg" :class="apiStatus.connected ? 'bg-emerald-100' : 'bg-red-100'">
              <div class="flex items-center">
                <div class="text-lg mr-2">{{ apiStatus.connected ? '✅' : '❌' }}</div>
                <div>
                  <div class="font-semibold" :class="apiStatus.connected ? 'text-emerald-800' : 'text-red-800'">
                    {{ apiStatus.connected ? 'Conexión exitosa' : 'Error de conexión' }}
                  </div>
                  <div class="text-sm text-slate-600">{{ apiStatus.message }}</div>
                </div>
              </div>
            </div>

            <!-- Test Connection Button -->
            <div class="mt-4">
              <button
                @click="testApiConnection"
                :disabled="!config.apiKey || !config.secretKey || testingConnection"
                class="px-4 py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-lg text-sm font-medium transition-colors duration-200 disabled:bg-slate-400"
              >
                <span v-if="!testingConnection">Probar Conexión</span>
                <span v-else class="flex items-center">
                  <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Probando...
                </span>
              </button>
            </div>

            <!-- Help Links -->
            <div class="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h5 class="font-semibold text-blue-900 mb-2">¿Cómo obtener las API Keys?</h5>
              <div class="text-sm text-blue-800 space-y-1">
                <div><strong>Para Testnet (Recomendado):</strong></div>
                <div>• Ve a <a href="https://testnet.binance.vision/" target="_blank" class="text-blue-600 hover:underline">testnet.binance.vision</a></div>
                <div>• Crea una cuenta de testnet gratuita</div>
                <div>• Ve a API Management y crea nuevas API Keys</div>
                <div>• Habilita "Enable Spot & Margin Trading"</div>
                <br>
                <div><strong>Para Mainnet (Solo expertos):</strong></div>
                <div>• Ve a <a href="https://www.binance.com/en/my/settings/api-management" target="_blank" class="text-red-600 hover:underline">Binance API Management</a></div>
                <div>• Crea API Keys con permisos de Spot Trading</div>
                <div class="text-red-700 font-semibold">⚠️ NUNCA compartas tus API Keys reales</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Telegram Integration (Manual Mode Only) -->
        <div v-if="selectedMode === 'manual'" class="mt-6 pt-6 border-t border-slate-200">
          <div class="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
            <div class="flex items-center mb-4">
              <div class="text-2xl mr-3">📱</div>
              <div>
                <h4 class="font-semibold text-slate-900">Conexión con Telegram</h4>
                <p class="text-sm text-slate-600">Recibe alertas directamente en Telegram</p>
              </div>
            </div>

            <!-- Estado de Conexión -->
            <div v-if="telegramStatus" class="mb-4">
              <div class="flex items-center p-3 rounded-lg" :class="telegramStatus.connected ? 'bg-emerald-100' : 'bg-slate-100'">
                <div class="text-lg mr-2">{{ telegramStatus.connected ? '✅' : '📱' }}</div>
                <div>
                  <div class="font-semibold" :class="telegramStatus.connected ? 'text-emerald-800' : 'text-slate-700'">
                    {{ telegramStatus.connected ? 'Conectado a Telegram' : 'No conectado' }}
                  </div>
                  <div class="text-sm text-slate-600" v-if="telegramStatus.connected">
                    Estado: {{ telegramStatus.subscription_status }} - Las alertas se enviarán automáticamente
                  </div>
                  <div class="text-sm text-slate-600" v-else>
                    Escanea el código QR para recibir alertas en Telegram
                  </div>
                </div>
              </div>
            </div>

            <!-- Botones de Control -->
            <div class="flex items-center space-x-3">
              <button
                v-if="!telegramStatus?.connected"
                @click="generateTelegramConnection"
                :disabled="generatingQR || !telegramStatus?.bot_configured"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors duration-200 disabled:bg-slate-400"
              >
                <span v-if="!generatingQR">Conectar Telegram</span>
                <span v-else class="flex items-center">
                  <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generando...
                </span>
              </button>

              <button
                v-if="telegramStatus?.connected"
                @click="disconnectTelegram"
                class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
              >
                Desconectar
              </button>

              <button
                @click="sendTestAlert"
                :disabled="!telegramStatus?.connected"
                class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors duration-200 disabled:bg-slate-400"
              >
                Enviar Prueba
              </button>
            </div>

            <!-- Warning si el bot no está configurado -->
            <div v-if="!telegramStatus?.bot_configured" class="mt-4 p-3 bg-yellow-100 border border-yellow-200 rounded-lg">
              <div class="flex items-center">
                <div class="text-lg mr-2">⚠️</div>
                <div class="text-sm text-yellow-800">
                  El bot de Telegram no está configurado en el servidor. Contacta al administrador.
                </div>
              </div>
            </div>
          </div>

          <!-- QR Code Modal -->
          <div v-if="showQRModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div class="bg-white rounded-lg w-full max-w-md max-h-screen overflow-y-auto">
              <!-- Header fijo -->
              <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 rounded-t-lg">
                <div class="flex items-center justify-between">
                  <h3 class="text-lg font-semibold text-slate-900">Conectar con Telegram</h3>
                  <button
                    @click="closeQRModal"
                    class="text-slate-400 hover:text-slate-600 transition-colors duration-200"
                  >
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                  </button>
                </div>
              </div>

              <!-- Contenido scrolleable -->
              <div class="px-6 py-4 space-y-4">
                <div v-if="qrConnection" class="text-center">
                  <!-- QR Code -->
                  <div class="bg-white p-4 rounded-lg border-2 border-slate-200 mb-4">
                    <img 
                      :src="`data:image/png;base64,${qrConnection.qr_code_base64}`" 
                      alt="QR Code Telegram"
                      class="mx-auto max-w-full h-auto"
                    />
                  </div>
                  
                  <!-- Token Manual -->
                  <div class="bg-slate-50 p-4 rounded-lg mb-4">
                    <p class="text-sm text-slate-600 mb-2">O copia este link:</p>
                    <div class="text-xs break-all font-mono text-slate-700 bg-white p-2 rounded border">
                      {{ qrConnection.telegram_link }}
                    </div>
                  </div>

                  <!-- Instrucciones -->
                  <div class="text-left space-y-2 text-sm text-slate-600 mb-4">
                    <p><strong>Instrucciones:</strong></p>
                    <p>1. Abre Telegram en tu teléfono</p>
                    <p>2. Escanea el código QR o haz clic en "Abrir en Telegram"</p>
                    <p>3. El bot te conectará automáticamente</p>
                    <p>4. ¡Listo! Recibirás las alertas de Bitcoin</p>
                  </div>

                  <!-- Enlace directo -->
                  <div class="mb-4">
                    <a 
                      :href="qrConnection.telegram_link" 
                      target="_blank"
                      class="inline-flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                    >
                      <span class="mr-2">📱</span>
                      Abrir en Telegram
                    </a>
                  </div>

                  <!-- Tiempo de expiración con contador -->
                  <div class="text-xs text-slate-500 mb-4">
                    <div v-if="tokenTimeLeft > 0" class="flex items-center justify-center space-x-2">
                      <div class="w-2 h-2 bg-orange-400 rounded-full animate-pulse"></div>
                      <span class="font-mono">Expira en: {{ formatTimeLeft(tokenTimeLeft) }}</span>
                    </div>
                    <div v-else class="text-red-500 font-semibold">
                      ⚠️ Token expirado - Genera uno nuevo
                    </div>
                  </div>

                  <!-- Botón Regenerar Token -->
                  <div class="mb-4">
                    <button
                      @click="regenerateToken"
                      :disabled="regeneratingToken"
                      class="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-medium transition-colors duration-200 disabled:bg-slate-400"
                    >
                      <span v-if="!regeneratingToken">🔄 Generar Nuevo Token</span>
                      <span v-else class="flex items-center">
                        <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Generando...
                      </span>
                    </button>
                  </div>
                </div>
              </div>

              <!-- Footer fijo -->
              <div class="sticky bottom-0 bg-white border-t border-slate-200 px-6 py-4 rounded-b-lg">
                <div class="text-center">
                  <button
                    @click="closeQRModal"
                    class="px-6 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors duration-200"
                  >
                    Cerrar
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Control Buttons - Solo Admin -->
        <div v-if="authStore.isAdmin" class="mt-6">
          <!-- Admin Info -->
          <div class="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
            <div class="flex items-center">
              <div class="text-amber-800 text-lg mr-2">👑</div>
              <div>
                <h4 class="font-semibold text-amber-800">Controles de Administrador</h4>
                <p class="text-sm text-amber-700">Solo tú puedes iniciar/detener el Bitcoin Bot automático</p>
              </div>
            </div>
          </div>

          <div class="flex items-center space-x-4">
            <button
              @click="startBot"
              :disabled="loading || botStatus.isRunning"
              :class="[
                'px-6 py-3 rounded-lg font-medium transition-colors duration-200',
                selectedMode === 'manual' 
                  ? 'bg-blue-600 hover:bg-blue-700 text-white disabled:bg-slate-400' 
                  : 'bg-emerald-600 hover:bg-emerald-700 text-white disabled:bg-slate-400'
              ]"
            >
              <span v-if="!loading">{{ botStatus.isRunning ? '🤖 Bot Activo - Scanner 4h' : '🚀 Iniciar Bitcoin Bot' }}</span>
              <span v-else class="flex items-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Iniciando Scanner...
              </span>
            </button>

            <button
              @click="stopBot"
              :disabled="loading || !botStatus.isRunning"
              class="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors duration-200 disabled:bg-slate-400"
            >
              ⏹️ Detener Bot
            </button>

            <button
              @click="refreshStatus"
              :disabled="loading"
              class="px-6 py-3 bg-slate-600 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors duration-200 disabled:bg-slate-400"
            >
              🔄 Actualizar
            </button>
          </div>
        </div>

        <!-- Info para usuarios no admin -->
        <div v-else class="mt-6">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
            <div class="text-4xl mb-3">👤</div>
            <h3 class="text-lg font-semibold text-blue-900 mb-2">Usuario Cliente</h3>
            <p class="text-blue-700 mb-4">
              El Bitcoin Bot está controlado por el administrador. Tú recibirás las alertas automáticamente en Telegram cuando se detecten patrones U.
            </p>
            <div class="text-sm text-blue-600">
              <div><strong>Estado del Bot:</strong> {{ botStatus.isRunning ? '🟢 Activo - Escaneando cada 4h' : '⭕ Inactivo' }}</div>
              <div v-if="botStatus.alerts_count"><strong>Alertas enviadas:</strong> {{ botStatus.alerts_count }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Current Analysis -->
      <div v-if="currentAnalysis" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
        <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <span class="text-2xl mr-2">📊</span>
          Análisis Actual de Bitcoin
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-600 mb-1">Precio Actual</div>
            <div class="text-2xl font-bold text-gray-900">${{ currentAnalysis.currentPrice?.toLocaleString() }}</div>
          </div>
          
          <div class="bg-blue-50 rounded-lg p-4">
            <div class="text-sm text-blue-600 mb-1">Nivel de Ruptura</div>
            <div class="text-2xl font-bold text-blue-900">
              {{ currentAnalysis.ruptureLevel ? `$${currentAnalysis.ruptureLevel.toLocaleString()}` : '-' }}
            </div>
          </div>
          
          <div class="bg-orange-50 rounded-lg p-4">
            <div class="text-sm text-orange-600 mb-1">Estado Patrón</div>
            <div class="text-lg font-bold" :class="getPatternStateClass(currentAnalysis.state)">
              {{ currentAnalysis.state || 'ANALIZANDO' }}
            </div>
          </div>
          
          <div class="bg-green-50 rounded-lg p-4">
            <div class="text-sm text-green-600 mb-1">Confianza</div>
            <div class="text-2xl font-bold text-green-900">
              {{ currentAnalysis.confidence ? `${currentAnalysis.confidence}%` : '-' }}
            </div>
          </div>
        </div>

        <!-- Pattern Details -->
        <div v-if="currentAnalysis.details" class="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 class="font-semibold text-gray-900 mb-2">Detalles del Análisis</h4>
          <div class="text-sm text-gray-700 space-y-1">
            <div><strong>Timeframe:</strong> {{ config.timeframe }}</div>
            <div><strong>Slope Left:</strong> {{ currentAnalysis.details.slopeLeft?.toFixed(3) || '-' }}</div>
            <div><strong>Pattern Width:</strong> {{ currentAnalysis.details.patternWidth || '-' }} períodos</div>
            <div><strong>Última actualización:</strong> {{ new Date(currentAnalysis.lastUpdate).toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- Alerts/Signals -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-gray-900 flex items-center">
            <span class="text-2xl mr-2">🚨</span>
            {{ selectedMode === 'manual' ? 'Alertas Recientes' : 'Trades Automáticos' }}
          </h3>
          <button
            @click="clearAlerts"
            class="text-gray-500 hover:text-gray-700 text-sm"
          >
            Limpiar
          </button>
        </div>

        <div v-if="alerts.length > 0" class="space-y-4">
          <div 
            v-for="alert in alerts.slice(0, 10)" 
            :key="alert.id"
            :class="[
              'p-4 rounded-lg border-l-4',
              getAlertClass(alert.type)
            ]"
          >
            <div class="flex justify-between items-start">
              <div>
                <div class="font-semibold" :class="getAlertTextClass(alert.type)">
                  {{ alert.title }}
                </div>
                <div class="text-sm text-gray-600 mt-1">{{ alert.message }}</div>
                <div class="text-sm text-gray-600 mt-2">
                  <span class="font-medium">Precio:</span> ${{ alert.price?.toLocaleString() }}
                  <span v-if="selectedMode === 'automatic' && alert.quantity" class="ml-4">
                    <span class="font-medium">Cantidad:</span> {{ alert.quantity }} BTC
                  </span>
                </div>
              </div>
              <div class="text-xs text-gray-500">
                {{ new Date(alert.timestamp).toLocaleTimeString() }}
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-12">
          <div class="text-6xl mb-4">📭</div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">Sin alertas</h3>
          <p class="text-gray-600">
            {{ selectedMode === 'manual' 
              ? 'Las alertas de compra/venta aparecerán aquí' 
              : 'Los trades automáticos se mostrarán aquí' 
            }}
          </p>
        </div>
      </div>

      <!-- Statistics -->
      <div v-if="statistics" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-6 flex items-center">
          <span class="text-2xl mr-2">📈</span>
          Estadísticas de Sesión
        </h3>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div class="text-center">
            <div class="text-3xl font-bold text-blue-600">{{ statistics.totalAlerts || 0 }}</div>
            <div class="text-sm text-gray-600">Total Alertas</div>
          </div>
          
          <div class="text-center">
            <div class="text-3xl font-bold text-green-600">{{ statistics.buySignals || 0 }}</div>
            <div class="text-sm text-gray-600">Señales Compra</div>
          </div>
          
          <div class="text-center">
            <div class="text-3xl font-bold text-red-600">{{ statistics.sellSignals || 0 }}</div>
            <div class="text-sm text-gray-600">Señales Venta</div>
          </div>
          
          <div class="text-center">
            <div class="text-3xl font-bold text-orange-600">{{ statistics.accuracy || 0 }}%</div>
            <div class="text-sm text-gray-600">Precisión</div>
          </div>
        </div>

        <div v-if="selectedMode === 'automatic' && statistics.portfolio" class="mt-6 pt-6 border-t border-gray-200">
          <h4 class="font-semibold text-gray-900 mb-4">Portfolio Testnet</h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="bg-gray-50 rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-gray-900">${{ statistics.portfolio.balance?.toLocaleString() || 0 }}</div>
              <div class="text-sm text-gray-600">Balance USDT</div>
            </div>
            
            <div class="bg-orange-50 rounded-lg p-4 text-center">
              <div class="text-2xl font-bold text-orange-900">{{ statistics.portfolio.btc?.toFixed(6) || 0 }}</div>
              <div class="text-sm text-orange-600">Bitcoin</div>
            </div>
            
            <div class="bg-green-50 rounded-lg p-4 text-center">
              <div class="text-2xl font-bold" :class="(statistics.portfolio.pnl || 0) >= 0 ? 'text-green-900' : 'text-red-900'">
                {{ (statistics.portfolio.pnl || 0) >= 0 ? '+' : '' }}${{ (statistics.portfolio.pnl || 0).toLocaleString() }}
              </div>
              <div class="text-sm text-gray-600">P&L Total</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Scanner Logs Panel -->
      <div v-if="botStatus.isRunning" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-gray-900 flex items-center">
            <span class="text-2xl mr-2">📊</span>
            Scanner Logs - Tiempo Real
          </h3>
          <div class="flex items-center space-x-2 text-sm text-gray-600">
            <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span>Activo</span>
          </div>
        </div>

        <div class="bg-gray-900 rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto" ref="logsContainer">
          <div v-if="scannerLogs.length === 0" class="text-gray-400 text-center py-8">
            Esperando logs del scanner...
          </div>
          <div v-else>
            <div 
              v-for="(log, index) in scannerLogs" 
              :key="index"
              :class="[
                'mb-2 p-2 rounded border-l-4',
                getLogClass(log.level)
              ]"
            >
              <div class="flex items-start space-x-3">
                <span class="text-gray-400 text-xs">{{ formatLogTime(log.timestamp) }}</span>
                <span :class="getLogTextClass(log.level)">{{ getLogIcon(log.level) }}</span>
                <div class="flex-1">
                  <div :class="getLogTextClass(log.level)">{{ log.message }}</div>
                  <div v-if="log.details && Object.keys(log.details).length > 0" class="mt-1 text-xs text-gray-300">
                    <div v-for="(value, key) in log.details" :key="key" class="inline-block mr-4">
                      <span class="text-gray-400">{{ key }}:</span> <span class="text-gray-200">{{ value }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-4 flex justify-between items-center text-sm text-gray-600">
          <div>
            <span v-if="botStatus.alerts_count">Alertas enviadas: <strong>{{ botStatus.alerts_count }}</strong></span>
            <span v-if="cooldownRemaining && cooldownRemaining > 0" class="ml-4">
              Próxima alerta en: <strong>{{ Math.ceil(cooldownRemaining/60) }} min</strong>
            </span>
          </div>
          <button 
            @click="refreshLogs" 
            class="text-blue-600 hover:text-blue-800 transition-colors duration-200"
          >
            🔄 Actualizar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import apiClient from '@/config/api'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()

// Template refs
const logsContainer = ref(null)

// Reactive data
const selectedMode = ref('manual')
const loading = ref(false)
const currentAnalysis = ref(null)
const alerts = ref([])
const statistics = ref(null)

// Scanner logs
const scannerLogs = ref([])
const cooldownRemaining = ref(0)

// Telegram state
const telegramStatus = ref(null)
const showQRModal = ref(false)
const qrConnection = ref(null)
const generatingQR = ref(false)
const regeneratingToken = ref(false)
const tokenTimeLeft = ref(0)

const botStatus = reactive({
  isRunning: false,
  lastCheck: null,
  mode: null
})

const config = reactive({
  timeframe: '4h',
  takeProfit: 12.0,
  stopLoss: 5.0,
  tradeAmount: 50,
  maxConcurrentTrades: 1,
  environment: 'testnet',
  apiKey: '',
  secretKey: ''
})

const apiStatus = ref(null)
const testingConnection = ref(false)

// Polling interval
let statusInterval = null

// Methods
const startBot = async () => {
  loading.value = true
  try {
    const response = await apiClient.post('/bitcoin-bot/start', {
      mode: selectedMode.value,
      config: config
    }, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    botStatus.isRunning = true
    botStatus.mode = selectedMode.value
    botStatus.lastCheck = new Date().toLocaleString()
    
    startPolling()
    
    console.log('Bitcoin Bot iniciado:', response.data)
  } catch (error) {
    console.error('Error iniciando Bitcoin Bot:', error)
    // Show error notification
  } finally {
    loading.value = false
  }
}

const stopBot = async () => {
  loading.value = true
  try {
    await apiClient.post('/bitcoin-bot/stop', {}, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    botStatus.isRunning = false
    botStatus.mode = null
    stopPolling()
    
  } catch (error) {
    console.error('Error deteniendo Bitcoin Bot:', error)
  } finally {
    loading.value = false
  }
}

const refreshStatus = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchStatus(),
      fetchCurrentAnalysis(),
      fetchAlerts(),
      fetchStatistics()
    ])
  } catch (error) {
    console.error('Error actualizando estado:', error)
  } finally {
    loading.value = false
  }
}

const fetchStatus = async () => {
  try {
    const response = await apiClient.get('/bitcoin-bot/status', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    Object.assign(botStatus, response.data)
  } catch (error) {
    console.error('Error obteniendo estado:', error)
  }
}

const fetchCurrentAnalysis = async () => {
  try {
    const response = await apiClient.get('/bitcoin-bot/analysis', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    currentAnalysis.value = response.data
  } catch (error) {
    console.error('Error obteniendo análisis:', error)
  }
}

const fetchAlerts = async () => {
  try {
    const response = await apiClient.get('/bitcoin-bot/alerts', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    alerts.value = response.data
  } catch (error) {
    console.error('Error obteniendo alertas:', error)
  }
}

const fetchStatistics = async () => {
  try {
    const response = await apiClient.get('/bitcoin-bot/statistics', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    statistics.value = response.data
  } catch (error) {
    console.error('Error obteniendo estadísticas:', error)
  }
}

const clearAlerts = () => {
  alerts.value = []
}

const startPolling = () => {
  if (statusInterval) clearInterval(statusInterval)
  
  statusInterval = setInterval(async () => {
    if (botStatus.isRunning) {
      await Promise.all([
        fetchCurrentAnalysis(),
        fetchAlerts(),
        fetchStatistics(),
        refreshLogs()
      ])
    }
  }, 30000) // Cada 30 segundos
}

const stopPolling = () => {
  if (statusInterval) {
    clearInterval(statusInterval)
    statusInterval = null
  }
}

const testApiConnection = async () => {
  testingConnection.value = true
  apiStatus.value = null
  
  try {
    const response = await apiClient.post('/bitcoin-bot/test-api', {
      apiKey: config.apiKey,
      secretKey: config.secretKey,
      environment: config.environment
    }, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.data.success) {
      apiStatus.value = {
        connected: true,
        message: `Conectado exitosamente al ${config.environment === 'testnet' ? 'Testnet' : 'Mainnet'} de Binance. ${response.data.accountInfo || ''}`
      }
    } else {
      apiStatus.value = {
        connected: false,
        message: response.data.error || 'Error de conexión desconocido'
      }
    }
  } catch (error) {
    console.error('Error probando API:', error)
    apiStatus.value = {
      connected: false,
      message: `Error: ${error.response?.data?.detail || error.message || 'No se pudo conectar al servidor'}`
    }
  } finally {
    testingConnection.value = false
  }
}

const getStatusText = () => {
  if (!botStatus.isRunning) return 'INACTIVO'
  if (botStatus.mode === 'manual') return 'ACTIVO MANUAL'
  if (botStatus.mode === 'automatic') return 'ACTIVO AUTOMÁTICO'
  return 'ACTIVO'
}

// Helper methods
const getPatternStateClass = (state) => {
  switch (state) {
    case 'RUPTURA': return 'text-green-900'
    case 'U_DETECTADO': return 'text-blue-900'
    case 'PALO_BAJANDO': return 'text-yellow-900'
    case 'POST_RUPTURA': return 'text-purple-900'
    default: return 'text-gray-900'
  }
}

const getAlertClass = (type) => {
  switch (type) {
    case 'BUY': return 'bg-green-50 border-green-400'
    case 'SELL': return 'bg-red-50 border-red-400'
    case 'INFO': return 'bg-blue-50 border-blue-400'
    case 'WARNING': return 'bg-yellow-50 border-yellow-400'
    default: return 'bg-gray-50 border-gray-400'
  }
}

const getAlertTextClass = (type) => {
  switch (type) {
    case 'BUY': return 'text-green-800'
    case 'SELL': return 'text-red-800'
    case 'INFO': return 'text-blue-800'
    case 'WARNING': return 'text-yellow-800'
    default: return 'text-gray-800'
  }
}

// Telegram functions
const fetchTelegramStatus = async () => {
  try {
    const response = await apiClient.get('/telegram/status?crypto=btc', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    telegramStatus.value = response.data
  } catch (error) {
    console.error('Error obteniendo estado de Telegram:', error)
    telegramStatus.value = {
      connected: false,
      bot_configured: false,
      subscription_status: 'inactive'
    }
  }
}

const generateTelegramConnection = async () => {
  generatingQR.value = true
  try {
    const response = await apiClient.post('/telegram/connect?crypto=btc', {}, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    qrConnection.value = response.data
    showQRModal.value = true
    
    // Inicializar contador si tenemos expires_in_seconds
    if (response.data.expires_in_seconds) {
      tokenTimeLeft.value = response.data.expires_in_seconds
      startTokenCountdown()
    }
    
    // Actualizar estado cada 5 segundos mientras está abierto el modal
    const statusCheckInterval = setInterval(async () => {
      await fetchTelegramStatus()
      if (telegramStatus.value?.connected) {
        clearInterval(statusCheckInterval)
        closeQRModal()
      }
    }, 5000)
    
    // Limpiar interval después de 10 minutos
    setTimeout(() => {
      clearInterval(statusCheckInterval)
    }, 600000)
    
  } catch (error) {
    console.error('Error generando conexión de Telegram:', error)
    // Mostrar error al usuario
  } finally {
    generatingQR.value = false
  }
}

const regenerateToken = async () => {
  regeneratingToken.value = true
  try {
    const response = await apiClient.post('/telegram/regenerate-token?crypto=btc', {}, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    qrConnection.value = response.data
    
    // Reiniciar contador con el nuevo token
    if (response.data.expires_in_seconds) {
      tokenTimeLeft.value = response.data.expires_in_seconds
      startTokenCountdown()
    }
    
  } catch (error) {
    console.error('Error regenerando token de Telegram:', error)
    // Mostrar error al usuario
  } finally {
    regeneratingToken.value = false
  }
}

const disconnectTelegram = async () => {
  try {
    await apiClient.post('/telegram/disconnect', {}, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    await fetchTelegramStatus()
  } catch (error) {
    console.error('Error desconectando de Telegram:', error)
  }
}

const sendTestAlert = async () => {
  try {
    await apiClient.post('/telegram/send-alert', {
      type: 'INFO',
      symbol: 'BTCUSDT',
      price: 45000,
      message: '🧪 Esta es una alerta de prueba desde BotU. Si recibes este mensaje, tu conexión funciona correctamente!'
    }, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    // Mostrar mensaje de confirmación
  } catch (error) {
    console.error('Error enviando alerta de prueba:', error)
  }
}

const closeQRModal = () => {
  showQRModal.value = false
  qrConnection.value = null
  stopTokenCountdown()
}

// Token countdown functions
let tokenCountdownInterval = null

const startTokenCountdown = () => {
  // Limpiar cualquier contador previo
  if (tokenCountdownInterval) {
    clearInterval(tokenCountdownInterval)
  }
  
  tokenCountdownInterval = setInterval(() => {
    if (tokenTimeLeft.value > 0) {
      tokenTimeLeft.value--
    } else {
      clearInterval(tokenCountdownInterval)
      tokenCountdownInterval = null
    }
  }, 1000)
}

const stopTokenCountdown = () => {
  if (tokenCountdownInterval) {
    clearInterval(tokenCountdownInterval)
    tokenCountdownInterval = null
  }
  tokenTimeLeft.value = 0
}

const formatTimeLeft = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

// Scanner logs functions
const refreshLogs = async () => {
  try {
    const response = await apiClient.get('/bitcoin-bot/logs', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.data.logs) {
      scannerLogs.value = response.data.logs.slice(-50) // Último 50 logs
      cooldownRemaining.value = response.data.cooldown_remaining || 0
      
      // Auto-scroll to bottom
      setTimeout(() => {
        if (logsContainer.value) {
          logsContainer.value.scrollTop = logsContainer.value.scrollHeight
        }
      }, 100)
    }
  } catch (error) {
    console.error('Error obteniendo logs del scanner:', error)
  }
}

const formatLogTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('es-ES', { hour12: false })
}

const getLogClass = (level) => {
  switch (level?.toLowerCase()) {
    case 'info': return 'bg-gray-800 border-blue-500'
    case 'warning': return 'bg-yellow-900 border-yellow-500'
    case 'error': return 'bg-red-900 border-red-500'
    case 'success': return 'bg-green-900 border-green-500'
    case 'alert': return 'bg-purple-900 border-purple-500'
    default: return 'bg-gray-800 border-gray-500'
  }
}

const getLogTextClass = (level) => {
  switch (level?.toLowerCase()) {
    case 'info': return 'text-blue-300'
    case 'warning': return 'text-yellow-300'
    case 'error': return 'text-red-300'
    case 'success': return 'text-green-300'
    case 'alert': return 'text-purple-300'
    default: return 'text-gray-300'
  }
}

const getLogIcon = (level) => {
  switch (level?.toLowerCase()) {
    case 'info': return 'ℹ️'
    case 'warning': return '⚠️'
    case 'error': return '❌'
    case 'success': return '✅'
    case 'alert': return '🚨'
    default: return '📋'
  }
}

// Lifecycle
onMounted(() => {
  refreshStatus()
  fetchTelegramStatus()
  if (botStatus.isRunning) {
    refreshLogs()
  }
})

onUnmounted(() => {
  stopPolling()
  stopTokenCountdown()
})
</script>

<style scoped>
/* Estilos adicionales si es necesario */
</style>