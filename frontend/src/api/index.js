/**
 * API 封装
 * 作用：统一管理前后端通信，提供请求/响应拦截
 */

import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    console.error('[API Error]', msg)
    return Promise.reject(error)
  }
)

export const websiteApi = {
  list: () => api.get('/websites/'),
  create: (data) => api.post('/websites/', data),
  update: (id, data) => api.put(`/websites/${id}`, data),
  delete: (id) => api.delete(`/websites/${id}`),
}

export const crawlerApi = {
  run: (websiteId) => api.post(`/crawlers/run/${websiteId}`),
}

export const alertApi = {
  list: (params) => api.get('/alerts/', { params }),
}

export const ruleApi = {
  list: () => api.get('/rules/'),
  reload: () => api.post('/rules/reload'),
}

export default api
