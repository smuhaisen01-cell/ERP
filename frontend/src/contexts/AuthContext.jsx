import { createContext, useContext, useState, useEffect, useRef } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

const BASE = '/api'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('erp_user')) } catch { return null }
  })
  const [tokens, setTokens] = useState(() => {
    try { return JSON.parse(localStorage.getItem('erp_tokens')) } catch { return null }
  })

  const api = useRef(axios.create({ baseURL: BASE })).current

  // Attach token to every request
  useEffect(() => {
    const interceptor = api.interceptors.request.use(config => {
      const t = JSON.parse(localStorage.getItem('erp_tokens') || '{}')
      if (t?.access) config.headers.Authorization = `Bearer ${t.access}`
      return config
    })
    return () => api.interceptors.request.eject(interceptor)
  }, [])

  // Auto-refresh on 401
  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      res => res,
      async err => {
        const orig = err.config
        if (err.response?.status === 401 && !orig._retry) {
          orig._retry = true
          try {
            const t = JSON.parse(localStorage.getItem('erp_tokens') || '{}')
            if (t?.refresh) {
              const res = await axios.post(`${BASE}/auth/token/refresh/`, { refresh: t.refresh })
              const newTokens = { ...t, access: res.data.access }
              localStorage.setItem('erp_tokens', JSON.stringify(newTokens))
              setTokens(newTokens)
              orig.headers.Authorization = `Bearer ${res.data.access}`
              return api(orig)
            }
          } catch { logout() }
        }
        return Promise.reject(err)
      }
    )
    return () => api.interceptors.response.eject(interceptor)
  }, [])

  const login = async (username, password) => {
    const res = await axios.post(`${BASE}/auth/token/`, { username, password })
    const newTokens = res.data
    localStorage.setItem('erp_tokens', JSON.stringify(newTokens))
    setTokens(newTokens)

    // Fetch user profile with role + modules
    const meRes = await api.get('/users/me/', {
      headers: { Authorization: `Bearer ${newTokens.access}` }
    })
    const userData = meRes.data
    localStorage.setItem('erp_user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }

  const logout = () => {
    localStorage.removeItem('erp_tokens')
    localStorage.removeItem('erp_user')
    setUser(null)
    setTokens(null)
  }

  const isAuthenticated = !!tokens?.access

  return (
    <AuthContext.Provider value={{ user, tokens, api, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
