import axios from 'axios'

const instance = axios.create({
  baseURL: '', // 使用相对路径，让Vite代理处理
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

// 请求拦截器：自动添加token
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken')  // 使用正确的key
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理401错误
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token过期，清除并跳转登录
      localStorage.removeItem('authToken')
      localStorage.removeItem('currentUser')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default {
  // ---- 原有 ----
  getSummary ()        { return instance.get('/v1/summary').then(r => r.data) },
  getPorts ()          { return instance.get('/v1/ports').then(r => r.data) },
  getFlowStats (p, s, e) { return instance.get('/v1/flowstats', { params: { port: p, start: s, end: e } }).then(r => r.data) },
  getPortRate ()       { return instance.get('/v1/portrate').then(r => r.data) },
  getProtocolRatio (p, s, e) { return instance.get('/v1/protocolratio', { params: { port: p, start: s, end: e } }).then(r => r.data) },
  getAnomalies (hours = 12, limit = null) { 
    const params = { hours };
    if (limit !== null) {
      params.limit = limit;
    }
    return instance.get('/v1/anomalies', { params }).then(r => r.data) 
  },
  
  // 获取攻击会话数据（从attack_sessions表，已去重的攻击记录）
  getAttackSessions (hours = 12, limit = 10) {
    const params = { hours, limit };
    return instance.get('/v1/attack_sessions', { params }).then(r => r.data)
  },
  
  // 统计不同时间段的攻击会话数量（用于异常检测页面）
  getAttackSessionsCount () {
    return instance.get('/v1/attack-sessions/count').then(r => r.data)
  },

  // 统计不同时间段的已处理攻击会话数量
  getHandledSessionsCount () {
    return instance.get('/v1/handled-sessions/count').then(r => r.data)
  },

  // 更新攻击会话状态（标记为已处理）
  updateAttackStatus (ip, action, handledBy = 'admin') {
    return instance.post('/v1/attack-sessions/update-status', {
      ip,
      action,
      handled_by: handledBy
    }).then(r => r.data)
  },

  // ---- 新增 ----
  getRateLimit ()      { return instance.get('/v1/ratelimit').then(r => r.data) },
  getACL ()            { return instance.get('/v1/acl').then(r => r.data) },
  getAnomaliesWeek ()  { return instance.get('/v1/anomalies/week').then(r => r.data) },
  getAnomaliesTop10 () { return instance.get('/v1/anomalies/top10').then(r => r.data) },
  
  // 设备异常API（真正的设备问题：IP配错、端口异常等）
  getDeviceAnomalies (hours = null, status = null) { 
    const params = {}
    if (hours !== null && hours !== undefined) params.hours = hours
    if (status) params.status = status
    return instance.get('/v1/device_anomalies', { params }).then(r => r.data) 
  },
  updateDeviceAnomalyStatus (anomalyId, status = 'handled', handledBy = 'admin', handleAction = 'frontend_resolve') {
    return instance.put(`/v1/device_anomalies/${anomalyId}/handle`, { status, handled_by: handledBy, handle_action: handleAction }).then(r => r.data)
  },
  getFlowTop10 ()      { return instance.get('/v1/flowstats/top10').then(r => r.data) },
  getSwitchInfo ()     { return instance.get('/v1/switch/info').then(r => r.data) },
  getWeeklyReport ()   { return instance.get('/v1/report/weekly').then(r => r.data) },
  exportPDF ()         { return instance.get('/v1/export/pdf', { responseType: 'blob' }) },
  getGeoIP (ip)        { return instance.get(`/v1/geoip/${ip}`).then(r => r.data) },
  putThreshold (body)  { return instance.put('/v1/settings', body) },
  bulkACL (csv)        { return instance.post('/v1/bulk/acl', `csv=${encodeURIComponent(csv)}`,
                                               { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }) },
  
  // 限速趋势图API
  getRateTrend (type = 'hour') { 
    // 支持字符串和数字两种参数格式
    let backendType = 1  // 默认24小时
    
    // 如果传入的是数字，直接使用
    if (typeof type === 'number') {
      backendType = type
    } else {
      // 如果传入的是字符串，进行映射
      const typeMap = {
        'hour': 1,   // 24小时
        'day': 3,    // 3天
        'week': 7    // 7天
      }
      backendType = typeMap[type] || 1
    }
    
    return instance.get('/v1/rate-trend', { params: { type: backendType } }).then(r => r.data) 
  },
  
  // 加黑和限速API
  addBlacklist (ip, ttl = -1) { 
    const formData = new URLSearchParams()
    formData.append('ip', ip)
    formData.append('ttl', ttl)
    return instance.post('/v1/acl/black', formData, { 
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).then(r => r.data) 
  },
  removeBlacklist (ip) { 
    return instance.delete(`/v1/acl/black/${ip}`).then(r => r.data) 
  },
  addRateLimit (ip, kbps = 1024, reason = '前端手动限速', duration_minutes = 5, operator = 'admin') { 
    const formData = new URLSearchParams()
    formData.append('ip', ip)
    formData.append('kbps', kbps)
    formData.append('reason', reason)
    formData.append('duration_minutes', duration_minutes)  // ✅ 添加时长参数
    formData.append('operator', operator)  // ✅ 添加操作人参数
    return instance.post('/v1/limit/ip', formData, { 
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).then(r => r.data) 
  },
  removeRateLimit (ip) { 
    return instance.delete(`/v1/limit/ip/${ip}`).then(r => r.data) 
  },
  
  // ✅ 修改限速速率
  changeRateSpeed (ip, kbps, reason = '管理员调整速率') {
    return instance.put(`/v1/rate/speed/${ip}`, { kbps, reason }).then(r => r.data)
  },
  
  // ✅ 修改限速时间（extra_seconds: 正数=延长，负数=缩短）
  changeRateDuration (ip, extra_seconds, reason = '管理员调整时长') {
    return instance.put(`/v1/rate/duration/${ip}`, { extra_seconds, reason }).then(r => r.data)
  },
  
  // 历史限速记录API
  getRateHistoryByDay (day) { 
    return instance.get(`/v1/rate/history/${day}`).then(r => r.data) 
  },
  
  // 仪表板卡片数据API
  getDashboardCards () { 
    return instance.get('/v1/dashboard/cards').then(r => r.data) 
  },
  
  // 限速原因统计API
  getRateReasonStats (hours = 24) { 
    return instance.get('/v1/rate-reason-stats', { params: { hours } }).then(r => r.data) 
  },
  
  // ✅ 真实流量趋势API（时间序列）- 今日数据（0点至今）
  getFlowTrend () {
    return instance.get('/v1/flow-trend').then(r => r.data)
  },

  // ============= SDN流表管理API =============
  // 获取控制器状态（通过summary接口判断）
  getSDNControllerStatus () {
    return instance.get('/v1/summary').then(r => r.data).then(data => ({ 
      status: data.success ? 'online' : 'offline', 
      data 
    }))
  },

  // 获取所有交换机
  getSDNSwitches () {
    return instance.get('/v1/switches').then(r => r.data)  // 已经返回完整对象 {success, switches, message}
  },

  // 获取指定交换机的流表
  getSDNSwitchFlows (dpid) {
    return instance.get(`/v1/switches/${dpid}/flows`).then(r => r.data)  // 已经返回完整对象 {success, dpid, flows, ...}
  },

  // 添加流表项
  addSDNFlowEntry (dpid, flowEntry) {
    return instance.post(`/v1/switches/${dpid}/flows`, flowEntry).then(r => r.data)  // 返回 {success, data, message}
  },

  // 删除流表项
  deleteSDNFlowEntry (dpid, flowEntry) {
    return instance.delete(`/v1/switches/${dpid}/flows`, { data: flowEntry }).then(r => r.data)
  },

  // 删除所有流表
  deleteSDNAllFlows (dpid) {
    return instance.delete(`/v1/switches/${dpid}/flows/all`).then(r => r.data)
  },

  // ============= Mininet主机管理API =============
  // 获取Mininet主机列表
  getMininetHosts () {
    return instance.get('/v1/mininet/hosts').then(r => r.data)
  },

  // ============= 设备异常API =============
  // 获取设备异常列表
  getDeviceAnomalies (hours = null, status = null) {
    const params = {}
    if (hours !== null && hours !== undefined) params.hours = hours
    if (status) params.status = status
    return instance.get('/v1/device_anomalies', { params }).then(r => r.data)
  },

  // ============= AI Agent API (RAG + MCP) =============
  // 分析异常（使用Agent系统）
  agentAnalyzeAnomaly (anomalyInfo) {
    return instance.post('/api/agent/analyze', anomalyInfo).then(r => r.data)
  },

  // 快速查询（RAG问答）
  agentQuickQuery (query) {
    return instance.post('/api/agent/query', { query }).then(r => r.data)
  },

  // 搜索知识库
  agentSearchKnowledge (query) {
    return instance.post('/api/agent/knowledge/search', { query }).then(r => r.data)
  },

  // 获取Agent状态
  getAgentStatus () {
    return instance.get('/api/agent/status').then(r => r.data)
  },

  // 测试端点（返回示例数据）
  getAgentTestDemo () {
    return instance.get('/api/agent/test/demo').then(r => r.data)
  }
}
