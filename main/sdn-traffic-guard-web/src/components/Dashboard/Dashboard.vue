<!-- Dashboard.vue - 网络流量监控大屏 -->
<template>
  <div class="min-h-screen bg-gray-50 font-inter">

    <!-- 主内容区 -->
    <main class="container mx-auto px-4 py-6">
      <!-- 状态概览卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-xl p-6 card-shadow hover-lift">
          <div class="flex justify-between items-start">
            <div>
              <p class="text-gray-500 text-sm font-medium">在线交换机</p>
              <h3 class="text-3xl font-bold mt-1">{{ switchCount }}</h3>
              <p class="text-secondary text-sm mt-2 flex items-center">
                <i class="fa fa-arrow-up mr-1"></i> 实时数据
              </p>
            </div>
            <div class="bg-blue-100 p-3 rounded-lg">
              <i class="fa fa-server text-primary text-xl"></i>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-xl p-6 card-shadow hover-lift">
          <div class="flex justify-between items-start">
            <div>
              <p class="text-gray-500 text-sm font-medium">活跃主机</p>
              <h3 class="text-3xl font-bold mt-1">{{ hostCount }}</h3>
              <p class="text-secondary text-sm mt-2 flex items-center">
                <i class="fa fa-arrow-up mr-1"></i> 实时数据
              </p>
            </div>
            <div class="bg-green-100 p-3 rounded-lg">
              <i class="fa fa-desktop text-secondary text-xl"></i>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-xl p-6 card-shadow hover-lift">
          <div class="flex justify-between items-start">
            <div>
              <p class="text-gray-500 text-sm font-medium">今日异常数据包</p>
              <h3 class="text-3xl font-bold mt-1">{{ anomalyCount }}</h3>
              <p class="text-danger text-sm mt-2 flex items-center">
                <i class="fa fa-arrow-up mr-1"></i> 实时数据
              </p>
            </div>
            <div class="bg-yellow-100 p-3 rounded-lg">
              <i class="fa fa-exclamation-circle text-warning text-xl"></i>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-xl p-6 card-shadow hover-lift">
          <div class="flex justify-between items-start">
            <div>
              <p class="text-gray-500 text-sm font-medium">限速主机</p>
              <h3 class="text-3xl font-bold mt-1">{{ limitedCount }}</h3>
              <p class="text-gray-500 text-sm mt-2 flex items-center">
                <i class="fa fa-minus mr-1"></i> 实时数据
              </p>
            </div>
            <div class="bg-purple-100 p-3 rounded-lg">
              <i class="fa fa-lock text-info text-xl"></i>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 加载状态和错误提示 -->
      <div v-if="isLoading || errorMessage" class="mb-4">
        <div v-if="isLoading" class="bg-blue-50 text-blue-700 p-3 rounded-lg flex items-center">
          <i class="fa fa-spinner fa-spin mr-2"></i> 正在加载数据...
        </div>
        <div v-if="errorMessage" class="bg-red-50 text-red-700 p-3 rounded-lg flex items-center">
          <i class="fa fa-exclamation-circle mr-2"></i> {{ errorMessage }}
        </div>
      </div>
      
      <!-- 流量监控图表 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <!-- 网络流量趋势图 -->
        <div class="bg-white rounded-xl p-6 card-shadow">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-lg font-semibold">网络流量趋势</h2>
            <div class="flex space-x-2 items-center">
              <div class="mr-4 flex items-center">
                <input 
                  type="checkbox" 
                  id="autoRefresh" 
                  v-model="autoRefresh" 
                  @change="setupAutoRefresh"
                  class="mr-2"
                />
                <label for="autoRefresh" class="text-sm text-gray-600">自动刷新</label>
              </div>
              <button 
                @click="handleManualRefresh" 
                class="text-primary text-sm hover:underline flex items-center"
                :disabled="isLoading"
              >
                <i class="fa fa-refresh mr-1" :class="{'fa-spin': isLoading}"></i> 刷新
              </button>
            </div>
          </div>
          <div class="h-64">
            <canvas ref="trafficChart"></canvas>
          </div>
        </div>
        
        <!-- 攻击类型分布图 -->
        <div class="bg-white rounded-xl p-6 card-shadow">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-lg font-semibold">攻击类型分布</h2>
            <button @click="goToAnomalies" class="text-primary text-sm hover:underline">详细</button>
          </div>
          <div class="h-64 relative">
            <!-- ✅ 空数据提示 -->
            <div v-if="!protocolData.labels || protocolData.labels.length === 0" 
                 class="absolute inset-0 flex items-center justify-center text-gray-400">
              <div class="text-center">
                <svg class="w-16 h-16 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <p class="text-lg font-medium">今日没有异常</p>
              </div>
            </div>
            <canvas v-show="protocolData.labels && protocolData.labels.length > 0" ref="protocolChart"></canvas>
          </div>
        </div>
      </div>
       


      <!-- 异常检测和访问控制 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <!-- 最近异常事件 -->
        <div class="bg-white rounded-xl p-6 card-shadow lg:col-span-2">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-lg font-semibold">最近异常事件 (12小时内)</h2>
            <button @click="goToAnomalies" class="text-primary text-sm hover:underline">查看全部</button>
          </div>
          
          <!-- ✅ 添加固定高度和自定义滚动条 -->
          <div class="overflow-x-auto anomaly-scroll-container" :style="{ maxHeight: aclCardHeight }">
            <table class="min-w-full">
              <thead class="sticky top-0 z-10 bg-white">
                <tr class="bg-gray-50 border-b-2 border-gray-200">
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">时间</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">源IP</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">异常类型</th>
                  <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">详情</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-100">
                <!-- 空状态提示 -->
                <tr v-if="recentAnomalies.length === 0">
                  <td colspan="4" class="py-8 text-center">
                    <div class="flex flex-col items-center justify-center">
                      <svg class="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
                      </svg>
                      <p class="text-gray-500 font-medium mb-1">网络状态良好</p>
                      <p class="text-gray-400 text-sm">当前没有检测到异常事件</p>
                    </div>
                  </td>
                </tr>
                <!-- 异常事件列表 -->
                <tr v-for="anomaly in recentAnomalies" :key="anomaly.id" class="hover:bg-gray-50 transition-colors duration-150">
                  <td class="px-4 py-4 whitespace-nowrap">
                    <div class="flex items-center text-sm text-gray-600">
                      <i class="far fa-clock mr-2 text-gray-400"></i>
                      {{ formatTime(anomaly.timestamp) }}
                    </div>
                  </td>
                  <td class="px-4 py-4 whitespace-nowrap">
                    <div class="flex flex-col">
                      <span class="text-sm font-semibold text-gray-900">{{ anomaly.src_ip }}</span>
                      <span class="text-xs text-gray-500 mt-1">{{ getHostName(anomaly.src_ip) }}</span>
                    </div>
                  </td>
                  <td class="px-4 py-4 whitespace-nowrap">
                    <span :class="getAnomalyTypeClass(anomaly.type)" class="px-3 py-1.5 text-xs font-medium rounded-md inline-flex items-center">
                      <i :class="getAnomalyTypeIcon(anomaly.type)" class="mr-1.5"></i>
                      {{ anomaly.type }}
                    </span>
                  </td>
                  <td class="px-4 py-4">
                    <span class="text-sm text-gray-600">{{ anomaly.details }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- 访问控制列表 -->
        <div class="bg-white rounded-xl p-6 card-shadow">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-lg font-semibold">访问控制</h2>
            <div class="flex space-x-2">
              <button @click="goToACL" class="text-primary text-sm hover:underline">查看全部</button>
            </div>
          </div>
          
          <div class="flex space-x-2 mb-4">
            <button 
              @click="activeTab = 'whitelist'" 
              :class="activeTab === 'whitelist' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
              class="px-3 py-1 text-xs rounded-md transition-colors"
            >
              白名单
            </button>
            <button 
              @click="activeTab = 'blacklist'" 
              :class="activeTab === 'blacklist' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
              class="px-3 py-1 text-xs rounded-md transition-colors"
            >
              黑名单
            </button>
          </div>
          
          <!-- 白名单 -->
           <div v-if="activeTab === 'whitelist'" class="space-y-4">
             <div v-for="item in whitelist" :key="item.ip" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
               <div>
                 <p class="font-medium">{{ item.ip }}</p>
                 <p class="text-xs text-gray-500">{{ item.description }}</p>
               </div>
               <button @click="removeFromWhitelist(item.ip)" class="text-danger hover:text-danger/80 text-sm">移除</button>
             </div>
           </div>
           
           <!-- 黑名单 -->
           <div v-if="activeTab === 'blacklist'" class="space-y-4">
             <div v-for="item in blacklist" :key="item.ip" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
               <div>
                 <p class="font-medium">{{ item.ip }}</p>
                 <p class="text-xs text-gray-500">{{ item.description }}</p>
               </div>
               <button @click="removeFromBlacklist(item.ip)" class="text-primary hover:text-primary/80 text-sm">移除</button>
             </div>
           </div>
           
           <button @click="activeTab === 'whitelist' ? addToWhitelist() : addToBlacklist()" class="mt-6 w-full py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg transition-colors flex items-center justify-center">
             <i class="fa fa-plus mr-2"></i> 添加IP到{{ activeTab === 'whitelist' ? '白名单' : '黑名单' }}
           </button>
        </div>
      </div>
    </main>

    <!-- 自定义模态框组件 -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden transform transition-all duration-300 scale-100">
        <!-- 模态框头部 -->
        <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 class="text-lg font-medium text-gray-900">{{ modalTitle }}</h3>
          <button @click="showModal = false" class="text-gray-400 hover:text-gray-600 focus:outline-none">
            <i class="fa fa-times text-lg"></i>
          </button>
        </div>
        
        <!-- 模态框内容 -->
        <div class="px-6 py-5">
          <!-- IP输入模态框 -->
          <div v-if="modalType === 'blacklist-add' || modalType === 'whitelist-add'">
            <p class="text-gray-600 mb-4">{{ modalType === 'blacklist-add' ? '请输入要添加到黑名单的IP地址' : '请输入要添加到白名单的IP地址' }}</p>
            <div class="space-y-2">
              <div class="relative">
                <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                  <i class="fa fa-globe text-gray-400"></i>
                </span>
                <input
                  v-model="ipInput"
                  type="text"
                  placeholder="例如: 192.168.1.100"
                  class="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-3 focus:ring-primary/20 focus:border-primary transition-all duration-200"
                  @input="ipInputError = ''"
                  @keyup.enter="handleModalConfirm"
                  autocomplete="off"
                />
              </div>
              <p v-if="ipInputError" class="text-danger text-sm mt-1">{{ ipInputError }}</p>
            </div>
          </div>
          
          <!-- 确认模态框 -->
          <div v-if="modalType === 'confirm'">
            <p class="text-gray-700">{{ modalMessage }}</p>
          </div>
        </div>
        
        <!-- 模态框底部按钮 -->
        <div class="px-6 py-4 bg-gray-50 flex justify-end space-x-3">
          <button
            @click="showModal = false"
            class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary/20 transition-colors"
          >
            取消
          </button>
          <button
            @click="handleModalConfirm"
            class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition-colors"
          >
            确认
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import ryuApi from '@/api/ryu'
import Chart from 'chart.js/auto'
import axios from 'axios'

const router = useRouter()

// 基于SDN拓扑的IP到主机名映射
const ipToHostMap = {
  '192.168.1.100': 'h1 ',
  '192.168.1.108': 'h8 ',
  '192.168.1.101': 'h2 ',
  '192.168.1.102': 'h3 ',
  '192.168.1.103': 'h4 ',
  '192.168.1.104': 'h5 ',
  '192.168.1.105': 'h6 ',
  '192.168.1.200': 'h7 '
}

// 获取主机名
const getHostName = (ip) => {
  return ipToHostMap[ip] || '未知主机'
}

// 响应式数据
const currentTime = ref('')
const autoRefresh = ref(true)
const refreshInterval = ref(null)
const activeTab = ref('whitelist')
const isLoading = ref(false)
const errorMessage = ref('')
const isFirstLoad = ref(true) // ✅ 标记首次加载

// 网络状态数据
const switchCount = ref(0)
const hostCount = ref(0)
const anomalyCount = ref(0)
const limitedCount = ref(0)

// Chart.js 引用
const trafficChart = ref(null)
const protocolChart = ref(null)
let trafficChartInstance = null
let protocolChartInstance = null

// 最近异常事件数据
const recentAnomalies = ref([])

// 异常统计数据（基于真实数据）
const anomalyStats = ref({
  synFlood: 0,
  arpSpoof: 0,
  udpFlood: 0,
  icmpFlood: 0
})

// 访问控制数据
const whitelist = ref([])
const blacklist = ref([])

// ✅ 动态计算ACL卡片高度（根据显示的条目数）
const aclCardHeight = computed(() => {
  const currentList = activeTab.value === 'whitelist' ? whitelist.value : blacklist.value
  const itemCount = currentList.length || 2 // 至少显示2条的空间
  // 每条ACL项目约72px高度，加上标题、tab、padding等约200px
  const baseHeight = 200
  const itemHeight = 72
  const totalHeight = baseHeight + (itemCount * itemHeight)
  return `${totalHeight}px`
})

// 流量数据
const trafficData = ref({
  labels: [],
  inbound: [],
  outbound: []
})

// 协议分布数据
const protocolData = ref({
  labels: [],
  data: []
})

// ✅ 获取仪表盘数据 - 优化loading显示
const fetchDashboardData = async (silent = false) => {
  // 只在首次加载或手动点击刷新时显示loading
  if (!silent && isFirstLoad.value) {
    isLoading.value = true
  }
  errorMessage.value = ''
  
  try {
    // 使用RYU API获取数据
    const { data: summaryData } = await ryuApi.getSummary()
    const { data: portsData } = await ryuApi.getPorts()
    
    // ✅ 获取attack_sessions数据
    // 注意：为了统计攻击类型分布，需要查询今天的所有数据，不能只取前10条
    let attackSessionsData = []
    let attackSessionsForStats = []  // 用于统计攻击类型的完整数据
    
    try {
      // 显示用：只取最近的10条
      const response = await ryuApi.getAttackSessions(12, 10)
      attackSessionsData = response || []
      console.log('[Dashboard] 成功获取attack_sessions显示数据:', attackSessionsData.length, '条')
      
      // 统计用：查询今天的所有数据（24小时，1000条足够覆盖一天的攻击）
      const statsResponse = await ryuApi.getAttackSessions(24, 1000)
      attackSessionsForStats = statsResponse || []
      console.log('[Dashboard] 成功获取attack_sessions统计数据:', attackSessionsForStats.length, '条')
    } catch (error) {
      console.warn('[Dashboard] attack_sessions API暂不可用，使用anomalies替代:', error)
      // 暂时用anomalies数据，简单去重
      const { data: anomaliesData } = await ryuApi.getAnomalies(24, 1000)
      // 简单去重：按src_ip分组，每个IP只取最新一条
      const groupedByIp = {}
      anomaliesData?.forEach(a => {
        if (!groupedByIp[a.src_ip] || groupedByIp[a.src_ip].timestamp < a.timestamp) {
          groupedByIp[a.src_ip] = a
        }
      })
      attackSessionsData = Object.values(groupedByIp).slice(0, 10)
      attackSessionsForStats = Object.values(groupedByIp)
    }
    
    // ✅ 获取真实流量趋势数据（时间序列）- 今日数据（0点至今）
    let flowTrendData = null
    
    try {
      const response = await ryuApi.getFlowTrend()  // 获取今日数据
      flowTrendData = response.data || []
      console.log('[Dashboard] 流量趋势数据（今日0点至今）:', flowTrendData.length, '个数据点')
    } catch (error) {
      console.warn('获取流量趋势数据失败:', error)
      flowTrendData = []
    }
    
    // 更新状态卡片数据
    switchCount.value = summaryData?.switch_count || 0
    hostCount.value = summaryData?.host_count || 0  // 使用后端返回的真实数据
    anomalyCount.value = summaryData?.today_anomalies || 0  // 这是今日异常数据包数量
    limitedCount.value = summaryData?.limit_count || 0
    
    // ✅ 处理攻击会话数据（attack_sessions表已经去重，直接使用）
    const processedSessions = attackSessionsData?.map(session => ({
      ...session,
      // 确保字段兼容性
      timestamp: session.timestamp || 0,
      type: session.anomaly_type || session.type || '未知攻击',
      // ✅ 正确处理packet_count：NULL表示管理员认定的攻击
      details: session.details || (
        session.packet_count != null 
          ? `${session.packet_count} 个数据包` 
          : '管理员认定'
      )
    })) || []
    
    // 不再过滤任何IP，显示所有攻击会话
    const filteredSessions = processedSessions
    
    // 更新显示数据（无需复杂的去重逻辑，attack_sessions已经是会话级别）
    recentAnomalies.value = filteredSessions
    
    // ✅ 基于今天的所有攻击会话统计攻击类型分布（动态统计所有类型）
    const attackTypeStats = {}
    
    // 统计攻击会话数据 - 使用完整的统计数据而不是只有10条的显示数据
    console.log('[Dashboard] 开始统计攻击类型，数据量:', attackSessionsForStats.length)
    attackSessionsForStats.forEach(session => {
      const type = session.type || session.anomaly_type || '未知攻击'
      attackTypeStats[type] = (attackTypeStats[type] || 0) + 1
    })
    
    console.log('[Dashboard] 攻击类型统计结果:', attackTypeStats)
    
    // 保持原有stats格式用于其他地方（如果有用到）
    const stats = {
      synFlood: attackTypeStats['SYN Flood'] || 0,
      arpSpoof: attackTypeStats['ARP 欺骗'] || attackTypeStats['ARP欺骗'] || 0,
      udpFlood: attackTypeStats['UDP Flood'] || 0,
      icmpFlood: attackTypeStats['ICMP Flood'] || 0
    }
    
    // 更新异常统计数据
    anomalyStats.value = stats
    
    // 获取访问控制列表数据
    await fetchACLData()
    
    // ✅ 处理真实流量趋势数据
    trafficData.value = {
      labels: (flowTrendData || []).map(f => {
        // 从完整时间戳中提取时间（显示HH:MM格式）
        const timeStr = f.time || ''
        const timeParts = timeStr.split(' ')
        return timeParts.length > 1 ? timeParts[1].substring(0, 5) : timeStr
      }),
      inbound: (flowTrendData || []).map(f => f.mbps || 0),
      outbound: (flowTrendData || []).map(f => f.kpps || 0)
    }

    
    // ✅ 协议分布改为攻击类型分布（基于attack_sessions统计，动态显示所有类型）
    const attackTypeLabels = []
    const attackTypeData = []
    
    // ✅ 遍历所有攻击类型（而不是只统计4种固定类型）
    Object.entries(attackTypeStats).forEach(([type, count]) => {
      if (count > 0) {
        attackTypeLabels.push(type)
        attackTypeData.push(count)
      }
    })
    
    protocolData.value = {
      labels: attackTypeLabels,
      data: attackTypeData
    }
    
    console.log('[Dashboard] 攻击类型分布:', { labels: attackTypeLabels, data: attackTypeData, stats: attackTypeStats })
    
    // 更新图表
    updateCharts()
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
    errorMessage.value = `获取数据失败: ${error.message}`
  } finally {
    isLoading.value = false
    isFirstLoad.value = false // ✅ 标记首次加载完成
  }
}

// 获取访问控制数据
const fetchACLData = async () => {
  try {
    const response = await axios.get('/v1/acl')
    const responseData = response.data
    
    // 中间层API返回格式: {success: true, data: {white_list: [...], black_list: [...]}, message: "ok"}
    if (responseData.success && responseData.data) {
      const data = responseData.data
      
      // 处理白名单数据
      if (data.white_list && Array.isArray(data.white_list)) {
        whitelist.value = data.white_list.map(item => ({
          ip: item.ip,
          description: `过期时间: ${item.expire_str || '永不过期'}`,
          status: item.status || 'active'
        }))
      } else {
        whitelist.value = []
      }
      
      // 处理黑名单数据
      if (data.black_list && Array.isArray(data.black_list)) {
        blacklist.value = data.black_list.map(item => ({
          ip: item.ip,
          description: `过期时间: ${item.expire_str || '永不过期'}`,
          status: item.status || 'active'
        }))
      } else {
        blacklist.value = []
      }
    } else {
      // API调用失败或返回错误
      console.warn('访问控制API返回错误:', responseData.message || '未知错误')
      whitelist.value = []
      blacklist.value = []
    }
  } catch (error) {
    console.error('获取访问控制数据失败:', error)
    // 设置默认空数据
    whitelist.value = []
    blacklist.value = []
  }
}

// 跳转功能
const goToAnomalies = () => {
  router.push('/anomalies')
}

const goToACL = () => {
  router.push('/acl')
}

// 样式类方法
const getAnomalyTypeClass = (type) => {
  const classes = {
    'SYN Flood': 'bg-red-100 text-red-700 border border-red-200',
    'ARP 欺骗': 'bg-orange-100 text-orange-700 border border-orange-200',
    'UDP Flood': 'bg-purple-100 text-purple-700 border border-purple-200',
    'ICMP Flood': 'bg-yellow-100 text-yellow-700 border border-yellow-200',
    '黑名单丢弃': 'bg-gray-800 text-white border border-gray-900'
  }
  return classes[type] || 'bg-gray-100 text-gray-600 border border-gray-200'
}

// 获取异常类型图标
const getAnomalyTypeIcon = (type) => {
  const icons = {
    'SYN Flood': 'fas fa-bolt',
    'ARP 欺骗': 'fas fa-user-secret',
    'UDP Flood': 'fas fa-water',
    'ICMP Flood': 'fas fa-broadcast-tower',
    '黑名单丢弃': 'fas fa-ban'
  }
  return icons[type] || 'fas fa-exclamation-triangle'
}

const getStatusClass = (status) => {
  const classes = {
    limited: 'bg-yellow-100 text-yellow-600',
    handled: 'bg-green-100 text-green-600',
    expired: 'bg-gray-100 text-gray-500'
  }
  return classes[status] || 'bg-gray-100 text-gray-600'
}

const getStatusText = (status) => {
  const texts = {
    limited: '已限速',
    handled: '已处理',
    expired: '已过期'
  }
  return texts[status] || '未知'
}

// 更新当前时间
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN')
}

// 格式化时间 - 增强版
const formatTime = (timestamp) => {
  // 处理无效时间戳
  if (!timestamp || isNaN(new Date(timestamp).getTime())) {
    // 返回当前时间而不是"未知时间"
    const now = new Date()
    return now.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit'
    })
  }
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit'
  })
}

// 初始化图表
const initCharts = () => {
  // 确保图表引用存在且是有效的Canvas元素
  if (!trafficChart.value || !protocolChart.value) {
    console.warn('图表引用未找到，延迟初始化')
    return
  }
  
  // 网络流量趋势图
  if (trafficChart.value && trafficChart.value.getContext) {
    // 如果已有实例，先销毁
    if (trafficChartInstance) {
      trafficChartInstance.destroy()
    }
    
    trafficChartInstance = new Chart(trafficChart.value, {
      type: 'line',
      data: {
        labels: trafficData.value.labels || [],
        datasets: [{
          label: '流量 (Mbps)',
          data: trafficData.value.inbound || [],
          borderColor: '#3B82F6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
          fill: true,
          yAxisID: 'y'
        }, {
          label: '数据包 (Kpps)',
          data: trafficData.value.outbound || [],
          borderColor: '#10B981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4,
          fill: true,
          yAxisID: 'y1'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            position: 'top',
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || ''
                if (label) {
                  label += ': '
                }
                label += context.parsed.y
                return label
              }
            }
          }
        },
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            beginAtZero: true,
            title: {
              display: true,
              text: 'Mbps'
            }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            beginAtZero: true,
            title: {
              display: true,
              text: 'Kpps'
            },
            grid: {
              drawOnChartArea: false,
            }
          },
          x: {
            title: {
              display: true,
              text: '时间'
            },
            ticks: {
              autoSkip: true,
              maxTicksLimit: 10,  // ✅ 减少到最多10个标签，避免拥挤
              maxRotation: 0,
              minRotation: 0
            }
          }
        }
      }
    })
  }

  // 攻击类型分布图（✅ 只在有数据时才创建图表）
  if (protocolChart.value && protocolChart.value.getContext && protocolData.value.labels && protocolData.value.labels.length > 0) {
    // 如果已有实例，先销毁
    if (protocolChartInstance) {
      protocolChartInstance.destroy()
    }
    
    // ✅ 为所有攻击类型定义不同的颜色（确保不重复）
    const attackColors = {
      'SYN Flood': '#EF4444',      // 红色
      'UDP Flood': '#A855F7',      // 紫色
      'ICMP Flood': '#FACC15',     // 黄色
      'ARP 欺骗': '#F97316',       // 橙色
      'ARP欺骗': '#F97316',        // 橙色（兼容）
      '异常流量': '#10B981',       // 绿色
      '带宽超限': '#06B6D4',       // 青色
      'Port Scan': '#EC4899',      // 粉色
      'SSH Brute Force': '#8B5CF6', // 紫罗兰色
      'Land Attack': '#F43F5E',    // 玫瑰红
      '手动限制': '#6366F1',       // 蓝色
      '其他原因': '#94A3B8',       // 灰色
      '未知攻击': '#64748B'        // 深灰色
    }
    
    const backgroundColors = protocolData.value.labels.map(label => attackColors[label] || '#6366F1')
    
    protocolChartInstance = new Chart(protocolChart.value, {
      type: 'doughnut',
      data: {
        labels: protocolData.value.labels || [],
        datasets: [{
          data: protocolData.value.data || [],
          backgroundColor: backgroundColors
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
          }
        }
      }
    })
  }
}

// 更新图表数据
const updateCharts = () => {
  if (trafficChartInstance) {
    trafficChartInstance.data.labels = trafficData.value.labels
    trafficChartInstance.data.datasets[0].data = trafficData.value.inbound
    trafficChartInstance.data.datasets[1].data = trafficData.value.outbound
    trafficChartInstance.update()
  }
  
  // ✅ 更新攻击类型分布图（如果图表不存在但有数据，就创建它）
  if (protocolData.value.labels && protocolData.value.labels.length > 0) {
    // 定义颜色映射
    const attackColors = {
      'SYN Flood': '#EF4444',      // 红色
      'UDP Flood': '#A855F7',      // 紫色
      'ICMP Flood': '#FACC15',     // 黄色
      'ARP 欺骗': '#F97316',       // 橙色
      'ARP欺骗': '#F97316',        // 橙色（兼容）
      '异常流量': '#10B981',       // 绿色
      '带宽超限': '#06B6D4',       // 青色
      'Port Scan': '#EC4899',      // 粉色
      'SSH Brute Force': '#8B5CF6', // 紫罗兰色
      'Land Attack': '#F43F5E',    // 玫瑰红
      '手动限制': '#6366F1',       // 蓝色
      '其他原因': '#94A3B8',       // 灰色
      '未知攻击': '#64748B'        // 深灰色
    }
    const backgroundColors = protocolData.value.labels.map(label => attackColors[label] || '#6366F1')
    
    // ✅ 如果图表实例不存在，创建它
    if (!protocolChartInstance && protocolChart.value && protocolChart.value.getContext) {
      console.log('[Dashboard] 创建饼图实例（延迟创建）')
      protocolChartInstance = new Chart(protocolChart.value, {
        type: 'doughnut',
        data: {
          labels: protocolData.value.labels,
          datasets: [{
            data: protocolData.value.data,
            backgroundColor: backgroundColors
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
            }
          }
        }
      })
    } else if (protocolChartInstance) {
      // ✅ 图表已存在，更新数据
      protocolChartInstance.data.labels = protocolData.value.labels
      protocolChartInstance.data.datasets[0].data = protocolData.value.data
      protocolChartInstance.data.datasets[0].backgroundColor = backgroundColors
      protocolChartInstance.update()
    }
  }
}

// ✅ 手动刷新 - 带防抖
let refreshDebounceTimer = null
const handleManualRefresh = () => {
  if (refreshDebounceTimer) {
    return // 防抖：如果正在刷新，忽略重复点击
  }
  
  isLoading.value = true
  fetchDashboardData(false) // 手动刷新显示loading
  
  // 设置2秒防抖
  refreshDebounceTimer = setTimeout(() => {
    refreshDebounceTimer = null
  }, 2000)
}

// ✅ 设置自动刷新 - 优化体验
const setupAutoRefresh = () => {
  if (autoRefresh.value) {
    refreshInterval.value = setInterval(() => {
      fetchDashboardData(true) // ✅ 静默刷新，不显示loading
    }, 30000) // ✅ 改为30秒刷新一次，减少干扰
  } else if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

// 生命周期钩子
onMounted(() => {
  updateTime()
  setInterval(updateTime, 1000)
  
  // 使用 nextTick 确保 DOM 完全加载后再初始化图表
  nextTick(() => {
    // 先初始化空图表，然后加载数据
    initCharts()
    fetchDashboardData().then(() => {
      updateCharts()
      setupAutoRefresh()
    })
  })
})

onUnmounted(() => {
  // 清理定时器
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
  // 销毁图表实例
  if (trafficChartInstance) {
    trafficChartInstance.destroy()
  }
  if (protocolChartInstance) {
    protocolChartInstance.destroy()
  }
});

// 模态框相关状态
const showModal = ref(false);
const modalTitle = ref('');
const modalType = ref(''); // 'blacklist-add', 'whitelist-add', 'confirm'
const modalMessage = ref('');
const confirmAction = ref(null);

// IP输入相关
const ipInput = ref('');
const ipInputError = ref('');

// 显示自定义IP输入模态框
const showIpInputModal = (type) => {
  modalType.value = type;
  modalTitle.value = type === 'blacklist-add' ? '添加IP到黑名单' : '添加IP到白名单';
  ipInput.value = '';
  ipInputError.value = '';
  showModal.value = true;
};

// 显示确认模态框
const showConfirmModal = (message, action) => {
  modalType.value = 'confirm';
  modalTitle.value = '确认操作';
  modalMessage.value = message;
  confirmAction.value = action;
  showModal.value = true;
};

// 验证IP地址格式
const validateIp = (ip) => {
  const ipRegex = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
  if (!ipRegex.test(ip)) {
    return '请输入有效的IP地址格式 (例如: 192.168.1.100)';
  }
  
  // 检查每个部分是否在0-255范围内
  const parts = ip.split('.').map(Number);
  for (const part of parts) {
    if (part < 0 || part > 255) {
      return 'IP地址的每个部分必须在0-255范围内';
    }
  }
  
  return '';
};

// 处理模态框确认
const handleModalConfirm = async () => {
  if (modalType.value === 'blacklist-add' || modalType.value === 'whitelist-add') {
    // 验证IP
    const error = validateIp(ipInput.value);
    if (error) {
      ipInputError.value = error;
      return;
    }
    
    // 根据类型执行添加操作
    if (modalType.value === 'blacklist-add') {
      await performAddToBlacklist(ipInput.value);
    } else {
      await performAddToWhitelist(ipInput.value);
    }
  } else if (modalType.value === 'confirm' && confirmAction.value) {
    // 执行确认操作
    confirmAction.value();
  }
  
  showModal.value = false;
};

// 添加IP到黑名单（实际操作函数）
const performAddToBlacklist = async (ip) => {
  try {
    // ✅ 使用JSON格式发送数据，并添加operator参数
    const response = await axios.post('/v1/acl/black', {
      ip: ip,
      ttl: -1,
      operator: 'admin'  // ✅ 标识为管理员操作，更新attack_sessions
    }, {
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (response.data.success) {
      showNotification(`IP ${ip} 已成功添加到黑名单`, 'success');
      // 重新加载ACL数据
      await fetchACLData();
    } else {
      showNotification(`添加黑名单失败: ${response.data.message || '未知错误'}`, 'error');
    }
  } catch (error) {
    console.error('[ERROR] 添加黑名单失败:', error);
    showNotification(`添加黑名单失败: ${error.response?.data?.message || error.message || '网络错误'}`, 'error');
  }
};

// 从黑名单移除IP
const removeFromBlacklist = async (ip) => {
  showConfirmModal(`确定要从黑名单中移除IP ${ip} 吗？`, async () => {
    try {
      const response = await axios.delete(`/v1/acl/black/${ip}`);
      
      if (response.data.success) {
        showNotification(`IP ${ip} 已从黑名单移除`, 'success');
        // 重新加载ACL数据
        await fetchACLData();
      } else {
        showNotification(`移除黑名单失败: ${response.data.message || '未知错误'}`, 'error');
      }
    } catch (error) {
      console.error('[ERROR] 移除黑名单失败:', error);
      showNotification(`移除黑名单失败: ${error.response?.data?.message || error.message || '网络错误'}`, 'error');
    }
  });
};

// 添加IP到白名单（实际操作函数）
const performAddToWhitelist = async (ip) => {
  try {
    // 使用FormData发送表单数据
    const formData = new FormData();
    formData.append('ip', ip);
    formData.append('ttl', -1);
    
    const response = await axios.post('/v1/acl/white', formData);
    

    
    if (response.data.success) {
      showNotification(`IP ${ip} 已成功添加到白名单`, 'success');
      // 重新加载ACL数据
      await fetchACLData();
    } else {
      showNotification(`添加白名单失败: ${response.data.message || '未知错误'}`, 'error');
    }
  } catch (error) {
    console.error('[ERROR] 添加白名单失败:', error);
    showNotification(`添加白名单失败: ${error.response?.data?.message || error.message || '网络错误'}`, 'error');
  }
};

// 从白名单移除IP
const removeFromWhitelist = async (ip) => {
  showConfirmModal(`确定要从白名单中移除IP ${ip} 吗？`, async () => {
    try {
      const response = await axios.delete(`/v1/acl/white/${ip}`);
      
      if (response.data.success) {
        showNotification(`IP ${ip} 已从白名单移除`, 'success');
        // 重新加载ACL数据
        await fetchACLData();
      } else {
        showNotification(`移除白名单失败: ${response.data.message || '未知错误'}`, 'error');
      }
    } catch (error) {
      console.error('[ERROR] 移除白名单失败:', error);
      showNotification(`移除白名单失败: ${error.response?.data?.message || error.message || '网络错误'}`, 'error');
    }
  });
};

// 显示通知
const showNotification = (message, type = 'info') => {
  // 创建一个临时通知元素
  const notification = document.createElement('div');
  notification.className = `fixed top-4 right-4 px-4 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-300 ease-in-out translate-x-full`;
  
  // 根据类型设置不同的样式
  if (type === 'success') {
    notification.classList.add('bg-green-50', 'text-green-800', 'border', 'border-green-200');
  } else if (type === 'error') {
    notification.classList.add('bg-red-50', 'text-red-800', 'border', 'border-red-200');
  } else {
    notification.classList.add('bg-blue-50', 'text-blue-800', 'border', 'border-blue-200');
  }
  
  notification.innerHTML = `
    <div class="flex items-center">
      <div class="flex-shrink-0">
        ${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}
      </div>
      <div class="ml-3">
        <p class="text-sm font-medium">${message}</p>
      </div>
    </div>
  `;
  
  // 添加到文档
  document.body.appendChild(notification);
  
  // 显示通知
  setTimeout(() => {
    notification.classList.remove('translate-x-full');
  }, 10);
  
  // 3秒后移除通知
  setTimeout(() => {
    notification.classList.add('opacity-0');
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 3000);
};

// 点击函数（供模板使用）
const addToBlacklist = () => {
  showIpInputModal('blacklist-add');
};

const addToWhitelist = () => {
  showIpInputModal('whitelist-add');
};

</script>

<style scoped>
/* Tailwind配置 */
:deep(.text-primary) {
  color: #3B82F6;
}

:deep(.text-secondary) {
  color: #10B981;
}

:deep(.text-warning) {
  color: #F59E0B;
}

:deep(.text-danger) {
  color: #EF4444;
}

:deep(.text-info) {
  color: #6366F1;
}

:deep(.bg-primary) {
  background-color: #3B82F6;
}

:deep(.bg-secondary) {
  background-color: #10B981;
}

:deep(.bg-warning) {
  background-color: #F59E0B;
}

:deep(.bg-danger) {
  background-color: #EF4444;
}

:deep(.bg-info) {
  background-color: #6366F1;
}

/* 自定义样式 */
.card-shadow {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.hover-lift {
  transition: transform 0.2s, box-shadow 0.2s;
}

.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .container {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}

@media (max-width: 768px) {
  .grid-cols-4 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  
  .lg\:col-span-2 {
    grid-column: span 1;
  }
  
  .lg\:grid-cols-3 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .grid-cols-4 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
}

/* ✅ 自定义滚动条样式 */
.anomaly-scroll-container {
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin; /* Firefox */
  scrollbar-color: #cbd5e1 #f1f5f9; /* Firefox */
}

/* Webkit浏览器（Chrome, Safari, Edge） */
.anomaly-scroll-container::-webkit-scrollbar {
  width: 8px;
}

.anomaly-scroll-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.anomaly-scroll-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
  transition: background 0.2s;
}

.anomaly-scroll-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 表格头部固定 */
.anomaly-scroll-container thead {
  position: sticky;
  top: 0;
  background: white;
  z-index: 10;
}
</style>

