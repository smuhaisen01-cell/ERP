import { createContext, useContext, useState, useCallback } from 'react'
import axios from 'axios'

const AuthContext = createContext()

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('erp_access')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  r => r,
  async err => {
    if (err.response?.status === 401 && !err.config._retry) {
      err.config._retry = true
      const refresh = localStorage.getItem('erp_refresh')
      if (refresh) {
        try {
          const { data } = await axios.post('/api/auth/token/refresh/', { refresh })
          localStorage.setItem('erp_access', data.access)
          err.config.headers.Authorization = `Bearer ${data.access}`
          return api(err.config)
        } catch {
          localStorage.clear()
          window.location.href = '/app/login'
        }
      }
    }
    return Promise.reject(err)
  }
)

export { api }

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('erp_user')) } catch { return null }
  })

  const login = useCallback(async (username, password) => {
    const { data } = await axios.post('/api/auth/token/', { username, password })
    localStorage.setItem('erp_access', data.access)
    localStorage.setItem('erp_refresh', data.refresh)
    const me = { username, name: username }
    localStorage.setItem('erp_user', JSON.stringify(me))
    setUser(me)
    return me
  }, [])

  const logout = useCallback(() => {
    localStorage.clear()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, logout, api, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
