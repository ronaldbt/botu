import { ref, reactive } from 'vue'
import apiClient from '@/config/api'

export function useTradingApiKeys() {
  // Estado reactivo
  const apiKeys = ref([])
  const testingConnection = ref(null)
  const submittingApiKey = ref(false)
  const loadingBalances = ref(null)

  // Formulario para agregar API Key
  const apiKeyForm = reactive({
    api_key: '',
    secret_key: '',
    is_testnet: true, // Default a testnet por seguridad
    max_position_size_usdt: 50,
    max_concurrent_positions: 3,
    auto_trading_enabled: false
  })

  // Funciones
  const loadApiKeys = async () => {
    console.log('[useTradingApiKeys] loadApiKeys() -> GET /trading/api-keys')
    try {
      const response = await apiClient.get('/trading/api-keys')
      apiKeys.value = response.data
      console.log('[useTradingApiKeys] API keys recibidas:', {
        total: apiKeys.value.length,
        ids: apiKeys.value.map(k => k.id),
        testnets: apiKeys.value.map(k => ({ id: k.id, is_testnet: k.is_testnet, status: k.connection_status })),
        raw_data: response.data
      })
    } catch (error) {
      console.error('Error cargando API keys:', error)
      console.error('Error details:', error.response?.data)
    }
  }

  const submitApiKey = async () => {
    console.log('[useTradingApiKeys] submitApiKey() payload:', { ...apiKeyForm })
    console.log('[useTradingApiKeys] is_testnet value:', apiKeyForm.is_testnet)
    submittingApiKey.value = true
    try {
      await apiClient.post('/trading/api-keys', apiKeyForm)
      resetApiKeyForm()
      await loadApiKeys()
      alert('✅ API Key agregada exitosamente')
    } catch (error) {
      console.error('Error guardando API key:', error)
      alert('❌ Error guardando API key: ' + (error.response?.data?.detail || error.message))
    } finally {
      submittingApiKey.value = false
      console.log('[useTradingApiKeys] submitApiKey() finalizado')
    }
  }

  const testConnection = async (apiKey) => {
    console.log('[useTradingApiKeys] testConnection() para API Key:', apiKey?.id)
    testingConnection.value = apiKey.id
    try {
      const response = await apiClient.post(`/trading/test-connection/${apiKey.id}`, {})
      if (response.data.success) {
        alert(`✅ Conexión exitosa\n${response.data.testnet ? 'Testnet' : 'Mainnet'}\nBalance: $${response.data.balance_usdt?.toFixed(2) || '0.00'}`)
      } else {
        alert(`❌ Error de conexión: ${response.data.message}`)
      }
      await loadApiKeys() // Actualizar estado
    } catch (error) {
      console.error('Error probando conexión:', error)
      alert('❌ Error probando conexión: ' + (error.response?.data?.detail || error.message))
    } finally {
      testingConnection.value = null
      console.log('[useTradingApiKeys] testConnection() finalizado para', apiKey?.id)
    }
  }

  const checkBalances = async (apiKey) => {
    console.log('[useTradingApiKeys] checkBalances() para API Key:', apiKey?.id)
    loadingBalances.value = apiKey.id
    try {
      const response = await apiClient.get(`/trading/balances/${apiKey.id}`)
      
      if (response.data.success) {
        const balances = response.data.balances
        let balanceText = `💰 Balances en ${response.data.testnet ? 'Testnet' : 'Mainnet'}:\n\n`
        
        // Mostrar las principales criptos
        const mainCryptos = ['USDT', 'BTC', 'ETH', 'BNB']
        let hasBalances = false
        
        for (const crypto of mainCryptos) {
          const balance = balances.find(b => b.asset === crypto)
          if (balance && parseFloat(balance.free) > 0) {
            balanceText += `${crypto}: ${parseFloat(balance.free).toFixed(8)} (Bloqueado: ${parseFloat(balance.locked).toFixed(8)})\n`
            hasBalances = true
          }
        }
        
        if (!hasBalances) {
          balanceText += `❌ No tienes fondos en las principales criptos (USDT, BTC, ETH, BNB)\n\n`
          if (response.data.testnet) {
            balanceText += `💡 TESTNET: Para obtener fondos ficticios:\n`
            balanceText += `1. Ve a testnet.binance.vision\n`
            balanceText += `2. Wallet > Spot > Faucet\n`
            balanceText += `3. Solicita USDT, BTC, ETH gratis`
          }
        }
        
        alert(balanceText)
      } else {
        alert(`❌ Error consultando balances: ${response.data.message}`)
      }
    } catch (error) {
      console.error('Error consultando balances:', error)
      alert('❌ Error consultando balances: ' + (error.response?.data?.detail || error.message))
    } finally {
      loadingBalances.value = null
      console.log('[useTradingApiKeys] checkBalances() finalizado para', apiKey?.id)
    }
  }

  const editApiKey = (apiKey) => {
    console.log('[useTradingApiKeys] editApiKey() clic:', apiKey?.id)
    // TODO: Implementar modal de edición
    alert('🚧 Función de edición en desarrollo')
  }

  const deleteApiKey = async (apiKeyId) => {
    console.log('[useTradingApiKeys] deleteApiKey() solicitada para', apiKeyId)
    if (!confirm('¿Estás seguro de que quieres eliminar esta API key?')) return
    
    try {
      await apiClient.delete(`/trading/api-keys/${apiKeyId}`)
      await loadApiKeys()
      alert('✅ API Key eliminada exitosamente')
    } catch (error) {
      console.error('Error eliminando API key:', error)
      alert('❌ Error eliminando API key: ' + (error.response?.data?.detail || error.message))
    }
  }

  const toggleCrypto = (apiKey, crypto) => {
    console.log('[useTradingApiKeys] toggleCrypto() clic', { apiKeyId: apiKey?.id, crypto })
    const cryptoNames = { btc: 'Bitcoin', btc_30m: 'Bitcoin 30m', eth: 'Ethereum', bnb: 'BNB' }
    const currentEnabled = apiKey[`${crypto}_enabled`]
    const currentAllocated = apiKey[`${crypto}_allocated_usdt`] || 0
    
    // Si está habilitando
    if (!currentEnabled) {
      const confirmed = confirm(`⚠️ ¿Estás seguro de que quieres activar el bot automático para ${cryptoNames[crypto]}?\n\n✅ Esto iniciará trading automático usando tu estrategia probada (8% TP, 3% SL)\n💰 Necesitas asignar un balance en USDT para esta crypto`)
      
      if (confirmed) {
        const amount = prompt(`💰 ¿Cuántos USDT quieres asignar a ${cryptoNames[crypto]}?\n\nBalance actual asignado: $${currentAllocated.toFixed(2)}`, currentAllocated.toString())
        
        if (amount !== null && !isNaN(amount) && parseFloat(amount) > 0) {
          updateCryptoAllocation(apiKey.id, crypto, true, parseFloat(amount))
        }
      }
    } else {
      // Si está deshabilitando
      const confirmed = confirm(`🛑 ¿Estás seguro de que quieres desactivar el trading automático para ${cryptoNames[crypto]}?\n\n⚠️ Se cancelarán las órdenes pendientes y se detendrá el monitoreo automático`)
      
      if (confirmed) {
        updateCryptoAllocation(apiKey.id, crypto, false, currentAllocated)
      }
    }
  }

  const updateCryptoAllocation = async (apiKeyId, crypto, enabled, allocatedUsdt) => {
    console.log('[useTradingApiKeys] updateCryptoAllocation() PUT /trading/crypto-allocation', { apiKeyId, crypto, enabled, allocatedUsdt })
    try {
      const response = await apiClient.put(`/trading/crypto-allocation/${apiKeyId}`, {
        crypto: crypto,
        enabled: enabled,
        allocated_usdt: allocatedUsdt
      })
      
      await loadApiKeys()
      console.log('[useTradingApiKeys] updateCryptoAllocation() respuesta:', response.data)
      alert(`✅ ${response.data.message}`)
      
    } catch (error) {
      console.error('Error actualizando crypto allocation:', error)
      alert('❌ Error actualizando configuración: ' + (error.response?.data?.detail || error.message))
    }
  }

  const resetApiKeyForm = () => {
    console.log('[useTradingApiKeys] resetApiKeyForm()')
    Object.assign(apiKeyForm, {
      api_key: '',
      secret_key: '',
      is_testnet: true, // Default a testnet por seguridad
      max_position_size_usdt: 50,
      max_concurrent_positions: 3,
      auto_trading_enabled: false
    })
  }

  const getCurrentApiKey = (environment = null) => {
    console.log('[useTradingApiKeys] getCurrentApiKey() - apiKeys:', apiKeys.value.length, 'environment:', environment)
    
    let filteredKeys = apiKeys.value
    
    // Filtrar por ambiente si se especifica
    if (environment) {
      if (environment === 'testnet') {
        filteredKeys = apiKeys.value.filter(key => key.is_testnet === true)
      } else if (environment === 'mainnet') {
        filteredKeys = apiKeys.value.filter(key => key.is_testnet === false)
      }
    }
    
    // Devolver la primera API key activa del ambiente, o la primera disponible
    return filteredKeys.find(key => key.is_active) || filteredKeys[0] || null
  }

  return {
    // Estado
    apiKeys,
    testingConnection,
    submittingApiKey,
    loadingBalances,
    apiKeyForm,
    
    // Funciones
    loadApiKeys,
    submitApiKey,
    testConnection,
    checkBalances,
    editApiKey,
    deleteApiKey,
    toggleCrypto,
    updateCryptoAllocation,
    resetApiKeyForm,
    getCurrentApiKey
  }
}