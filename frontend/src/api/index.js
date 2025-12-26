import axios from 'axios'

const API_URL = 'http://localhost:5000/api'

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// ==================== 사용자 API ====================
export const userApi = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
  search: (params) => api.get('/users/search', { params })
}

// ==================== 장비 API ====================
export const equipmentApi = {
  getAll: (params) => api.get('/equipment', { params }),
  getById: (id) => api.get(`/equipment/${id}`),
  getByAsset: (assetNumber) => api.get(`/equipment/asset/${assetNumber}`),
  create: (data) => api.post('/equipment', data),
  update: (id, data) => api.put(`/equipment/${id}`, data),
  delete: (id) => api.delete(`/equipment/${id}`),
  search: (params) => api.get('/equipment/search', { params }),
  getAvailable: () => api.get('/equipment/available')
}

// ==================== 할당 API ====================
export const assignmentApi = {
  getAll: () => api.get('/assignments'),
  getActive: () => api.get('/assignments/active'),
  create: (data) => api.post('/assignments', data),
  return: (id, data) => api.put(`/assignments/${id}/return`, data),
  getByUser: (userId) => api.get(`/assignments/user/${userId}`),
  getByEquipment: (equipmentId) => api.get(`/assignments/equipment/${equipmentId}`)
}

// ==================== 보안씰 API ====================
export const sealApi = {
  getAll: () => api.get('/security-seals'),
  getById: (id) => api.get(`/security-seals/${id}`),
  create: (data) => api.post('/security-seals', data),
  update: (id, data) => api.put(`/security-seals/${id}`, data),
  delete: (id, data) => api.delete(`/security-seals/${id}`, { data }),
  search: (params) => api.get('/security-seals/search', { params }),
  getByEquipment: (equipmentId) => api.get(`/security-seals/equipment/${equipmentId}`),
  checkDuplicate: (params) => api.get('/security-seals/check-duplicate', { params })
}

// ==================== 수리/점검 API ====================
export const maintenanceApi = {
  getAll: (params) => api.get('/maintenance-logs', { params }),
  getById: (id) => api.get(`/maintenance-logs/${id}`),
  create: (data) => api.post('/maintenance-logs', data),
  update: (id, data) => api.put(`/maintenance-logs/${id}`, data),
  delete: (id) => api.delete(`/maintenance-logs/${id}`),
  getByEquipment: (equipmentId) => api.get(`/maintenance-logs/equipment/${equipmentId}`)
}

// ==================== 이력 API ====================
export const historyApi = {
  getChangeLogs: (params) => api.get('/change-logs', { params }),
  getRecentChanges: (limit) => api.get('/change-logs/recent', { params: { limit } })
}

// ==================== 통계 API ====================
export const statisticsApi = {
  get: () => api.get('/statistics')
}

// ==================== 임포트/익스포트 API ====================
export const importApi = {
  exportExcel: () => api.get('/export/excel', { responseType: 'blob' }),
  previewImport: (formData) => api.post('/import/excel/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  executeImport: (formData) => api.post('/import/excel/execute', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  downloadTemplate: () => api.get('/import/template', { responseType: 'blob' })
}

export default api