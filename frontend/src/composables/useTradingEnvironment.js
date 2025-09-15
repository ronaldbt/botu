import { ref, computed } from 'vue'

export function useTradingEnvironment() {
  // Estado reactivo
  const environment = ref('testnet') // Default a testnet por seguridad

  // Computed
  const isTestnet = computed(() => environment.value === 'testnet')
  const isMainnet = computed(() => environment.value === 'mainnet')

  // Funciones
  const getCurrentEnvironment = () => environment.value

  const setEnvironment = (newEnvironment) => {
    if (['testnet', 'mainnet'].includes(newEnvironment)) {
      environment.value = newEnvironment
      // Persistir en localStorage (mismo key que el componente)
      localStorage.setItem('trading-environment', newEnvironment)
      console.log('[useTradingEnvironment] Ambiente cambiado a:', newEnvironment)
    }
  }

  const loadEnvironment = () => {
    const saved = localStorage.getItem('trading-environment')
    if (saved && ['testnet', 'mainnet'].includes(saved)) {
      environment.value = saved
    }
    console.log('[useTradingEnvironment] Ambiente cargado:', environment.value)
  }

  const filterApiKeysByEnvironment = (apiKeys) => {
    if (!Array.isArray(apiKeys)) return []
    
    if (environment.value === 'testnet') {
      return apiKeys.filter(key => key.is_testnet === true)
    } else {
      return apiKeys.filter(key => key.is_testnet === false)
    }
  }

  const filterOrdersByEnvironment = (orders) => {
    if (!Array.isArray(orders)) return []
    
    // Asumiendo que las órdenes tienen una propiedad is_testnet
    // Si no la tienen, puedes filtrar por API key o otra lógica
    if (environment.value === 'testnet') {
      return orders.filter(order => order.is_testnet === true)
    } else {
      return orders.filter(order => order.is_testnet === false)
    }
  }

  return {
    // Estado
    environment,
    isTestnet,
    isMainnet,
    
    // Funciones
    getCurrentEnvironment,
    setEnvironment,
    loadEnvironment,
    filterApiKeysByEnvironment,
    filterOrdersByEnvironment
  }
}

