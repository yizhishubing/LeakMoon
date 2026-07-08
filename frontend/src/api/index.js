/**
 * API 封装
 * 作用：统一管理前后端通信，提供请求/响应拦截
 * 做法：使用 axios 创建实例，统一 baseURL 和超时设置
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 响应拦截器：统一错误提示
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
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

export const leakApi = {
  list: (params) => api.get('/leaks/', { params }),
  total: (params) => api.get('/leaks/total', { params }),
  verify: (id, data) => api.put(`/leaks/${id}/verify`, data),
}

export const alertApi = {
  list: (params) => api.get('/alerts/', { params }),
  total: (params) => api.get('/alerts/total', { params }),
  acknowledge: (id) => api.put(`/alerts/${id}/ack`),
  resolve: (id) => api.put(`/alerts/${id}/resolve`),
}

export const ruleApi = {
  list: () => api.get('/rules/'),
  reload: () => api.post('/rules/reload'),
}

export const reportApi = {
  list: () => api.get('/reports/'),
  generate: (data) => api.post('/reports/', data),
}

export default api
