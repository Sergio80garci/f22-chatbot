// Cliente HTTP central — todas las llamadas al backend pasan por aqui.
// En desarrollo: VITE_API_URL vacio, Vite proxy maneja /api/* hacia localhost:8001.
// En produccion (GitHub Pages): VITE_API_URL apunta al Cloud Run completo.
import axios from 'axios'

export const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')

export const apiUrl = (path) => `${API_BASE}${path.startsWith('/') ? path : '/' + path}`

export const api = axios.create({
  baseURL: API_BASE || undefined,
  timeout: 120000,
})
