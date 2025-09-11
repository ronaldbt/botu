<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div>
            <h1 class="text-3xl md:text-4xl font-bold text-slate-900 mb-2">
              BNB Bot U-Pattern
            </h1>
            <p class="text-slate-600 text-base">Sistema avanzado de detección de patrones U para BNB Coin con backtesting probado</p>
            <div class="mt-2 flex items-center space-x-4 text-sm">
              <span class="bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full font-semibold">BNB Pattern Detection</span>
              <span class="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full font-semibold">BNBUSDT Trading</span>
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
                ? 'border-yellow-500 bg-yellow-50 shadow-md' 
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
          🪙 Estrategia BNB Optimizada - Modo {{ selectedMode === 'manual' ? 'Manual' : 'Automático' }}
        </h3>
        
        <div class="bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <div class="flex items-center mb-2">
            <span class="text-lg mr-2">⚙️</span>
            <h4 class="font-semibold text-slate-800">Parámetros Optimizados por Backtest 2023</h4>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-600">
            <div class="flex items-center">
              <span class="text-yellow-600 font-medium mr-2">Timeframe:</span>
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
            ✨ Los parámetros están preconfigurados según backtests históricos exitosos. Incluye filtros anti-bajistas específicos para BNB.
          </p>
        </div>

        <!-- API Keys Configuration (Automatic Mode Only) -->
        <div v-if="selectedMode === 'automatic'" class="mt-6 pt-6 border-t border-slate-200">
          <div class="bg-gradient-to-br from-emerald-50 to-green-50 border border-emerald-200 rounded-lg p-6">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center">
                <div class="text-2xl mr-3">🔑</div>
                <div>
                  <h4 class="font-semibold text-slate-900">Configuración API de Binance</h4>
                  <p class="text-sm text-slate-600">Conecta tu cuenta de Binance para trading automático</p>
                </div>
              </div>
              <button
                @click="showApiHelpModal = true"
                class="flex items-center justify-center w-8 h-8 bg-yellow-500 hover:bg-yellow-600 text-white rounded-full transition-colors duration-200 text-lg font-bold"
                title="Ayuda para obtener API Keys"
              >
                ?
              </button>
            </div>

            <!-- Environment Selector -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-slate-700 mb-2">Entorno de Trading</label>
              <div class="grid grid-cols-2 gap-4">
                <div class="relative">
                  <input type="radio" id="testnet" v-model="config.environment" value="testnet" class="sr-only">
                  <label for="testnet" :class="[
                    'block p-3 border-2 rounded-lg cursor-pointer transition-all duration-200',
                    config.environment === 'testnet' 
                      ? 'border-emerald-500 bg-emerald-50' 
                      : 'border-slate-200 hover:border-slate-300'
                  ]">
                    <div class="text-sm font-semibold text-slate-900">🧪 Testnet</div>
                    <div class="text-xs text-slate-600">Dinero virtual - Recomendado</div>
                  </label>
                </div>
                <div class="relative">
                  <input type="radio" id="mainnet" v-model="config.environment" value="mainnet" class="sr-only">
                  <label for="mainnet" :class="[
                    'block p-3 border-2 rounded-lg cursor-pointer transition-all duration-200',
                    config.environment === 'mainnet' 
                      ? 'border-red-500 bg-red-50' 
                      : 'border-slate-200 hover:border-slate-300'
                  ]">
                    <div class="text-sm font-semibold text-slate-900">💰 Mainnet</div>
                    <div class="text-xs text-slate-600">Dinero real - Solo expertos</div>
                  </label>
                </div>
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
                  class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
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
                  class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
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
                class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm font-medium transition-colors duration-200 disabled:bg-slate-400"
              >
                <span v-if="!testingConnection">Probar Conexión</span>
                <span v-else class="flex items-center">
                  <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Probando...
                </span>
              </button>
            </div>
          </div>
        </div>

        <!-- Telegram Integration (Manual Mode Only) -->
        <div v-if="selectedMode === 'manual'" class="mt-6 pt-6 border-t border-slate-200">
          <div class="bg-gradient-to-br from-yellow-50 to-amber-50 border border-yellow-200 rounded-lg p-6">
            <div class="flex items-center mb-4">
              <div class="text-2xl mr-3">📱</div>
              <div>
                <h4 class="font-semibold text-slate-900">Conexión con Telegram - BNB</h4>
                <p class="text-sm text-slate-600">Recibe alertas de BNB Coin directamente en Telegram</p>
              </div>
            </div>

            <!-- Estado de Conexión -->
            <div v-if="telegramStatus" class="mb-4">
              <div class="flex items-center p-3 rounded-lg" :class="telegramStatus.connected ? 'bg-emerald-100' : 'bg-slate-100'">
                <div class="text-lg mr-2">{{ telegramStatus.connected ? '✅' : '📱' }}</div>
                <div>
                  <div class="font-semibold" :class="telegramStatus.connected ? 'text-emerald-800' : 'text-slate-700'">
                    {{ telegramStatus.connected ? 'Conectado a Telegram BNB' : 'No conectado' }}
                  </div>
                  <div class="text-sm text-slate-600" v-if="telegramStatus.connected">
                    Estado: {{ telegramStatus.subscription_status }} - Las alertas de BNB se enviarán automáticamente
                  </div>
                  <div class="text-sm text-slate-600" v-else>
                    Conecta tu Telegram para recibir alertas de patrones U de BNB Coin
                  </div>
                </div>
              </div>
            </div>

            <!-- Botones de Control -->
            <div class="flex items-center space-x-3">
              <button
                v-if="!telegramStatus?.connected"
                @click="generateTelegramConnection"
                :disabled="generatingQR"
                class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm font-medium transition-colors duration-200 disabled:bg-slate-400"
              >
                <span v-if="!generatingQR">Conectar Telegram BNB</span>
                <span v-else class="flex items-center">
                  <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
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
                Enviar Prueba BNB
              </button>
            </div>
          </div>

          <!-- QR Code Modal -->
          <div v-if="showQRModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div class="bg-white rounded-lg w-full max-w-md max-h-screen overflow-y-auto">
              <!-- Header fijo -->
              <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 rounded-t-lg">
                <div class="flex items-center justify-between">
                  <h3 class="text-lg font-semibold text-slate-900">Conectar con Telegram BNB</h3>
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
                      alt="QR Code Telegram BNB"
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
                    <p>4. ¡Listo! Recibirás las alertas de BNB Coin</p>
                  </div>

                  <!-- Enlace directo -->
                  <div class="mb-4">
                    <a 
                      :href="qrConnection.telegram_link" 
                      target="_blank"
                      class="inline-flex items-center px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                    >
                      <span class="mr-2">📱</span>
                      Abrir en Telegram
                    </a>
                  </div>

                  <!-- Tiempo de expiración -->
                  <div class="text-xs text-slate-500 mb-4">
                    Este código expira en {{ qrConnection.expires_in_minutes }} minutos
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

          <!-- API Help Modal -->
          <div v-if="showApiHelpModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div class="bg-white rounded-lg w-full max-w-2xl max-h-screen overflow-y-auto">
              <!-- Header fijo -->
              <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 rounded-t-lg">
                <div class="flex items-center justify-between">
                  <h3 class="text-xl font-semibold text-slate-900 flex items-center">
                    🔑 Cómo obtener API Keys de Binance
                  </h3>
                  <button
                    @click="showApiHelpModal = false"
                    class="text-slate-400 hover:text-slate-600 transition-colors duration-200"
                  >
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                  </button>
                </div>
              </div>

              <!-- Contenido scrolleable -->
              <div class="px-6 py-6">
                <!-- Tabs -->
                <div class="mb-6">
                  <div class="border-b border-gray-200">
                    <nav class="-mb-px flex space-x-8">
                      <button
                        @click="activeHelpTab = 'testnet'"
                        :class="[
                          'py-2 px-1 border-b-2 font-medium text-sm',
                          activeHelpTab === 'testnet'
                            ? 'border-emerald-500 text-emerald-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        ]"
                      >
                        🧪 Testnet (Recomendado)
                      </button>
                      <button
                        @click="activeHelpTab = 'mainnet'"
                        :class="[
                          'py-2 px-1 border-b-2 font-medium text-sm',
                          activeHelpTab === 'mainnet'
                            ? 'border-red-500 text-red-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        ]"
                      >
                        💰 Mainnet (Expertos)
                      </button>
                    </nav>
                  </div>
                </div>

                <!-- Testnet Content -->
                <div v-if="activeHelpTab === 'testnet'" class="space-y-6">
                  <div class="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                    <div class="flex items-center mb-2">
                      <span class="text-2xl mr-2">✅</span>
                      <h4 class="font-semibold text-emerald-800">Testnet - Entorno de Pruebas (RECOMENDADO)</h4>
                    </div>
                    <p class="text-emerald-700 text-sm">Usa dinero virtual para aprender y probar estrategias sin riesgo</p>
                  </div>

                  <div class="space-y-4">
                    <h4 class="font-semibold text-lg flex items-center">
                      <span class="bg-emerald-100 text-emerald-800 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold mr-2">1</span>
                      Crear cuenta en Binance Testnet
                    </h4>
                    <div class="bg-gray-50 p-4 rounded-lg">
                      <p class="text-sm text-gray-700 mb-2">Ve a la página oficial de Binance Testnet:</p>
                      <a 
                        href="https://testnet.binance.vision/" 
                        target="_blank"
                        class="inline-flex items-center px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                      >
                        🔗 Abrir Binance Testnet
                        <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                        </svg>
                      </a>
                      <p class="text-xs text-gray-600 mt-2">La cuenta de testnet es completamente gratuita y separada de tu cuenta real de Binance</p>
                    </div>

                    <h4 class="font-semibold text-lg flex items-center">
                      <span class="bg-emerald-100 text-emerald-800 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold mr-2">2</span>
                      Crear API Keys en Testnet
                    </h4>
                    <div class="space-y-3">
                      <div class="flex items-start">
                        <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-0.5">2.1</span>
                        <div>
                          <p class="font-medium">Accede a API Management</p>
                          <p class="text-sm text-gray-600">Una vez logueado, ve a tu perfil > API Management</p>
                        </div>
                      </div>
                      <div class="flex items-start">
                        <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-0.5">2.2</span>
                        <div>
                          <p class="font-medium">Crear nueva API Key</p>
                          <p class="text-sm text-gray-600">Haz clic en "Create API" y elige un nombre descriptivo como "BotU-BNB"</p>
                        </div>
                      </div>
                      <div class="flex items-start">
                        <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-0.5">2.3</span>
                        <div>
                          <p class="font-medium">Configurar permisos</p>
                          <p class="text-sm text-gray-600">Activa SOLO: ✓ Enable Spot & Margin Trading</p>
                          <p class="text-xs text-red-600">⚠️ NO actives Futures, Withdrawals ni otras opciones</p>
                        </div>
                      </div>
                      <div class="flex items-start">
                        <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-0.5">2.4</span>
                        <div>
                          <p class="font-medium">Copiar las keys</p>
                          <p class="text-sm text-gray-600">Guarda tanto la API Key como la Secret Key en un lugar seguro</p>
                          <p class="text-xs text-orange-600">⚠️ La Secret Key solo se muestra una vez</p>
                        </div>
                      </div>
                    </div>

                    <h4 class="font-semibold text-lg flex items-center">
                      <span class="bg-emerald-100 text-emerald-800 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold mr-2">3</span>
                      Obtener fondos virtuales
                    </h4>
                    <div class="bg-blue-50 p-4 rounded-lg">
                      <p class="text-sm text-blue-800">En Testnet puedes obtener BNB y USDT virtuales gratis desde el "Faucet" en tu wallet. ¡Perfecto para probar el bot sin riesgo!</p>
                    </div>
                  </div>
                </div>

                <!-- Mainnet Content -->
                <div v-if="activeHelpTab === 'mainnet'" class="space-y-6">
                  <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div class="flex items-center mb-2">
                      <span class="text-2xl mr-2">⚠️</span>
                      <h4 class="font-semibold text-red-800">Mainnet - Trading con Dinero Real (SOLO EXPERTOS)</h4>
                    </div>
                    <p class="text-red-700 text-sm">Requiere experiencia previa y puede resultar en pérdidas reales de dinero</p>
                  </div>

                  <div class="space-y-4">
                    <h4 class="font-semibold text-lg flex items-center">
                      <span class="bg-red-100 text-red-800 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold mr-2">1</span>
                      Cuenta verificada en Binance
                    </h4>
                    <div class="bg-gray-50 p-4 rounded-lg">
                      <p class="text-sm text-gray-700 mb-2">Debes tener una cuenta completamente verificada en Binance:</p>
                      <a 
                        href="https://www.binance.com/" 
                        target="_blank"
                        class="inline-flex items-center px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                      >
                        🔗 Binance.com
                        <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                        </svg>
                      </a>
                    </div>

                    <h4 class="font-semibold text-lg flex items-center">
                      <span class="bg-red-100 text-red-800 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold mr-2">2</span>
                      Crear API Keys (Con precaución)
                    </h4>
                    <div class="space-y-3">
                      <div class="flex items-start">
                        <span class="bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-0.5">2.1</span>
                        <div>
                          <p class="font-medium">Ve a API Management</p>
                          <p class="text-sm text-gray-600">Perfil > Seguridad > API Management</p>
                        </div>
                      </div>
                      <div class="flex items-start">
                        <span class="bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-0.5">2.2</span>
                        <div>
                          <p class="font-medium">Crear API Key</p>
                          <p class="text-sm text-gray-600">Usar solo permisos de "Spot Trading"</p>
                          <p class="text-xs text-red-600">⚠️ NUNCA actives Withdrawals</p>
                        </div>
                      </div>
                      <div class="flex items-start">
                        <span class="bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-0.5">2.3</span>
                        <div>
                          <p class="font-medium">Restricciones IP</p>
                          <p class="text-sm text-gray-600">Recomendado: Restringir a tu IP actual para mayor seguridad</p>
                        </div>
                      </div>
                    </div>

                    <div class="bg-red-100 border border-red-300 rounded-lg p-4">
                      <h4 class="font-semibold text-red-800 mb-2">🚨 ADVERTENCIAS IMPORTANTES</h4>
                      <ul class="text-sm text-red-700 space-y-1">
                        <li>• NUNCA compartas tus API Keys reales con nadie</li>
                        <li>• Solo usa fondos que puedes permitirte perder</li>
                        <li>• Empieza con cantidades muy pequeñas</li>
                        <li>• Monitorea constantemente las operaciones</li>
                        <li>• El trading automático siempre tiene riesgos</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Footer -->
              <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 rounded-b-lg">
                <div class="flex justify-between items-center">
                  <div class="text-sm text-gray-600">
                    📚 <strong>Recomendación:</strong> Siempre prueba primero en Testnet
                  </div>
                  <button
                    @click="showApiHelpModal = false"
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
                <p class="text-sm text-amber-700">Solo tú puedes iniciar/detener el BNB Bot automático</p>
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
                  ? 'bg-yellow-600 hover:bg-yellow-700 text-white disabled:bg-slate-400' 
                  : 'bg-emerald-600 hover:bg-emerald-700 text-white disabled:bg-slate-400'
              ]"
            >
              <span v-if="!loading">{{ botStatus.isRunning ? '🤖 BNB Bot Activo - Scanner 4h' : '🚀 Iniciar BNB Bot' }}</span>
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
          <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <div class="text-4xl mb-3">👤</div>
            <h3 class="text-lg font-semibold text-yellow-900 mb-2">Usuario Cliente</h3>
            <p class="text-yellow-700 mb-4">
              El BNB Bot está controlado por el administrador. Tú recibirás las alertas automáticamente en Telegram cuando se detecten patrones U en BNB.
            </p>
            <div class="text-sm text-yellow-600">
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
          Análisis Actual de BNB Coin
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-600 mb-1">Precio Actual BNB</div>
            <div class="text-2xl font-bold text-gray-900">${{ currentAnalysis.currentPrice?.toLocaleString() }}</div>
          </div>
          
          <div class="bg-yellow-50 rounded-lg p-4">
            <div class="text-sm text-yellow-600 mb-1">Nivel de Ruptura</div>
            <div class="text-2xl font-bold text-yellow-900">
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
      </div>

      <!-- Scanner Logs Panel -->
      <div v-if="botStatus.isRunning" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-gray-900 flex items-center">
            <span class="text-2xl mr-2">📊</span>
            BNB Scanner Logs - Tiempo Real
          </h3>
          <div class="flex items-center space-x-2 text-sm text-gray-600">
            <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span>Activo</span>
          </div>
        </div>

        <div class="bg-gray-900 rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto" ref="logsContainer">
          <div v-if="scannerLogs.length === 0" class="text-gray-400 text-center py-8">
            Esperando logs del scanner de BNB...
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
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-4 flex justify-between items-center text-sm text-gray-600">
          <div>
            <span v-if="botStatus.alerts_count">Alertas BNB enviadas: <strong>{{ botStatus.alerts_count }}</strong></span>
          </div>
          <button 
            @click="refreshLogs" 
            class="text-yellow-600 hover:text-yellow-800 transition-colors duration-200"
          >
            🔄 Actualizar
          </button>
        </div>
      </div>

      <!-- Alertas Recientes BNB -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mt-8">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-gray-900 flex items-center">
            <span class="text-2xl mr-2">🚨</span>
            Alertas Recientes BNB
          </h3>
          <button 
            @click="fetchRecentAlerts" 
            class="text-yellow-600 hover:text-yellow-800 transition-colors duration-200"
          >
            🔄 Actualizar
          </button>
        </div>
        <div v-if="recentAlerts && recentAlerts.length > 0" class="space-y-3">
          <div 
            v-for="alert in recentAlerts" 
            :key="alert.id"
            class="bg-yellow-50 border border-yellow-200 rounded-lg p-4"
          >
            <div class="flex justify-between items-start mb-2">
              <span class="text-sm font-medium text-yellow-700">
                {{ alert.type === 'BUY' ? '🟢 Señal de Compra' : '🔴 Señal de Venta' }}
              </span>
              <div class="text-right text-xs text-gray-500">
                <div>{{ alert.date_day }}</div>
                <div>{{ alert.date_time }}</div>
              </div>
            </div>
            <div class="text-sm text-gray-700 mb-2">
              <strong>{{ alert.symbol }}</strong>
            </div>
            <div v-if="alert.entry_price" class="text-xs text-gray-600">
              Precio: ${{ alert.entry_price.toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}
            </div>
            <div v-if="alert.rupture_level" class="text-xs text-gray-600">
              Nivel ruptura: ${{ alert.rupture_level.toLocaleString('es-ES', {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}
            </div>
            <div class="text-xs text-gray-500 mt-2">
              Modo: {{ alert.bot_mode === 'automatic' ? 'Automático' : 'Manual' }}
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8">
          <div class="text-6xl mb-4">📪</div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">Sin alertas</h3>
          <p class="text-gray-500">Las alertas de compra/venta de BNB aparecerán aquí</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()

// Reactive data
const selectedMode = ref('manual')
const loading = ref(false)
const currentAnalysis = ref(null)
const scannerLogs = ref([])
const recentAlerts = ref([])

// Telegram state
const telegramStatus = ref(null)
const showQRModal = ref(false)
const qrConnection = ref(null)
const generatingQR = ref(false)

// API Help Modal
const showApiHelpModal = ref(false)
const activeHelpTab = ref('testnet')

// API Connection
const apiStatus = ref(null)
const testingConnection = ref(false)

const botStatus = reactive({
  isRunning: false,
  lastCheck: null,
  mode: null,
  alerts_count: 0
})

const config = reactive({
  timeframe: '4h',
  takeProfit: 12.0,
  stopLoss: 5.0,
  tradeAmount: 50,
  maxConcurrentTrades: 1,
  environment: 'testnet',
  symbol: 'BNBUSDT',
  apiKey: '',
  secretKey: ''
})

// Polling interval
let statusInterval = null

// Methods
const startBot = async () => {
  loading.value = true
  try {
    const response = await axios.post('http://localhost:8000/bnb-bot/start', {
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
    
    console.log('BNB Bot iniciado:', response.data)
  } catch (error) {
    console.error('Error iniciando BNB Bot:', error)
  } finally {
    loading.value = false
  }
}

const stopBot = async () => {
  loading.value = true
  try {
    await axios.post('http://localhost:8000/bnb-bot/stop', {}, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    botStatus.isRunning = false
    botStatus.mode = null
    stopPolling()
    
  } catch (error) {
    console.error('Error deteniendo BNB Bot:', error)
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
      fetchRecentAlerts()
    ])
  } catch (error) {
    console.error('Error actualizando estado:', error)
  } finally {
    loading.value = false
  }
}

const fetchStatus = async () => {
  try {
    const response = await axios.get('http://localhost:8000/bnb-bot/status', {
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
    const response = await axios.get('http://localhost:8000/bnb-bot/analysis', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    currentAnalysis.value = response.data
  } catch (error) {
    console.error('Error obteniendo análisis:', error)
  }
}

const startPolling = () => {
  if (statusInterval) clearInterval(statusInterval)
  
  statusInterval = setInterval(async () => {
    if (botStatus.isRunning) {
      await Promise.all([
        fetchCurrentAnalysis(),
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

// Telegram functions
const generateTelegramConnection = async () => {
  generatingQR.value = true
  try {
    const response = await axios.post('http://localhost:8000/telegram/connect?crypto=bnb', {}, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    qrConnection.value = response.data
    showQRModal.value = true
    
    console.log('Telegram BNB connection generated:', response.data)
  } catch (error) {
    console.error('Error generando conexión de Telegram BNB:', error)
  } finally {
    generatingQR.value = false
  }
}

const disconnectTelegram = async () => {
  try {
    await axios.post('http://localhost:8000/telegram/disconnect?crypto=bnb', {}, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
  } catch (error) {
    console.error('Error desconectando de Telegram BNB:', error)
  }
}

const sendTestAlert = async () => {
  try {
    await axios.post('http://localhost:8000/telegram/send-alert/bnb', {
      type: 'INFO',
      symbol: 'BNBUSDT',
      price: 600,
      message: '🧪 Esta es una alerta de prueba para BNB Coin desde BotU. Si recibes este mensaje, tu conexión BNB funciona correctamente!'
    }, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
  } catch (error) {
    console.error('Error enviando alerta de prueba BNB:', error)
  }
}

const closeQRModal = () => {
  showQRModal.value = false
  qrConnection.value = null
}

const testApiConnection = async () => {
  testingConnection.value = true
  try {
    const response = await axios.post('http://localhost:8000/bnb-bot/test-connection', {
      apiKey: config.apiKey,
      secretKey: config.secretKey,
      environment: config.environment
    }, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    apiStatus.value = response.data
  } catch (error) {
    console.error('Error testing API connection:', error)
    apiStatus.value = {
      connected: false,
      message: 'Error probando conexión: ' + (error.response?.data?.detail || error.message)
    }
  } finally {
    testingConnection.value = false
  }
}

// Scanner logs functions
const refreshLogs = async () => {
  try {
    const response = await axios.get('http://localhost:8000/bnb-bot/logs', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.data.logs) {
      scannerLogs.value = response.data.logs.slice(-50) // Último 50 logs
    }
  } catch (error) {
    console.error('Error obteniendo logs del scanner BNB:', error)
  }
}

const fetchRecentAlerts = async () => {
  try {
    const response = await axios.get('http://localhost:8000/bnb-bot/alerts', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    recentAlerts.value = response.data
  } catch (error) {
    console.error('Error obteniendo alertas recientes BNB:', error)
    recentAlerts.value = []
  }
}

const formatLogTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('es-ES', { hour12: false })
}

const getLogClass = (level) => {
  switch (level?.toLowerCase()) {
    case 'info': return 'bg-gray-800 border-yellow-500'
    case 'warning': return 'bg-yellow-900 border-yellow-500'
    case 'error': return 'bg-red-900 border-red-500'
    case 'success': return 'bg-green-900 border-green-500'
    case 'alert': return 'bg-purple-900 border-purple-500'
    default: return 'bg-gray-800 border-gray-500'
  }
}

const getLogTextClass = (level) => {
  switch (level?.toLowerCase()) {
    case 'info': return 'text-yellow-300'
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
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
/* Estilos adicionales si es necesario */
</style>