// API Configuration
const API_BASE_URL = import.meta.env.PROD 
  ? 'https://api.botut.net' 
  : 'http://localhost:8000'

export default {
  baseURL: API_BASE_URL
}