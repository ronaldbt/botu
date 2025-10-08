import axios from 'axios'

// Determinar la URL base del API
const API_URL = import.meta.env.VITE_API_URL || 'https://api.botut.net'

console.log('🌐 [API Config] Configurando cliente de API')
console.log('🌐 [API Config] VITE_API_URL:', import.meta.env.VITE_API_URL)
console.log('🌐 [API Config] URL base final:', API_URL)

// Crear instancia de axios configurada
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000 // 30 segundos timeout
})

// Interceptor para agregar token automáticamente
apiClient.interceptors.request.use(
  (config) => {
    console.log('📤 [API Request]', {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      hasToken: !!localStorage.getItem('token')
    })
    
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log('🔑 [API Request] Token agregado al request')
    } else {
      console.warn('⚠️ [API Request] No hay token disponible')
    }
    return config
  },
  (error) => {
    console.error('❌ [API Request] Error en interceptor de request:', error)
    return Promise.reject(error)
  }
)

// Interceptor para manejo de errores
apiClient.interceptors.response.use(
  (response) => {
    console.log('✅ [API Response]', {
      status: response.status,
      url: response.config.url,
      data: response.data
    })
    return response
  },
  (error) => {
    console.error('❌ [API Response] Error en response:', {
      url: error.config?.url,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message
    })
    
    if (error.response?.status === 401) {
      console.warn('🚪 [API Response] Token inválido o expirado, redirigiendo al login')
      // Remover token inválido
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient

// Para compatibilidad con código existente
export { apiClient }