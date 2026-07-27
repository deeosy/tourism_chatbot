/**
 * AuthContext — provides login state and token management to the entire app.
 *
 * Usage:
 *   const { user, token, login, signup, logout } = useAuth();
 *
 * On mount, it reads localStorage for a saved token and validates it
 * against the backend's GET /auth/me endpoint.
 */

import { createContext, useContext, useEffect, useState } from "react"

const AuthContext = createContext(null)

// Backend base URL (same pattern as the chat API)
const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:7860"

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)       // { id, name, email } or null
  const [token, setToken] = useState(null)     // JWT string or null
  const [loading, setLoading] = useState(true) // true while checking stored token

  // On mount, try to restore session from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("gg_token")
    if (saved) {
      setToken(saved)
      // Validate the token against the backend
      fetch(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${saved}` },
      })
        .then((r) => (r.ok ? r.json() : Promise.reject()))
        .then((data) => setUser(data.user))
        .catch(() => {
          // Token is invalid or expired — clear it
          localStorage.removeItem("gg_token")
          setToken(null)
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  // Sign up a new account
  const signup = async (name, email, password) => {
    const res = await fetch(`${API}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || "Signup failed")
    }
    const data = await res.json()
    localStorage.setItem("gg_token", data.token)
    setToken(data.token)
    setUser(data.user)
  }

  // Log in with existing account
  const login = async (email, password) => {
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || "Login failed")
    }
    const data = await res.json()
    localStorage.setItem("gg_token", data.token)
    setToken(data.token)
    setUser(data.user)
  }

  // Log out
  const logout = () => {
    localStorage.removeItem("gg_token")
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, signup, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// Convenience hook
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
