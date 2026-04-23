import axios from 'axios'

const API_BASE_URL = `${import.meta.env.VITE_API_URL}/api`

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const authAPI = {
  register: (userData) => api.post('/auth/register', userData),
  login: (credentials) => api.post('/auth/login', credentials)
}

export default api
