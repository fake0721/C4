<template>
  <div class="min-h-screen bg-gray-50 font-inter">
    <!-- 主内容区 -->
    <main class="container mx-auto px-4 py-6">
      <!-- 页面标题与操作区 -->
      <div class="mb-8 flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h2 class="text-[clamp(1.5rem,3vw,2.5rem)] font-bold text-dark">限速管理中心</h2>
          <p class="text-dark-2 mt-1">实时监控和管理网络中的限速规则与历史记录</p>
        </div>
        
        <div class="mt-4 md:mt-0 flex space-x-3">
          <div class="relative">
            <input type="text" placeholder="搜索IP地址..." 
                v-model="searchQuery"
                class="pl-10 pr-4 py-2 rounded-lg border border-light-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all w-full md:w-64">
            <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-dark-2"></i>
          </div>
          
          <button @click="refreshData" class="flex items-center space-x-2 px-4 py-2 rounded-lg bg-light-1 hover:bg-light-2 transition-colors">
            <i class="fa fa-refresh"></i>
            <span>刷新</span>
          </button>
        </div>
      </div>
      
      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="p-6 bg-white rounded-xl shadow-sm stat-card">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-dark-2 text-sm">当前限速数</p>
              <h3 class="text-3xl font-bold mt-2">{{ stats.currentRateLimits }}</h3>
              <p v-if="stats.currentLimitChangePct !== undefined && stats.currentLimitChangePct !== 0" 
                :class="stats.currentLimitChangePct > 0 ? 'text-danger' : 'text-success'" 
                class="text-sm mt-2 flex items-center">
                <i :class="stats.currentLimitChangePct > 0 ? 'fa fa-arrow-up' : 'fa fa-arrow-down'" class="mr-1"></i> 
                较昨日{{ stats.currentLimitChangePct > 0 ? '增加' : '减少' }} {{ Math.abs(stats.currentLimitChangePct) }}%
              </p>
              <p v-else-if="stats.currentLimitChangePct === 0" class="text-dark-2 text-sm mt-2 flex items-center">
                <i class="fa fa-minus mr-1"></i> 与昨日持平
              </p>
              <p v-else class="text-dark-2 text-sm mt-2">暂无对比数据</p>
            </div>
            <div class="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <i class="fa fa-tachometer text-xl"></i>
            </div>
          </div>
        </div>
        
        <div class="p-6 bg-white rounded-xl shadow-sm stat-card">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-dark-2 text-sm">今日新增限速</p>
              <h3 class="text-3xl font-bold mt-2">{{ stats.todayAdded }}</h3>
              <p v-if="stats.todayLimitChangePct !== undefined && stats.todayLimitChangePct !== 0" 
                :class="stats.todayLimitChangePct > 0 ? 'text-danger' : 'text-success'" 
                class="text-sm mt-2 flex items-center">
                <i :class="stats.todayLimitChangePct > 0 ? 'fa fa-arrow-up' : 'fa fa-arrow-down'" class="mr-1"></i> 
                较昨日{{ stats.todayLimitChangePct > 0 ? '增加' : '减少' }} {{ Math.abs(stats.todayLimitChangePct) }}%
              </p>
              <p v-else-if="stats.todayLimitChangePct === 0" class="text-dark-2 text-sm mt-2 flex items-center">
                <i class="fa fa-minus mr-1"></i> 与昨日持平
              </p>
              <p v-else class="text-dark-2 text-sm mt-2">暂无对比数据</p>
            </div>
            <div class="h-12 w-12 rounded-full bg-warning/10 flex items-center justify-center text-warning">
              <i class="fa fa-plus-circle text-xl"></i>
            </div>
          </div>
        </div>
        
        <div class="p-6 bg-white rounded-xl shadow-sm stat-card">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-dark-2 text-sm">主要限速原因</p>
              <h3 class="text-xl font-bold mt-2">{{ getMainReason() }}</h3>
            </div>
            <div class="h-12 w-12 rounded-full bg-secondary/10 flex items-center justify-center text-secondary">
              <i class="fa fa-bar-chart text-xl"></i>
            </div>
          </div>
        </div>
        
        <div class="p-6 bg-white rounded-xl shadow-sm stat-card">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-dark-2 text-sm">高频限速IP</p>
              <h3 class="text-xl font-bold mt-2">{{ getTopIP() }}</h3>
              <p class="text-dark-2 text-sm mt-2">今日被限速 {{ getTopIPCount() }} 次</p>
            </div>
            <div class="h-12 w-12 rounded-full bg-danger/10 flex items-center justify-center text-danger">
              <i class="fa fa-exclamation-triangle text-xl"></i>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 图表区域 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div class="lg:col-span-2 p-6 bg-white rounded-xl shadow-sm">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="font-semibold text-lg">{{ getTrendTitle() }}</h3>
              <p class="text-xs text-dark-2 mt-1">
                <i class="fa fa-chart-line mr-1"></i>
                {{ getTrendDescription() }}
              </p>
            </div>
            <div class="flex space-x-2">
              <button 
                @click="changeChartPeriod('day')" 
                :class="[chartPeriod === 'day' ? 'bg-primary text-white shadow-md' : 'bg-light-1 text-dark-2 hover:bg-light-2', 'px-4 py-2 text-sm rounded-lg transition-all font-medium']">
                <i class="fa fa-calendar mr-1"></i>最近1天
              </button>
              <button 
                @click="changeChartPeriod('3day')" 
                :class="[chartPeriod === '3day' ? 'bg-primary text-white shadow-md' : 'bg-light-1 text-dark-2 hover:bg-light-2', 'px-4 py-2 text-sm rounded-lg transition-all font-medium']">
                <i class="fa fa-calendar mr-1"></i>最近3天
              </button>
              <button 
                @click="changeChartPeriod('week')" 
                :class="[chartPeriod === 'week' ? 'bg-primary text-white shadow-md' : 'bg-light-1 text-dark-2 hover:bg-light-2', 'px-4 py-2 text-sm rounded-lg transition-all font-medium']">
                <i class="fa fa-calendar-check-o mr-1"></i>最近1周
              </button>
            </div>
          </div>
          <div class="h-80 relative">
            <canvas ref="trendChartRef"></canvas>
            <!-- 加载状态 -->
            <div v-if="loading" class="absolute inset-0 bg-white/80 flex items-center justify-center rounded-lg">
              <div class="text-center">
                <i class="fa fa-spinner fa-spin text-3xl text-primary mb-2"></i>
                <p class="text-sm text-dark-2">加载中...</p>
              </div>
            </div>
            <!-- 空数据状态 -->
            <div v-else-if="!trendData || trendData.length === 0" 
                 class="absolute inset-0 bg-gray-50/50 flex items-center justify-center rounded-lg">
              <div class="text-center">
                <i class="fa fa-line-chart text-gray-300 text-4xl mb-3"></i>
                <p class="text-sm text-gray-600 font-medium">暂无趋势数据</p>
                <p class="text-xs text-gray-500 mt-1">{{ getTrendDescription() }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="p-6 bg-white rounded-xl shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-lg">限速原因分布</h3>
            <button 
              v-if="reasonData && reasonData.length > 0"
              @click="toggleReasonStats"
              class="text-sm text-primary hover:text-primary/80 transition-colors flex items-center space-x-1">
              <span>{{ showReasonStats ? '收起统计' : '展开统计' }}</span>
              <i :class="showReasonStats ? 'fa fa-chevron-up' : 'fa fa-chevron-down'"></i>
            </button>
          </div>
          <div class="h-64 mb-4">
            <canvas ref="reasonChartRef"></canvas>
          </div>
          <!-- 数据明细：显示限速原因统计（可折叠） -->
          <transition name="slide-fade">
            <div v-if="showReasonStats && reasonData && reasonData.length > 0" class="mt-4 space-y-2">
              <p class="font-semibold text-dark-2 text-sm mb-3 flex items-center">
                <i class="fa fa-bar-chart mr-2 text-primary"></i>
                限速原因统计（{{ getReasonStatsTitle() }}）
              </p>
              <div v-for="(item, index) in reasonData" :key="index" 
                   class="flex items-center justify-between p-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div class="flex items-center space-x-2">
                  <div class="w-3 h-3 rounded-full" 
                       :style="{ backgroundColor: getReasonColor(item.reason) }"></div>
                  <span class="text-sm text-dark">{{ item.reason }}</span>
                </div>
                <div class="flex items-center space-x-2">
                  <span class="font-medium text-primary">{{ item.count }}</span>
                  <span class="text-xs text-dark-2">次</span>
                </div>
              </div>
            </div>
          </transition>
          <div v-if="!reasonData || reasonData.length === 0" class="mt-4 p-4 bg-gray-50 rounded-lg text-center">
            <i class="fa fa-info-circle text-gray-400 text-2xl mb-2"></i>
            <p class="text-sm text-gray-600">暂无限速原因数据</p>
            <p class="text-xs text-gray-500 mt-1">系统当前没有检测到限速事件</p>
          </div>
        </div>
      </div>
      
      <!-- 限速主机列表（整合当前和历史） -->
      <div class="bg-white rounded-xl shadow-sm overflow-hidden mb-8">
        <div class="p-6 border-b border-light-2">
          <div class="flex items-center justify-between">
            <!-- 标签页切换 -->
            <div class="flex space-x-1 bg-light-1 rounded-lg p-1">
              <button 
                @click="activeTab = 'current'" 
                class="px-4 py-2 rounded-md text-sm font-medium transition-all"
                :class="activeTab === 'current' ? 'bg-white text-primary shadow-sm' : 'text-dark-2 hover:text-dark'">
                当前限速主机
              </button>
              <button 
                @click="activeTab = 'history'" 
                class="px-4 py-2 rounded-md text-sm font-medium transition-all"
                :class="activeTab === 'history' ? 'bg-white text-primary shadow-sm' : 'text-dark-2 hover:text-dark'">
                历史限速主机
              </button>
            </div>
            
            <!-- 操作按钮区域 -->
            <div class="flex space-x-2">
              <!-- 当前限速主机操作按钮 -->
              <div v-if="activeTab === 'current'" class="flex items-center space-x-2">
                <button @click="exportData" class="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-light-1 hover:bg-light-2 transition-colors text-sm">
                  <i class="fa fa-download"></i>
                  <span>导出</span>
                </button>
                <button @click="showAddLimitModal = true" class="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors text-sm">
                  <i class="fa fa-plus"></i>
                  <span>添加限速</span>
                </button>
              </div>
              
              <!-- 历史限速主机操作按钮 -->
              <div v-if="activeTab === 'history'" class="flex items-center space-x-4">
                <div class="flex items-center space-x-2">
                  <label class="text-sm text-dark-2 whitespace-nowrap">选择日期：</label>
                  <input type="date" v-model="historyDate" @change="loadHistoryData" 
                    class="px-3 py-1.5 rounded-lg border border-light-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all">
                </div>
                <button @click="exportHistoryData" class="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-light-1 hover:bg-light-2 transition-colors text-sm">
                  <i class="fa fa-download"></i>
                  <span>导出历史</span>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 当前限速主机内容 -->
        <div v-if="activeTab === 'current'" class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="bg-light-1">
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">IP地址</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">限速原因</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">限速值</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">开始时间</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">剩余时间</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">状态</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-light-2">
              <tr v-for="(host, index) in filteredHosts" :key="index" class="hover:bg-light-1/50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div class="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary mr-3">
                      <i class="fa fa-desktop"></i>
                    </div>
                    <div>
                      <div class="font-medium text-dark">{{ getHostName(host.ip) }}</div>
                      <div class="text-xs text-dark-2">{{ host.ip }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 py-1 text-xs rounded-full" :class="getReasonClass(host.reason)">
                    {{ host.reason || '自动检测' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="font-medium">{{ host.kbps || 1024 }} Kbps</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-dark-2">
                  {{ formatDateTime(host.createdAt) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="w-32 bg-light-1 rounded-full h-2">
                    <div class="h-full rounded-full" :style="{
                      width: `${host.ttl_left ? Math.max(0, Math.min(100, (host.ttl_left / 300) * 100)) : getTimePercentage(host.createdAt, host.expireAt)}%`,
                      background: host.ttl_left ? getTimeBarColor(Math.max(0, Math.min(100, (host.ttl_left / 300) * 100))) : getTimeBarColor(getTimePercentage(host.createdAt, host.expireAt))
                    }"></div>
                  </div>
                  <div class="text-xs text-dark-2 mt-1">{{ host.ttl_left ? `${host.ttl_left}秒` : calculateRemainingTime(host.expireAt) }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 py-1 text-xs rounded-full" :class="getStatusClass(getHostStatus(host))">
                    {{ getHostStatus(host) }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <div class="flex items-center space-x-2">
                    <!-- 编辑按钮 -->
                    <button @click="editHost(host)" 
                      class="px-3 py-1 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors text-xs font-medium"
                      title="编辑限速规则">
                      编辑
                    </button>
                    <!-- 解除限速按钮 -->
                    <button @click="releaseHost(host)" 
                      class="px-3 py-1 rounded-lg bg-success text-white hover:bg-success/90 transition-colors text-xs font-medium"
                      title="解除限速">
                      解除
                    </button>
                    <!-- 封禁主机按钮 -->
                    <button @click="blockHost(host)" 
                      class="px-3 py-1 rounded-lg bg-danger text-white hover:bg-danger/90 transition-colors text-xs font-medium"
                      title="封禁主机">
                      封禁
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="filteredHosts.length === 0">
                <td colspan="7" class="px-6 py-10 text-center text-dark-2">
                  <i class="fa fa-check-circle text-success text-3xl mb-3"></i>
                  <p>当前没有限速主机</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- 历史限速主机内容 -->
        <div v-if="activeTab === 'history'" class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="bg-light-1">
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">IP地址</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">操作类型</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">原因</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">限速值</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">操作时间</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-dark-2 uppercase tracking-wider">操作者</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-light-2">
              <tr v-for="(record, index) in paginatedRecords" :key="index" class="hover:bg-light-1/50 transition-colors">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div class="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 mr-3">
                      <i class="fa fa-history"></i>
                    </div>
                    <div>
                      <div class="font-medium text-dark">{{ getHostName(record.src_ip) }}</div>
                      <div class="text-xs text-dark-2">{{ record.src_ip }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 py-1 text-xs rounded-full" :class="getActionClass(record.action)">
                    {{ getActionText(record.action) }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                    {{ record.reason || '未知' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="font-medium">{{ record.kbps || '-' }} Kbps</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-dark-2">
                  {{ formatDateTime(record.created_at) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-sm text-dark-2">{{ record.operator || '系统' }}</span>
                </td>
              </tr>
              <tr v-if="historyRecords.length === 0">
                <td colspan="6" class="px-6 py-10 text-center text-dark-2">
                  <i class="fa fa-clock text-gray-400 text-3xl mb-3"></i>
                  <p>{{ historyDate ? `${historyDate} 没有历史限速记录` : '请选择日期查看历史限速记录' }}</p>
                </td>
              </tr>
            </tbody>
          </table>
           
           <!-- 分页控件 -->
           <div v-if="historyRecords.length > 0" class="mt-6 flex justify-between items-center">
             <div class="text-sm text-dark-2">
               显示 {{ (currentPage - 1) * pageSize + 1 }} 至 {{ Math.min(currentPage * pageSize, historyRecords.length) }} 条，
               共 {{ historyRecords.length }} 条记录
             </div>
             <div class="flex space-x-2">
               <button 
                 @click="goToPreviousPage" 
                 :disabled="currentPage <= 1"
                 class="px-3 py-2 rounded-lg border border-light-2 text-dark-2 hover:border-primary hover:text-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
               >
                 <i class="fa fa-chevron-left"></i> 上一页
               </button>
               <div class="flex items-center space-x-1">
                 <span class="text-sm text-dark-2">第</span>
                 <span class="font-medium">{{ currentPage }}</span>
                 <span class="text-sm text-dark-2">页 / 共</span>
                 <span class="font-medium">{{ totalPages }}</span>
                 <span class="text-sm text-dark-2">页</span>
               </div>
               <button 
                 @click="goToNextPage" 
                 :disabled="currentPage >= totalPages"
                 class="px-3 py-2 rounded-lg border border-light-2 text-dark-2 hover:border-primary hover:text-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
               >
                 下一页 <i class="fa fa-chevron-right"></i>
               </button>
             </div>
           </div>
        </div>
      </div>
    </main>
    
    <!-- 添加限速模态框 -->
    <div v-if="showAddLimitModal" class="fixed inset-0 bg-dark/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-lg w-full max-w-md p-6 m-4">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-lg font-semibold">添加限速规则</h3>
          <button @click="showAddLimitModal = false" class="text-dark-2 hover:text-dark transition-colors">
            <i class="fa fa-times"></i>
          </button>
        </div>
        
        <form @submit.prevent="addLimitRule">
          <div class="mb-4">
            <label class="block text-dark-2 text-sm font-medium mb-2">IP地址</label>
            <input type="text" v-model="newLimitForm.ip" placeholder="192.168.1.1" 
              class="w-full px-4 py-2 rounded-lg border border-light-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all">
          </div>
          
          <div class="mb-4">
            <label class="block text-dark-2 text-sm font-medium mb-2">限速原因</label>
            <select v-model="newLimitForm.reason" 
              @change="onReasonChange"
              class="w-full px-4 py-2 rounded-lg border border-light-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              style="max-height: 200px; overflow-y: auto;">
              <option value="">请选择原因</option>
              <option value="SYN Flood">SYN Flood</option>
              <option value="UDP Flood">UDP Flood</option>
              <option value="ICMP Flood">ICMP Flood</option>
              <option value="ARP 欺骗">ARP 欺骗</option>
              <option value="带宽超限">带宽超限</option>
              <option value="异常流量">异常流量</option>
              <option value="手动限制">手动限制</option>
              <option value="其他原因">其他原因</option>
            </select>
          </div>
          
          <!-- 自定义原因输入框（选择"其他原因"时显示） -->
          <div v-if="newLimitForm.reason === '其他原因'" class="mb-4">
            <label class="block text-dark-2 text-sm font-medium mb-2">请输入原因</label>
            <input type="text" v-model="newLimitForm.customReason" 
              placeholder="请输入自定义的限速原因"
              class="w-full px-4 py-2 rounded-lg border border-light-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all">
          </div>
          
          <div class="mb-4">
            <label class="block text-dark-2 text-sm font-medium mb-2">限速档位</label>
            <select v-model.number="newLimitForm.kbps" 
              class="w-full px-4 py-2 rounded-lg border border-light-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all">
              <option :value="256">低速 - 256 Kbps</option>
              <option :value="1024">中速 - 1024 Kbps (1 Mbps)</option>
              <option :value="2048">高速 - 2048 Kbps (2 Mbps)</option>
            </select>
            <p class="text-xs text-gray-500 mt-1">请选择限速档位（对应QoS队列）</p>
          </div>
          
          <!-- ✅ 新增：限速时长 -->
          <div class="mb-4">
            <label class="block text-dark-2 text-sm font-medium mb-2">限速时长（分钟）</label>
            <input type="number" v-model="newLimitForm.durationMinutes" min="1" step="1" 
              placeholder="默认5分钟"
              class="w-full px-4 py-2 rounded-lg border border-light-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all">
            <p class="text-xs text-gray-500 mt-1">设置限速持续时间，默认5分钟</p>
          </div>
          
          <div class="flex justify-end space-x-3 mt-6">
            <button type="button" @click="showAddLimitModal = false" 
              class="px-4 py-2 rounded-lg bg-light-1 hover:bg-light-2 transition-colors">
              取消
            </button>
            <button type="submit" 
              class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors">
              添加
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- 编辑限速模态框 -->
    <div v-if="showEditModal" class="fixed inset-0 bg-dark/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-lg w-full max-w-md p-6 m-4">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-lg font-semibold">编辑限速规则</h3>
          <button @click="showEditModal = false" class="text-dark-2 hover:text-dark transition-colors">
            <i class="fa fa-times"></i>
          </button>
        </div>
        
        <form @submit.prevent="updateLimitRule">
          <div class="mb-4">
            <label class="block text-dark-2 text-sm font-medium mb-2">IP地址</label>
            <input type="text" v-model="editLimitForm.ip" disabled
              class="w-full px-4 py-2 rounded-lg border border-light-2 bg-gray-100">
          </div>
          
          <div class="mb-4">
            <label class="block text-dark-2 text-sm font-medium mb-2">限速档位</label>
            <select v-model.number="editLimitForm.kbps" 
              class="w-full px-4 py-2 rounded-lg border border-light-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all">
              <option :value="256">低速 - 256 Kbps</option>
              <option :value="1024">中速 - 1024 Kbps (1 Mbps)</option>
              <option :value="2048">高速 - 2048 Kbps (2 Mbps)</option>
            </select>
            <p class="text-xs text-gray-500 mt-1">请选择限速档位（对应QoS队列）</p>
          </div>
          
          <!-- ✅ 新增：修改限速时间 -->
          <div class="mb-4">
            <label class="block text-dark-2 text-sm font-medium mb-2">调整限速时间</label>
            <div class="flex space-x-2">
              <select v-model="editLimitForm.timeAdjustType" 
                class="w-1/3 px-4 py-2 rounded-lg border border-light-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all">
                <option value="extend">延长</option>
                <option value="shorten">缩短</option>
              </select>
              <input type="number" v-model="editLimitForm.timeAdjustMinutes" min="0" step="1" 
                placeholder="分钟数"
                class="flex-1 px-4 py-2 rounded-lg border border-light-2 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all">
              <span class="flex items-center px-2 text-dark-2 text-sm">分钟</span>
            </div>
            <p class="text-xs text-gray-500 mt-1">留空则不调整时间，仅修改速率</p>
          </div>
          
          <div class="flex justify-end space-x-3 mt-6">
            <button type="button" @click="showEditModal = false" 
              class="px-4 py-2 rounded-lg bg-light-1 hover:bg-light-2 transition-colors">
              取消
            </button>
            <button type="submit" 
              class="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors">
              更新
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- 解除限速确认模态框 -->
    <div v-if="showReleaseModal" class="fixed inset-0 bg-dark/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-lg w-full max-w-sm p-6 m-4">
        <div class="text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-warning/10 mb-4">
            <i class="fa fa-exclamation-triangle text-warning text-xl"></i>
          </div>
          <h3 class="text-lg font-medium text-dark mb-2">确认解除限速</h3>
          <p class="text-dark-2 mb-6">确定要解除对 {{ currentHost?.ip }} 的限速吗？</p>
          <div class="flex space-x-3 justify-center">
            <button @click="showReleaseModal = false" 
              class="px-4 py-2 rounded-lg bg-light-1 hover:bg-light-2 transition-colors">
              取消
            </button>
            <button @click="confirmRelease" 
              class="px-4 py-2 rounded-lg bg-success text-white hover:bg-success/90 transition-colors">
              确认解除
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 封禁主机确认模态框 -->
    <div v-if="showBlockModal" class="fixed inset-0 bg-dark/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-lg w-full max-w-sm p-6 m-4">
        <div class="text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-danger/10 mb-4">
            <i class="fa fa-ban text-danger text-xl"></i>
          </div>
          <h3 class="text-lg font-medium text-dark mb-2">确认封禁主机</h3>
          <p class="text-dark-2 mb-6">确定要封禁 {{ currentHost?.ip }} 吗？该主机将被加入黑名单。</p>
          <div class="flex space-x-3 justify-center">
            <button @click="showBlockModal = false" 
              class="px-4 py-2 rounded-lg bg-light-1 hover:bg-light-2 transition-colors">
              取消
            </button>
            <button @click="confirmBlock" 
              class="px-4 py-2 rounded-lg bg-danger text-white hover:bg-danger/90 transition-colors">
              确认封禁
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import Chart from 'chart.js/auto'
import ryuAPI from '@/api/ryu'

// 页面状态变量
const searchQuery = ref('')
const chartPeriod = ref('day')  // 默认显示最近1天
const showAddLimitModal = ref(false)
const showEditModal = ref(false)
const showReleaseModal = ref(false)
const showBlockModal = ref(false)
const loading = ref(false)
const historyDate = ref('')
const activeTab = ref('current') // 当前激活的标签页：'current' 或 'history'
const showReasonStats = ref(true) // 控制限速原因统计的显示/隐藏

// 统计数据
const stats = ref({
  currentRateLimits: 0,
  currentLimitChangePct: 0,
  todayAdded: 0,
  todayLimitChangePct: 0,
  todayReleased: 0,
  totalRateLimits: 0,
  blackCount: 0,
  whiteCount: 0,
  switchCount: 0
})

// 限速主机数据
const limitedHosts = ref([])
const filteredHosts = computed(() => {
  if (!Array.isArray(limitedHosts.value)) return []
  if (!searchQuery.value) return limitedHosts.value
  return limitedHosts.value.filter(host => 
    host.ip.includes(searchQuery.value) || 
    host.reason.includes(searchQuery.value)
  )
})

// 历史限速记录数据
const historyRecords = ref([])

// 历史数据统计信息
const historyStats = ref({
  totalRecords: 0,
  uniqueIPs: 0,
  limitActions: 0,
  releaseActions: 0,
  duplicateCount: 0
})

// 分页相关状态
const currentPage = ref(1)
const pageSize = ref(10) // 每页显示10条记录
const totalPages = ref(0)
const paginatedRecords = ref([]) // 当前页显示的数据

// 图表数据
const trendData = ref([])
const reasonData = ref([])  // 用户选择的图表时间范围的数据
const todayReasonData = ref([])  // 今天的限速原因数据（用于卡片显示）
const topIPData = ref({ ip: '', count: 0 })

// 图表引用
const trendChartRef = ref(null)
const reasonChartRef = ref(null)
let trendChart = null
let reasonChart = null

// 切换图表周期
const changeChartPeriod = async (period) => {
  console.log('='.repeat(60))
  console.log('[图表周期] ⚡ 用户点击切换按钮:', period)
  console.log('[图表周期] 当前周期:', chartPeriod.value)
  
  if (chartPeriod.value === period) {
    console.log('[图表周期] ⚠️ 已经是当前周期，无需切换')
    return
  }
  
  chartPeriod.value = period
  console.log('[图表周期] ✅ 周期已切换为:', period)
  
  // 根据周期重新加载图表数据
  try {
    loading.value = true
    
    // 将前端周期映射为后端type参数和小时数
    let apiType = 1
    let hours = 24
    if (period === 'day') {
      apiType = 1  // 24小时
      hours = 24
    } else if (period === '3day') {
      apiType = 3  // 3天
      hours = 72   // 3 * 24
    } else if (period === 'week') {
      apiType = 7  // 7天
      hours = 168  // 7 * 24
    }
    
    console.log(`[图表周期] 📡 准备发送请求: apiType=${apiType}, hours=${hours}`)
    
    // 1. 获取趋势数据
    console.log('[图表周期] 🔄 正在调用 ryuAPI.getRateTrend...')
    const trendResponse = await ryuAPI.getRateTrend(apiType)
    console.log('[图表周期] ✅ 趋势数据API响应成功')
    console.log('[图表周期] 响应数据:', trendResponse)
    
    // 处理API响应格式
    if (trendResponse && trendResponse.success && Array.isArray(trendResponse.data)) {
      trendData.value = trendResponse.data
      console.log('[图表周期] 成功获取趋势数据，数据量:', trendData.value.length)
    } else if (Array.isArray(trendResponse)) {
      trendData.value = trendResponse
      console.log('[图表周期] 成功获取趋势数据（直接数组），数据量:', trendData.value.length)
    } else {
      console.warn('[图表周期] 获取到的趋势数据格式不正确')
      trendData.value = []
    }
    
    // 2. 同步更新饼图数据 - 使用相同的时间范围
    console.log('[图表周期] 🔄 正在调用 ryuAPI.getRateReasonStats, hours=', hours)
    const reasonResponse = await ryuAPI.getRateReasonStats(hours)
    console.log('[图表周期] ✅ 饼图数据API响应成功')
    console.log('[图表周期] 响应数据:', reasonResponse)
    
    if (reasonResponse && reasonResponse.success && Array.isArray(reasonResponse.data)) {
      reasonData.value = reasonResponse.data
      console.log('[图表周期] 成功更新饼图数据，数据量:', reasonData.value.length)
    } else if (Array.isArray(reasonResponse)) {
      reasonData.value = reasonResponse
      console.log('[图表周期] 成功更新饼图数据（直接数组），数据量:', reasonData.value.length)
    } else {
      console.warn('[图表周期] 饼图数据格式不正确')
    }
    
    // 3. 等待DOM更新后再更新图表
    await nextTick()
    updateCharts()
    
    console.log('[图表周期] 图表数据已更新为', period, '周期，时间范围:', hours, '小时')
  } catch (error) {
    console.error('[图表周期] 切换图表周期失败:', error)
    trendData.value = []
    await nextTick()
    updateCharts()
  } finally {
    loading.value = false
  }
}

// 添加限速表单
const newLimitForm = ref({
  ip: '',
  reason: '',
  customReason: '',  // ✅ 自定义原因输入框的值
  kbps: 1024,
  durationMinutes: 5  // ✅ 限速时长（分钟），默认5分钟
})

// 编辑限速表单（不再包含reason字段）
const editLimitForm = ref({
  ip: '',
  kbps: 1024,
  timeAdjustType: 'extend',  // ✅ 时间调整类型：extend(延长) / shorten(缩短)
  timeAdjustMinutes: null    // ✅ 调整的分钟数
})

// 当前操作的主机
const currentHost = ref(null)

// 刷新数据
const refreshData = async () => {
  console.log('[刷新数据] 开始刷新限速页面数据...')
  await loadRateLimitData()
  console.log('[刷新数据] 数据刷新完成')
}

// 切换限速原因统计的显示/隐藏
const toggleReasonStats = () => {
  showReasonStats.value = !showReasonStats.value
  console.log('[限速原因统计] 切换显示状态:', showReasonStats.value ? '展开' : '收起')
}

// 获取趋势图标题
const getTrendTitle = () => {
  const titles = {
    'day': '限速趋势（今天）',
    '3day': '限速趋势（最近3天）',
    'week': '限速趋势（最近7天）'
  }
  return titles[chartPeriod.value] || '限速趋势'
}

// 获取趋势图描述
const getTrendDescription = () => {
  const descriptions = {
    'day': '今天每小时新增限速会话统计',
    '3day': '最近3天每天新增限速会话统计',
    'week': '最近7天每天新增限速会话统计'
  }
  return descriptions[chartPeriod.value] || '限速会话统计'
}

// 获取X轴标签
const getXAxisLabel = () => {
  const labels = {
    'day': '时间',
    '3day': '日期',
    'week': '日期'
  }
  return labels[chartPeriod.value] || '时间'
}

// 获取饼图统计标题
const getReasonStatsTitle = () => {
  const titles = {
    'day': '今天',
    '3day': '最近3天',
    'week': '最近7天'
  }
  return titles[chartPeriod.value] || '今天'
}

// 辅助函数
const formatDateTime = (date) => {
  return new Date(date).toLocaleString('zh-CN')
}

// 数据分析和去重函数
const analyzeAndDeduplicateHistoryData = (data) => {
  if (!Array.isArray(data) || data.length === 0) {
    return {
      uniqueRecords: [],
      statistics: {
        totalRecords: 0,
        uniqueIPs: 0,
        limitActions: 0,
        releaseActions: 0,
        duplicateCount: 0
      }
    }
  }
  
  // 统计信息
  const statistics = {
    totalRecords: data.length,
    uniqueIPs: 0,
    limitActions: 0,
    releaseActions: 0,
    duplicateCount: 0
  }
  
  // 按IP地址和攻击类型组合分组，找出重复记录
  const ipReasonGroups = {}
  data.forEach(record => {
    const ip = record.src_ip
    const reason = record.reason || '未知原因'
    const groupKey = `${ip}_${reason}` // 组合键：IP_攻击类型
    
    if (!ipReasonGroups[groupKey]) {
      ipReasonGroups[groupKey] = []
    }
    ipReasonGroups[groupKey].push(record)
  })
  
  // 去重逻辑：对于每个IP和攻击类型组合，只保留最新的记录
  const uniqueRecords = []
  Object.entries(ipReasonGroups).forEach(([groupKey, records]) => {
    // 按时间排序，最新的在前
    const sortedRecords = records.sort((a, b) => {
      const timeA = new Date(a.created_at).getTime()
      const timeB = new Date(b.created_at).getTime()
      return timeB - timeA
    })
    
    // 只保留最新的记录
    uniqueRecords.push(sortedRecords[0])
    
    // 统计重复数量
    statistics.duplicateCount += (records.length - 1)
  })
  
  // 统计唯一IP数量（基于IP地址，不考虑攻击类型）
  const uniqueIPs = new Set()
  uniqueRecords.forEach(record => {
    uniqueIPs.add(record.src_ip)
  })
  statistics.uniqueIPs = uniqueIPs.size
  
  // 统计操作类型
  uniqueRecords.forEach(record => {
    if (record.action === 'limit' || record.action === 'block') {
      statistics.limitActions++
    } else if (record.action === 'release' || record.action === 'unlimit') {
      statistics.releaseActions++
    }
  })
  
  return {
    uniqueRecords,
    statistics
  }
}

const calculateRemainingTime = (expireAt) => {
  const now = new Date()
  // 修复时间格式问题：RYU返回"2025-10-20 15:42:30"格式，需要将空格替换为'T'变成ISO格式
  const isoExpireAt = expireAt.replace(' ', 'T')
  const expire = new Date(isoExpireAt)
  const diff = expire - now
  if (diff <= 0) return '已过期'
  
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  return `${hours}小时${minutes}分钟`
}

const getTimePercentage = (startAt, expireAt) => {
  // 修复时间格式问题：RYU返回"2025-10-20 15:42:30"格式，需要将空格替换为'T'变成ISO格式
  const isoStartAt = startAt.replace(' ', 'T')
  const isoExpireAt = expireAt.replace(' ', 'T')
  const start = new Date(isoStartAt).getTime()
  const expire = new Date(isoExpireAt).getTime()
  const now = new Date().getTime()
  const total = expire - start
  const elapsed = now - start
  
  if (elapsed >= total) return 100
  if (elapsed <= 0) return 0
  
  return Math.round((elapsed / total) * 100)
}

const getTimeBarColor = (percentage) => {
  if (percentage >= 80) return '#ef4444'
  if (percentage >= 60) return '#f59e0b'
  return '#10b981'
}

const getHostStatus = (host) => {
  // ✅ 优先使用RYU返回的ttl_left字段判断（更准确）
  if (host.ttl_left !== undefined && host.ttl_left !== null) {
    return host.ttl_left > 0 ? '限速中' : '已过期'
  }
  
  // 备用方案：使用expireAt时间戳判断
  const now = new Date()
  // 修复时间格式问题：RYU返回"2025-10-20 15:42:30"格式，需要将空格替换为'T'变成ISO格式
  const isoExpireAt = host.expireAt.replace(' ', 'T')
  const expire = new Date(isoExpireAt)
  return now < expire ? '限速中' : '已过期'
}

const getReasonClass = (reason) => {
  const classes = {
    'SYN Flood': 'bg-red-100 text-red-800',
    'UDP Flood': 'bg-orange-100 text-orange-800',
    'ICMP Flood': 'bg-green-100 text-green-800',
    'ARP Spoof': 'bg-blue-100 text-blue-800',
    'Botnet': 'bg-purple-100 text-purple-800',
    '带宽超限': 'bg-pink-100 text-pink-800',
    '异常流量': 'bg-orange-100 text-orange-800',
    '手动限制': 'bg-indigo-100 text-indigo-800'
  }
  return classes[reason] || 'bg-gray-100 text-gray-800'
}

const getReasonColor = (reason) => {
  const colorMap = {
    'SYN Flood': '#ef4444',      // 红色
    'UDP Flood': '#f59e0b',      // 橙色
    'ICMP Flood': '#10b981',     // 绿色
    'ARP Spoof': '#3b82f6',      // 蓝色
    'Botnet': '#8b5cf6',         // 紫色
    '带宽超限': '#ec4899',        // 粉色
    '异常流量': '#f97316',        // 深橙色
    '手动限制': '#6366f1',        // 靛蓝色
    '暂无数据': '#d1d5db'         // 灰色
  }
  return colorMap[reason] || '#94a3b8' // 默认灰蓝色
}

const getStatusClass = (status) => {
  const classes = {
    '限速中': 'bg-green-100 text-green-800',
    '已过期': 'bg-gray-100 text-gray-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

const getHostName = (ip) => {
  // 这里可以添加实际的IP到主机名的映射逻辑
  // 目前返回IP地址本身，或者可以根据需要从API获取主机名信息
  return ip
}

// 统计卡片辅助函数
const getMainReason = () => {
  // 卡片应该显示今天的数据，使用 todayReasonData
  if (todayReasonData.value && Array.isArray(todayReasonData.value) && todayReasonData.value.length > 0) {
    // 如果今天有限速原因数据，使用第一个原因（按次数排序，最多的在前）
    const firstReason = todayReasonData.value[0]
    return firstReason.reason || '未知原因'
  }
  
  // 如果今天没有数据，返回"无数据"
  return '无数据'
}

const getMainReasonPercentage = () => {
  // 优先使用从后端API获取的reasonData
  if (reasonData.value && Array.isArray(reasonData.value) && reasonData.value.length > 0) {
    // 如果后端返回了主要限速原因数据，使用第一个原因的占比
    const firstReason = reasonData.value[0]
    return firstReason.percentage || Math.round((firstReason.count || 1) / (Array.isArray(limitedHosts.value) ? limitedHosts.value.length : 1) * 100)
  }
  
  // 如果后端数据为空，使用前端计算逻辑
  if (!Array.isArray(limitedHosts.value) || limitedHosts.value.length === 0) return 0
  
  const reasonCounts = {}
  if (Array.isArray(limitedHosts.value)) {
    limitedHosts.value.forEach(host => {
      reasonCounts[host.reason] = (reasonCounts[host.reason] || 0) + 1
    })
  }
  
  const mainReason = getMainReason()
  return Math.round((reasonCounts[mainReason] || 0) / (Array.isArray(limitedHosts.value) ? limitedHosts.value.length : 1) * 100)
}

const getTopIP = () => {
  // 卡片应该显示今天的数据，优先使用从后端API获取的topIPData
  if (topIPData.value && topIPData.value.ip && topIPData.value.count > 0) {
    return topIPData.value.ip
  }
  
  // 如果后端数据为空，返回"无数据"
  return '无数据'
}

const getTopIPCount = () => {
  // 卡片应该显示今天的数据，优先使用从后端API获取的topIPData
  if (topIPData.value && topIPData.value.count > 0) {
    return topIPData.value.count
  }
  
  // 如果后端数据为空，返回0
  return 0
}

// 更新统计数据
const updateStats = () => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  const todayAdded = Array.isArray(limitedHosts.value) ? limitedHosts.value.filter(host => {
    const hostDate = new Date(host.createdAt)
    return hostDate >= today
  }).length : 0
  
  const totalCount = Array.isArray(limitedHosts.value) ? limitedHosts.value.length : 0
  
  stats.value = {
    currentRateLimits: totalCount,
    todayAdded: todayAdded,
    todayReleased: 0, // 需要从历史数据计算
    totalRateLimits: totalCount, // 简化处理
    blackCount: 0, // 需要从API获取
    whiteCount: 0, // 需要从API获取
    switchCount: 0 // 需要从API获取
  }
  
  // 调试信息：显示当前限速主机数量
  console.log(`[DEBUG] 当前限速主机数量: ${totalCount}, 今日新增: ${todayAdded}`)
  
  // 如果当前没有限速数据，显示提示信息
  if (totalCount === 0) {
    console.log('[INFO] 当前没有活跃的限速主机，系统正常运行中')
  }
}

// API调用函数
const loadRateLimitData = async () => {
  try {
    loading.value = true
    console.log('[数据刷新] 开始加载限速数据...')
    
    // 三层API结构调用：前端 → 后端API层 → RYU控制器
    
    // 1. 获取当前限速列表 - 通过后端API层代理到RYU控制器
    const rateLimitResponse = await ryuAPI.getRateLimit()
    console.log('[数据刷新] 限速列表API响应:', rateLimitResponse)
    
    // 处理三层API结构返回的数据格式
    if (rateLimitResponse.success && rateLimitResponse.data) {
      // 后端API层返回的数据结构：{success: true, data: {limit_list: [...]}, message: "ok"}
      const rawData = rateLimitResponse.data.limit_list || []
      console.log('[数据刷新] 解析后端数据 (格式1):', rawData)
      // 转换数据结构：使用RYU控制器返回的实际原因字段
      limitedHosts.value = rawData.map(item => {
        console.log(`[数据刷新] 处理IP ${item.ip}: kbps=${item.kbps}, reason=${item.reason}`)
        return {
          ip: item.ip,
          ttl_left: item.ttl_left,
          reason: item.reason || '系统检测', // 使用实际原因，如果没有则显示"系统检测"
          kbps: item.kbps || 1024, // 使用实际速率，如果没有则显示1024
          createdAt: item.start_time || new Date().toISOString().replace('T', ' ').slice(0, 19), // 使用实际开始时间
          expireAt: new Date(Date.now() + (item.ttl_left || 0) * 1000).toISOString().replace('T', ' ').slice(0, 19) // 根据ttl_left计算过期时间
        }
      })
    } else if (Array.isArray(rateLimitResponse)) {
      // 直接RYU控制器返回的数据结构：[...]
      console.log('[数据刷新] 解析RYU数据 (格式2):', rateLimitResponse)
      limitedHosts.value = rateLimitResponse.map(item => {
        console.log(`[数据刷新] 处理IP ${item.ip}: kbps=${item.kbps}, reason=${item.reason}`)
        return {
          ip: item.ip,
          ttl_left: item.ttl_left,
          reason: item.reason || '系统检测', // 使用实际原因，如果没有则显示"系统检测"
          kbps: item.kbps || 1024, // 使用实际速率，如果没有则显示1024
          createdAt: item.start_time || new Date().toISOString().replace('T', ' ').slice(0, 19), // 使用实际开始时间
          expireAt: new Date(Date.now() + (item.ttl_left || 0) * 1000).toISOString().replace('T', ' ').slice(0, 19) // 根据ttl_left计算过期时间
        }
      })
    } else {
      // 其他格式，使用默认值
      const rawData = rateLimitResponse.limit_list || []
      console.log('[数据刷新] 解析其他格式数据 (格式3):', rawData)
      limitedHosts.value = rawData.map(item => {
        console.log(`[数据刷新] 处理IP ${item.ip}: kbps=${item.kbps}, reason=${item.reason}`)
        return {
          ip: item.ip,
          ttl_left: item.ttl_left,
          reason: item.reason || '系统检测', // 使用实际原因，如果没有则显示"系统检测"
          kbps: item.kbps || 1024, // 使用实际速率，如果没有则显示1024
          createdAt: item.start_time || new Date().toISOString().replace('T', ' ').slice(0, 19), // 使用实际开始时间
          expireAt: new Date(Date.now() + (item.ttl_left || 0) * 1000).toISOString().replace('T', ' ').slice(0, 19) // 根据ttl_left计算过期时间
        }
      })
    }
    console.log('[数据刷新] 最终limitedHosts:', limitedHosts.value)
    
    // 2. 获取系统概览数据 - 通过后端API层
    const summaryResponse = await ryuAPI.getSummary()
    console.log('系统概览API响应:', summaryResponse)
    
    // 处理三层API结构返回的数据格式
    const summaryData = summaryResponse.success ? summaryResponse.data : summaryResponse
    
    stats.value = {
      currentRateLimits: Array.isArray(limitedHosts.value) ? limitedHosts.value.length : 0,
      todayAdded: 0, // 需要从历史数据计算
      todayReleased: 0, // 需要从历史数据计算
      totalRateLimits: Array.isArray(limitedHosts.value) ? limitedHosts.value.length : 0, // 简化处理
      blackCount: summaryData.black_count || 0,
      whiteCount: summaryData.white_count || 0,
      switchCount: summaryData.switch_count || 0
    }
    
    // 3. 获取限速趋势数据 - 根据当前选择的图表周期获取数据
    let apiType = 1
    let hours = 24
    if (chartPeriod.value === 'day') {
      apiType = 1  // 24小时
      hours = 24
    } else if (chartPeriod.value === '3day') {
      apiType = 3  // 3天
      hours = 72
    } else if (chartPeriod.value === 'week') {
      apiType = 7  // 7天
      hours = 168
    }
    
    console.log(`[数据加载] 根据当前周期 ${chartPeriod.value} 获取数据: apiType=${apiType}, hours=${hours}`)
    
    const trendResponse = await ryuAPI.getRateTrend(apiType)
    console.log('[数据加载] 限速趋势API响应:', trendResponse)
    console.log('[数据加载] 当前时间:', new Date().toLocaleString('zh-CN'))
    console.log('[数据加载] 数据时间范围检查:', trendResponse.data ? trendResponse.data.map(d => d.time) : '无数据')
    
    // 处理三层API结构返回的数据格式
    if (trendResponse.success && trendResponse.data) {
      trendData.value = trendResponse.data || []
    } else if (Array.isArray(trendResponse)) {
      trendData.value = trendResponse
    } else {
      trendData.value = trendResponse.value || trendResponse || []
    }
    
    console.log('处理后的趋势数据:', trendData.value)
    
    // 4. 获取限速原因分布数据 - 使用与趋势图相同的时间范围
    try {
      // 调用新的API获取限速原因统计，使用相同的时间范围
      const reasonStatsResponse = await ryuAPI.getRateReasonStats(hours)
      console.log('=== 限速原因统计API原始响应 ===')
      console.log('响应类型:', typeof reasonStatsResponse)
      console.log('响应内容:', JSON.stringify(reasonStatsResponse, null, 2))
      
      // 处理不同的响应格式
      let processedData = []
      
      if (reasonStatsResponse && reasonStatsResponse.success && Array.isArray(reasonStatsResponse.data)) {
        // 格式1: {success: true, data: [{reason: "...", count: N}]}
        processedData = reasonStatsResponse.data
        console.log('✅ 使用格式1: success + data数组')
      } else if (Array.isArray(reasonStatsResponse)) {
        // 格式2: 直接是数组 [{reason: "...", count: N}]
        processedData = reasonStatsResponse
        console.log('✅ 使用格式2: 直接数组')
      } else if (reasonStatsResponse && Array.isArray(reasonStatsResponse.data)) {
        // 格式3: {data: [{reason: "...", count: N}]}
        processedData = reasonStatsResponse.data
        console.log('✅ 使用格式3: 仅data数组')
      } else {
        console.warn('⚠️ 无法识别的响应格式，使用降级方案')
        // 降级方案：从异常数据中分析
        const anomaliesResponse = await ryuAPI.getAnomalies(24)
        let anomaliesData = []
        if (anomaliesResponse.success && anomaliesResponse.data) {
          anomaliesData = anomaliesResponse.data
        } else if (Array.isArray(anomaliesResponse)) {
          anomaliesData = anomaliesResponse
        } else {
          anomaliesData = anomaliesResponse.value || []
        }
        processedData = analyzeRateReasons(anomaliesData)
        console.log('使用异常数据分析结果')
      }
      
      reasonData.value = processedData
      console.log('=== 最终处理后的原因分布数据 ===')
      console.log('[数据加载] 当前系统时间:', new Date().toLocaleString('zh-CN'))
      console.log('[数据加载] 饼图数据数量:', processedData.length)
      console.log('[数据加载] 饼图数据内容:', JSON.stringify(processedData, null, 2))
      console.log('[数据加载] ⚠️ 注意检查：数据是否为今天的数据？')
      
      if (processedData.length === 0) {
        console.warn('⚠️ 原因分布数据为空！')
      } else if (processedData.length === 1) {
        console.warn('⚠️ 只有一种限速原因，饼图将显示单色')
      } else {
        console.log('✅ 有', processedData.length, '种限速原因，饼图应显示多色')
      }
      
    } catch (error) {
      console.error('❌ 获取限速原因统计失败:', error)
      console.error('错误堆栈:', error.stack)
      // 降级方案：从异常数据中分析
      const anomaliesResponse = await ryuAPI.getAnomalies(24)
      let anomaliesData = []
      if (anomaliesResponse.success && anomaliesResponse.data) {
        anomaliesData = anomaliesResponse.data
      } else if (Array.isArray(anomaliesResponse)) {
        anomaliesData = anomaliesResponse
      } else {
        anomaliesData = anomaliesResponse.value || []
      }
      reasonData.value = analyzeRateReasons(anomaliesData)
      console.log('使用异常数据分析结果（错误降级）')
    }
    
    // 5. 获取今天的限速原因数据（用于卡片显示）
    try {
      const todayReasonResponse = await ryuAPI.getRateReasonStats(24)  // 固定获取今天（24小时）的数据
      console.log('[卡片数据] 今天的限速原因统计:', todayReasonResponse)
      
      if (todayReasonResponse && todayReasonResponse.success && Array.isArray(todayReasonResponse.data)) {
        todayReasonData.value = todayReasonResponse.data
        console.log('[卡片数据] 今天的限速原因数据:', todayReasonData.value)
      } else if (Array.isArray(todayReasonResponse)) {
        todayReasonData.value = todayReasonResponse
      } else {
        todayReasonData.value = []
        console.log('[卡片数据] 今天没有限速原因数据')
      }
    } catch (error) {
      console.warn('[卡片数据] 获取今天的限速原因统计失败:', error)
      todayReasonData.value = []
    }
    
    // 6. 获取仪表板卡片数据 - 通过新的dashboard_cards接口
    try {
      const dashboardCardsResponse = await ryuAPI.getDashboardCards()
      console.log('仪表板卡片数据API响应:', dashboardCardsResponse)
      
      // 处理三层API结构返回的数据格式
      if (dashboardCardsResponse && dashboardCardsResponse.success && dashboardCardsResponse.data) {
        const cardsData = dashboardCardsResponse.data
        
        // 使用后端返回的卡片数据更新统计信息
        stats.value = {
          currentRateLimits: cardsData.current_limit_cnt || (Array.isArray(limitedHosts.value) ? limitedHosts.value.length : 0),
          currentLimitChangePct: cardsData.current_limit_change_pct || 0,
          todayAdded: cardsData.today_new_limit || 0,
          todayLimitChangePct: cardsData.today_limit_change_pct || 0,
          todayReleased: 0, // 需要从历史数据计算
          totalRateLimits: cardsData.current_limit_cnt || (Array.isArray(limitedHosts.value) ? limitedHosts.value.length : 0),
          blackCount: summaryData.black_count || 0,
          whiteCount: summaryData.white_count || 0,
          switchCount: summaryData.switch_count || 0
        }
        
        // 更新高频限速IP数据
        if (cardsData.top_ip) {
          topIPData.value = {
            ip: cardsData.top_ip,
            count: cardsData.top_ip_count || 0
          }
        }
        
        console.log('使用仪表板卡片数据更新统计信息:', cardsData)
      } else {
        console.warn('仪表板卡片数据格式不正确，使用前端计算数据')
        updateStats()
      }
    } catch (error) {
      console.warn('获取仪表板卡片数据失败，使用前端计算数据:', error)
      // 如果新接口调用失败，使用原有的前端计算逻辑
      updateStats()
    }
    
    // 等待DOM更新后再更新图表
    await nextTick()
    
    // 再次检查Canvas引用是否存在后才更新图表
    if (trendChartRef.value && reasonChartRef.value) {
      updateCharts()
    } else {
      console.warn('[数据加载] Canvas引用不存在，延迟100ms后重试...')
      setTimeout(() => {
        if (trendChartRef.value && reasonChartRef.value) {
          updateCharts()
        } else {
          console.warn('[数据加载] 重试后Canvas仍不存在，跳过图表更新')
        }
      }, 100)
    }
    
  } catch (error) {
    console.error('加载限速数据失败:', error)
    // 只在不是Canvas相关错误时才显示alert
    if (!error.message?.includes('Canvas') && !error.message?.includes('ownerDocument')) {
      alert('加载限速数据失败，请检查网络连接和后端服务状态')
    }
  } finally {
    loading.value = false
  }
}

// 分析限速原因分布
const analyzeRateReasons = (anomalies) => {
  const reasons = {}
  anomalies.forEach(anomaly => {
    if (anomaly.anomaly_type) {
      reasons[anomaly.anomaly_type] = (reasons[anomaly.anomaly_type] || 0) + 1
    }
  })
  
  return Object.entries(reasons).map(([reason, count]) => ({
    reason,
    count
  }))
}

// ✅ 处理限速原因选择变化（添加时）
const onReasonChange = () => {
  // 如果不是"其他原因"，清空自定义输入框
  if (newLimitForm.value.reason !== '其他原因') {
    newLimitForm.value.customReason = ''
  }
}

// ✅ 处理限速原因选择变化（编辑时） - 已移除，编辑时不再修改原因

// 添加限速规则
const addLimitRule = async () => {
  // ✅ 表单验证：如果选择"其他原因"，必须输入自定义原因
  if (!newLimitForm.value.ip) {
    alert('请输入IP地址')
    return
  }
  
  if (!newLimitForm.value.reason) {
    alert('请选择限速原因')
    return
  }
  
  if (newLimitForm.value.reason === '其他原因' && !newLimitForm.value.customReason.trim()) {
    alert('请输入自定义的限速原因')
    return
  }
  
  try {
    console.log('添加限速规则:', newLimitForm.value)
    
    // ✅ 如果选择"其他原因"，使用自定义输入的原因；否则使用下拉框选择的原因
    const finalReason = newLimitForm.value.reason === '其他原因' 
      ? newLimitForm.value.customReason.trim() 
      : newLimitForm.value.reason
    
    console.log('最终使用的限速原因:', finalReason)
    
    const ip = newLimitForm.value.ip
    const kbps = newLimitForm.value.kbps
    const durationMinutes = newLimitForm.value.durationMinutes || 5  // 默认5分钟
    
    // ✅ 直接调用addRateLimit，传入duration_minutes参数
    const response = await ryuAPI.addRateLimit(ip, kbps, finalReason, durationMinutes)
    console.log('添加限速API响应:', response)
    
    // 检查添加是否成功
    const addSuccess = response.success || (response.message && response.message.includes('成功'))
    
    if (addSuccess) {
      showAddLimitModal.value = false
      newLimitForm.value = { ip: '', reason: '', customReason: '', kbps: 1024, durationMinutes: 5 }
      await loadRateLimitData()
      alert(`✅ 限速规则添加成功！\n- 限速值: ${kbps} Kbps\n- 时长: ${durationMinutes} 分钟`)
    } else {
      const errorMessage = response.message || response.detail || '添加限速规则失败'
      alert('添加限速规则失败: ' + errorMessage)
    }
    
  } catch (error) {
    console.error('添加限速规则失败:', error)
    alert('添加限速规则失败: ' + error.message)
  }
}

// 解除限速规则
const removeRateLimit = async (ip) => {
  try {
    console.log('解除限速:', ip)
    
    // 三层API结构调用：前端 → 后端API层 → RYU控制器
    const response = await ryuAPI.removeRateLimit(ip)
    
    console.log('解除限速API响应:', response)
    
    // 处理三层API结构返回的数据格式
    if (response.success) {
      // 后端API层返回成功
      await loadRateLimitData()
      alert('限速解除成功')
    } else if (response.message && response.message.includes('成功')) {
      // RYU控制器直接返回成功消息
      await loadRateLimitData()
      alert('限速解除成功')
    } else {
      // 处理错误情况
      const errorMessage = response.message || response.detail || '解除限速失败'
      alert('解除限速失败: ' + errorMessage)
    }
  } catch (error) {
    console.error('解除限速规则失败:', error)
    alert('解除限速失败: ' + error.message)
  }
}

// 更新图表
const updateCharts = () => {
  console.log('[更新图表] 开始更新图表...')
  
  // 检查Canvas引用是否存在 - 在定时刷新或路由切换时可能为空，这是正常的
  if (!trendChartRef.value || !reasonChartRef.value) {
    console.warn('[更新图表] ⚠️ Canvas引用暂时不可用，跳过本次图表更新')
    console.warn('[更新图表] 这在页面切换或初始化时是正常的')
    return
  }
  
  console.log('[更新图表] ✅ Canvas引用正常，继续渲染图表')
  
  // 销毁旧图表
  if (trendChart && typeof trendChart.destroy === 'function') {
    trendChart.destroy()
    console.log('[更新图表] 已销毁旧的趋势图')
  }
  if (reasonChart && typeof reasonChart.destroy === 'function') {
    reasonChart.destroy()
    console.log('[更新图表] 已销毁旧的饼图')
  }
  
  // 处理趋势图表数据格式 - 兼容三层API结构
  let trendLabels = []
  let trendValues = []
  
  console.log('[趋势图渲染] 开始处理趋势数据，周期:', chartPeriod.value)
  console.log('[趋势图渲染] 原始趋势数据:', trendData.value)
  
  if (trendData.value && trendData.value.length > 0) {
    // 检查数据格式，处理不同的API返回结构
    const firstItem = trendData.value[0]
    console.log('[趋势图渲染] 第一条数据格式:', firstItem)
    
    if (firstItem.time && firstItem.count !== undefined) {
      // 标准格式：{time: "12:00", count: 5}
      trendLabels = trendData.value.map(item => item.time || '')
      trendValues = trendData.value.map(item => item.count || 0)
      console.log('[趋势图渲染] 使用标准格式 (time + count)')
    } else if (firstItem.hour !== undefined && firstItem.count !== undefined) {
      // 备选格式：{hour: "12:00", count: 5}
      trendLabels = trendData.value.map(item => item.hour || '')
      trendValues = trendData.value.map(item => item.count || 0)
      console.log('[趋势图渲染] 使用备选格式 (hour + count)')
    } else if (firstItem.date && firstItem.count !== undefined) {
      // 日期格式：{date: "2025-10-31", count: 5}
      trendLabels = trendData.value.map(item => item.date || '')
      trendValues = trendData.value.map(item => item.count || 0)
      console.log('[趋势图渲染] 使用日期格式 (date + count)')
    } else if (typeof firstItem === 'object' && Object.keys(firstItem).length >= 2) {
      // 键值对格式：自动检测键名
      const keys = Object.keys(firstItem)
      const timeKey = keys.find(k => k.includes('time') || k.includes('hour') || k.includes('date')) || keys[0]
      const valueKey = keys.find(k => k.includes('count') || k.includes('value')) || keys[1]
      trendLabels = trendData.value.map(item => item[timeKey] || '')
      trendValues = trendData.value.map(item => item[valueKey] || 0)
      console.log('[趋势图渲染] 使用键值对格式，时间键:', timeKey, '数值键:', valueKey)
    }
    
    console.log('[趋势图渲染] 处理后的标签:', trendLabels)
    console.log('[趋势图渲染] 处理后的数值:', trendValues)
  } else {
    console.warn('[趋势图渲染] 没有趋势数据')
    trendLabels = []
    trendValues = []
  }
  
  // 创建趋势图表
  if (trendChartRef.value && trendLabels.length > 0) {
    console.log('[趋势图渲染] ✅ Canvas引用存在，数据量:', trendLabels.length)
    
    try {
      const ctx = trendChartRef.value.getContext('2d')
    
    // 根据周期调整图表标题
    const periodTitles = {
      'hour': '限速趋势 (最近24小时)',
      'day': '限速趋势 (最近3天)',
      'week': '限速趋势 (最近7天)'
    }
    const chartTitle = periodTitles[chartPeriod.value] || '限速趋势'
    
    console.log('[趋势图渲染] 创建折线图，数据点数量:', trendLabels.length)
    
    // 设置Chart.js默认字体，确保中文显示正常
    Chart.defaults.font.family = "'Microsoft YaHei', 'SimHei', 'Arial', sans-serif"
    
    // 保存当前周期，供callback使用
    const currentPeriod = chartPeriod.value
    
    trendChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: trendLabels,
        datasets: [{
          label: '限速会话',
          data: trendValues,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.15)',
          borderWidth: 3,
          fill: true,
          tension: 0.3,
          pointRadius: 5,
          pointHoverRadius: 8,
          pointBackgroundColor: '#3b82f6',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointHoverBackgroundColor: '#2563eb',
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        locale: 'zh-CN',  // 设置为中文环境
        layout: {
          padding: {
            left: 15,
            right: 20,
            top: 10,
            bottom: 10
          }
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            align: 'end',
            labels: {
              font: {
                size: 12,
                weight: '500'
              },
              usePointStyle: true,
              padding: 15,
              boxWidth: 8,
              boxHeight: 8
            }
          },
          tooltip: {
            enabled: true,
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: '#3b82f6',
            borderWidth: 1,
            padding: 12,
            displayColors: true,
            callbacks: {
              title: function(context) {
                return `时间: ${context[0].label}`
              },
              label: function(context) {
                return `限速会话: ${context.parsed.y} 次`
              },
              afterLabel: function(context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                const percentage = total > 0 ? ((context.parsed.y / total) * 100).toFixed(1) : 0
                return `占该时段总数: ${percentage}%`
              }
            }
          },
          title: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: '限速会话数',
              font: {
                size: 13,
                weight: '600'
              },
              color: '#374151'
            },
            ticks: {
              stepSize: (() => {
                // 动态计算Y轴stepSize，根据数据最大值
                const maxValue = Math.max(...trendValues, 10)
                if (maxValue <= 10) return 1
                if (maxValue <= 50) return 5
                if (maxValue <= 100) return 10
                if (maxValue <= 500) return 50
                return Math.ceil(maxValue / 10)
              })(),
              font: {
                size: 12,
                weight: '500'
              },
              color: '#6b7280',
              padding: 10,
              callback: function(value) {
                return Number.isInteger(value) ? value : ''
              }
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.06)',
              drawBorder: false,
              lineWidth: 1
            }
          },
          x: {
            title: {
              display: true,
              text: getXAxisLabel(),
              font: {
                size: 13,
                weight: '600'
              },
              color: '#374151'
            },
            ticks: {
              maxRotation: 0,  // 不旋转，水平显示
              minRotation: 0,
              font: {
                size: 11,
                family: "'Microsoft YaHei', 'SimHei', sans-serif"  // 使用中文字体
              },
              color: '#6b7280',
              autoSkip: true,
              autoSkipPadding: 20,  // 增加标签之间的间距
              maxTicksLimit: 10,    // 最多显示10个标签
              callback: function(value, index, ticks) {
                const label = this.getLabelForValue(value)
                if (!label) return ''
                
                // 处理不同的时间格式
                if (currentPeriod === 'day') {
                  // 最近1天模式：显示 "2025-10-31 14:00" 格式
                  if (label.includes(' ')) {
                    const datePart = label.split(' ')[0]
                    const timePart = label.split(' ')[1]
                    if (timePart) {
                      const dateShort = datePart.substring(5)  // 提取 MM-DD
                      return `${dateShort} ${timePart.substring(0, 5)}`  // MM-DD HH:MM
                    }
                  }
                  return label
                } else {
                  // 天/周模式：显示 "10-31" 格式（月-日）
                  if (label.includes('-')) {
                    const parts = label.split('-')
                    if (parts.length === 3) {
                      return `${parts[1]}-${parts[2]}`  // 显示 MM-DD
                    }
                  }
                  return label
                }
              }
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.03)',
              drawBorder: false,
              lineWidth: 1
            }
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        }
      }
    })
    
      console.log('[趋势图渲染] ✅ 折线图创建成功')
    } catch (chartError) {
      console.error('[趋势图渲染] ❌ 创建折线图时出错:', chartError)
    }
  } else {
    if (!trendChartRef.value) {
      console.warn('[趋势图渲染] ⚠️ Canvas引用为空，跳过创建')
    } else if (trendLabels.length === 0) {
      console.warn('[趋势图渲染] ⚠️ 无数据，跳过图表创建')
    }
  }
  
  // 处理原因分布图表数据格式 - 兼容三层API结构
  let reasonLabels = []
  let reasonValues = []
  
  console.log('[饼图渲染] 开始处理原因分布数据:', reasonData.value)
  
  if (reasonData.value && reasonData.value.length > 0) {
    // 检查数据格式，处理不同的API返回结构
    const firstItem = reasonData.value[0]
    console.log('[饼图渲染] 第一条数据格式:', firstItem)
    
    if (firstItem.reason && firstItem.count !== undefined) {
      // 标准格式：{reason: "SYN Flood", count: 5}
      reasonLabels = reasonData.value.map(item => item.reason || '未知原因')
      reasonValues = reasonData.value.map(item => item.count || 0)
      console.log('[饼图渲染] 使用标准格式')
    } else if (typeof firstItem === 'object' && Object.keys(firstItem).length === 2) {
      // 键值对格式：{reason: "SYN Flood", value: 5}
      const keys = Object.keys(firstItem)
      const reasonKey = keys.find(k => k.includes('reason') || k.includes('type')) || keys[0]
      const valueKey = keys.find(k => k.includes('count') || k.includes('value')) || keys[1]
      reasonLabels = reasonData.value.map(item => item[reasonKey] || '未知原因')
      reasonValues = reasonData.value.map(item => item[valueKey] || 0)
      console.log('[饼图渲染] 使用键值对格式')
    }
    
    console.log('[饼图渲染] 处理后的标签:', reasonLabels)
    console.log('[饼图渲染] 处理后的数值:', reasonValues)
  } else {
    console.warn('[饼图渲染] 没有原因分布数据，使用占位数据')
    reasonLabels = ['暂无数据']
    reasonValues = [1]
  }
  
  // 创建原因分布图表
  if (reasonChartRef.value && reasonLabels.length > 0 && reasonValues.length > 0) {
    console.log('[饼图渲染] ✅ Canvas引用存在，数据量:', reasonLabels.length)
    
    try {
      const ctx = reasonChartRef.value.getContext('2d')
    
    // ✅ 预定义颜色池（30种不重复的鲜明颜色）
    const colorPool = [
      '#ef4444',  // 红色 - SYN Flood
      '#f59e0b',  // 橙色 - UDP Flood
      '#10b981',  // 绿色 - ICMP Flood
      '#3b82f6',  // 蓝色 - ARP欺骗
      '#8b5cf6',  // 紫色 - Botnet
      '#ec4899',  // 粉色 - 带宽超限
      '#f97316',  // 深橙色 - 异常流量
      '#6366f1',  // 靛蓝色 - 手动限制
      '#06b6d4',  // 青色
      '#84cc16',  // 黄绿色
      '#d946ef',  // 紫粉色
      '#f43f5e',  // 玫红色
      '#14b8a6',  // 青绿色
      '#a855f7',  // 亮紫色
      '#22c55e',  // 鲜绿色
      '#0ea5e9',  // 天蓝色
      '#eab308',  // 黄色
      '#fb923c',  // 亮橙色
      '#c084fc',  // 淡紫色
      '#38bdf8',  // 浅蓝色
      '#4ade80',  // 亮绿色
      '#fbbf24',  // 金黄色
      '#f472b6',  // 亮粉色
      '#a78bfa',  // 柔紫色
      '#2dd4bf',  // 薄荷色
      '#fb7185',  // 珊瑚粉
      '#34d399',  // 翡翠绿
      '#60a5fa',  // 钢蓝色
      '#fcd34d',  // 柠檬黄
      '#f87171'   // 浅红色
    ]
    
    // ✅ 为每个原因生成唯一且不重复的颜色
    const usedColors = new Set()  // 跟踪已使用的颜色
    const generateColor = (label, index) => {
      // 优先为常见的限速原因分配固定颜色
      const fixedColors = {
        'SYN Flood': '#ef4444',
        'UDP Flood': '#f59e0b', 
        'ICMP Flood': '#10b981',
        'ARP 欺骗': '#3b82f6',
        'ARP Spoof': '#3b82f6',
        'Botnet': '#8b5cf6',
        '带宽超限': '#ec4899',
        '异常流量': '#f97316',
        '手动限制': '#6366f1',
        '其他': '#94a3b8',
        '暂无数据': '#d1d5db'
      }
      
      // 如果是固定颜色，直接返回
      if (fixedColors[label]) {
        usedColors.add(fixedColors[label])
        return fixedColors[label]
      }
      
      // 使用label的哈希值生成颜色索引
      let hash = 0
      for (let i = 0; i < label.length; i++) {
        hash = label.charCodeAt(i) + ((hash << 5) - hash)
      }
      
      // 尝试找到一个未使用的颜色
      let colorIndex = Math.abs(hash) % colorPool.length
      let attempts = 0
      while (usedColors.has(colorPool[colorIndex]) && attempts < colorPool.length) {
        colorIndex = (colorIndex + 1) % colorPool.length
        attempts++
      }
      
      const selectedColor = colorPool[colorIndex]
      usedColors.add(selectedColor)
      return selectedColor
    }
    
    // 根据标签生成不重复的颜色数组
    const backgroundColors = reasonLabels.map((label, index) => generateColor(label, index))
    
    console.log('[饼图渲染] 创建饼图，标签数量:', reasonLabels.length, '颜色数量:', backgroundColors.length)
    
    reasonChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: reasonLabels,
        datasets: [{
          data: reasonValues,
          backgroundColor: backgroundColors,
          borderWidth: 2,
          borderColor: '#fff',
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 15,
              font: {
                size: 12
              },
              usePointStyle: true
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || ''
                const value = context.parsed || 0
                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
                return `${label}: ${value} 次 (${percentage}%)`
              }
            }
          }
        }
      }
    })
    
      console.log('[饼图渲染] ✅ 饼图创建成功，包含', reasonLabels.length, '个原因分类')
    } catch (chartError) {
      console.error('[饼图渲染] ❌ 创建饼图时出错:', chartError)
    }
  } else {
    if (!reasonChartRef.value) {
      console.warn('[饼图渲染] ⚠️ Canvas引用为空，跳过创建')
    } else if (reasonLabels.length === 0) {
      console.warn('[饼图渲染] ⚠️ 无数据，跳过图表创建')
    }
  }
  
  console.log('[更新图表] 图表更新完成')
}



const editHost = (host) => {
  currentHost.value = host
  // ✅ 记录原始数据，用于判断用户是否修改了速率
  editLimitForm.value = { 
    ip: host.ip,
    kbps: host.kbps,
    originalKbps: host.kbps,      // 记录原始速率
    timeAdjustType: 'extend',
    timeAdjustMinutes: null
  }
  showEditModal.value = true
}

const releaseHost = (host) => {
  currentHost.value = host
  showReleaseModal.value = true
}

const blockHost = (host) => {
  currentHost.value = host
  showBlockModal.value = true
}

const confirmRelease = async () => {
  try {
    if (currentHost.value) {
      console.log('开始解除限速，IP:', currentHost.value.ip)
      
      // 三层API结构调用：前端 → 后端API层 → RYU控制器
      const response = await ryuAPI.removeRateLimit(currentHost.value.ip)
      console.log('解除限速API响应:', response)
      
      // 处理三层API结构返回的数据格式
      if (response.success || (response.message && response.message.includes('成功'))) {
        showReleaseModal.value = false
        await loadRateLimitData()
        alert('解除限速成功')
      } else {
        // 处理错误情况
        const errorMessage = response.message || response.detail || '解除限速失败'
        alert('解除限速失败: ' + errorMessage)
      }
    }
  } catch (error) {
    console.error('解除限速失败:', error)
    alert('解除限速失败: ' + error.message)
  }
}

const confirmBlock = async () => {
  try {
    if (currentHost.value) {
      // 三层API结构调用：前端 → 后端API层 → RYU控制器
      const response = await ryuAPI.addBlacklist(currentHost.value.ip)
      console.log('封禁主机API响应:', response)
      
      // 处理三层API结构返回的数据格式
      if (response.success || (response.message && response.message.includes('成功'))) {
        showBlockModal.value = false
        await loadRateLimitData()
        alert('主机封禁成功')
      } else {
        // 处理错误情况
        const errorMessage = response.message || response.detail || '封禁主机失败'
        alert('封禁主机失败: ' + errorMessage)
      }
    }
  } catch (error) {
    console.error('封禁主机失败:', error)
    alert('封禁主机失败: ' + error.message)
  }
}

const updateLimitRule = async () => {
  // ✅ 表单验证
  if (!editLimitForm.value.ip) {
    alert('IP地址不能为空')
    return
  }
  
  try {
    console.log('[编辑限速] 更新限速规则:', editLimitForm.value)
    
    const ip = editLimitForm.value.ip
    const kbps = editLimitForm.value.kbps
    const originalKbps = editLimitForm.value.originalKbps
    
    let allSuccess = true
    let messages = []
    
    // 判断用户是否修改了速率
    const speedChanged = kbps !== originalKbps
    
    console.log(`[编辑限速] 速率是否改变: ${speedChanged} (原:${originalKbps}, 新:${kbps})`)
    
    // ✅ 1. 如果速率改变了，调用修改速率API（不传reason参数）
    if (speedChanged) {
      try {
        const speedResponse = await ryuAPI.changeRateSpeed(ip, kbps, '管理员调整速率')
        console.log('[编辑限速] 修改速率API响应:', speedResponse)
        
        if (speedResponse.success || (speedResponse.message && speedResponse.message.includes('成功'))) {
          messages.push(`✅ 速率已调整为 ${kbps} Kbps`)
        } else {
          allSuccess = false
          messages.push(`❌ 速率调整失败: ${speedResponse.message || '未知错误'}`)
        }
      } catch (error) {
        console.error('[编辑限速] 修改速率失败:', error)
        allSuccess = false
        messages.push(`❌ 速率调整失败: ${error.message}`)
      }
    }
    
    // ✅ 2. 修改限速时间（如果用户填写了调整时间）
    if (editLimitForm.value.timeAdjustMinutes && editLimitForm.value.timeAdjustMinutes > 0) {
      const minutes = parseInt(editLimitForm.value.timeAdjustMinutes)
      const extra_seconds = editLimitForm.value.timeAdjustType === 'extend' 
        ? minutes * 60   // 延长：正数
        : -minutes * 60  // 缩短：负数
      
      const timeReason = `管理员${editLimitForm.value.timeAdjustType === 'extend' ? '延长' : '缩短'}${minutes}分钟`
      
      try {
        const durationResponse = await ryuAPI.changeRateDuration(ip, extra_seconds, timeReason)
        console.log('[编辑限速] 修改时间API响应:', durationResponse)
        
        if (durationResponse.success || (durationResponse.message && durationResponse.message.includes('成功'))) {
          messages.push(`✅ ${durationResponse.message || '时间调整成功'}`)
        } else {
          allSuccess = false
          messages.push(`❌ 时间调整失败: ${durationResponse.message || '未知错误'}`)
        }
      } catch (error) {
        console.error('[编辑限速] 修改时间失败:', error)
        allSuccess = false
        messages.push(`❌ 时间调整失败: ${error.message}`)
      }
    }
    
    // 如果没有任何修改
    if (!speedChanged && (!editLimitForm.value.timeAdjustMinutes || editLimitForm.value.timeAdjustMinutes <= 0)) {
      alert('请至少修改速率或调整时间中的一项')
      return
    }
    
    // 显示结果
    if (allSuccess) {
      showEditModal.value = false
      // ✅ 等待100ms确保数据库事务完成
      await new Promise(resolve => setTimeout(resolve, 100))
      await loadRateLimitData()  // ✅ 先刷新数据
      console.log('[编辑限速] 数据刷新完成，当前limitedHosts:', limitedHosts.value)
      alert('限速规则更新成功\n\n' + messages.join('\n'))
    } else {
      await new Promise(resolve => setTimeout(resolve, 100))
      await loadRateLimitData()  // ✅ 失败也要刷新，同步最新状态
      alert('限速规则更新部分失败\n\n' + messages.join('\n'))
    }
    
  } catch (error) {
    console.error('[编辑限速] 更新限速规则失败:', error)
    alert('更新限速规则失败: ' + error.message)
  }
}

const exportData = () => {
  // 导出数据逻辑
  console.log('导出数据')
}

// 历史限速相关函数
const loadHistoryData = async () => {
  try {
    if (!historyDate.value) {
      historyRecords.value = []
      return
    }
    
    loading.value = true
    console.log('开始加载历史限速数据，日期:', historyDate.value)
    
    // 三层API结构调用：前端 → 后端API层 → RYU控制器
    const response = await ryuAPI.getRateHistoryByDay(historyDate.value)
    console.log('历史限速API响应数据:', response)
    
    // 数据格式处理：兼容不同API返回结构
    let data = []
    if (response && response.data) {
      // 标准格式：后端API层返回格式
      data = response.data
    } else if (Array.isArray(response)) {
      // 备选格式：直接RYU控制器返回格式
      data = response
    } else if (response && typeof response === 'object') {
      // 键值对格式：某些API可能返回对象格式
      data = Object.values(response)
    }
    
    console.log('处理后的历史限速数据:', data)
    
    // 数据验证和转换
    if (Array.isArray(data)) {
      const processedData = data.map(item => ({
        src_ip: item.src_ip || item.ip || '',
        action: item.action || 'limit',
        reason: item.reason || '未知',
        kbps: item.kbps || null,
        created_at: item.created_at || item.createdAt || new Date().toISOString(),
        operator: item.operator || '系统'
      }))
      
      // 数据分析和去重处理
      const { uniqueRecords, statistics } = analyzeAndDeduplicateHistoryData(processedData)
      
      // 按时间倒序排列，最新的记录显示在最前面
      historyRecords.value = uniqueRecords.sort((a, b) => {
        const timeA = new Date(a.created_at).getTime()
        const timeB = new Date(b.created_at).getTime()
        return timeB - timeA
      })
      
      // 更新统计信息
      historyStats.value = statistics
      console.log('历史数据统计:', statistics)
      
      // 更新分页数据
      updatePagination()
    } else {
      historyRecords.value = []
      historyStats.value = {
        totalRecords: 0,
        uniqueIPs: 0,
        limitActions: 0,
        releaseActions: 0,
        duplicateCount: 0
      }
    }
    
    console.log('最终历史限速数据:', historyRecords.value)
    
  } catch (error) {
    console.error('加载历史限速数据失败:', error)
    
    // 错误处理：显示用户友好的错误信息
    let errorMessage = '加载历史限速数据失败'
    if (error.response && error.response.data) {
      errorMessage = error.response.data.message || error.response.data.detail || errorMessage
    } else if (error.message) {
      errorMessage = error.message
    }
    
    alert(errorMessage)
    historyRecords.value = []
  } finally {
    loading.value = false
  }
}

const exportHistoryData = () => {
  if (historyRecords.value.length === 0) {
    alert('没有历史数据可导出')
    return
  }
  
  // 创建CSV格式数据
  const headers = ['IP地址', '操作类型', '限速原因', '限速值(Kbps)', '操作时间', '操作者']
  const csvData = historyRecords.value.map(record => [
    record.src_ip,
    getActionText(record.action),
    record.reason,
    record.kbps || '-',
    formatDateTime(record.created_at),
    record.operator
  ])
  
  // 创建CSV内容
  const csvContent = [headers, ...csvData]
    .map(row => row.map(cell => `"${cell}"`).join(','))
    .join('\n')
  
  // 创建下载链接
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `历史限速记录_${historyDate.value}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const getActionText = (action) => {
  const actionMap = {
    'limit': '限速',
    'release': '解除限速',
    'unlimit': '解除限速',
    'block': '封禁'
  }
  return actionMap[action] || action
}

const getActionClass = (action) => {
  const classes = {
    'limit': 'bg-blue-100 text-blue-800',
    'release': 'bg-green-100 text-green-800',
    'unlimit': 'bg-green-100 text-green-800',
    'block': 'bg-red-100 text-red-800'
  }
  return classes[action] || 'bg-gray-100 text-gray-800'
}



// 注意：不要监听 chartPeriod 变化自动加载数据，因为 changeChartPeriod 已经处理了数据加载
// watch(chartPeriod, (newPeriod) => {
//   loadRateLimitData()
// })

// 分页相关函数
const updatePagination = () => {
  // 计算总页数
  totalPages.value = Math.ceil(historyRecords.value.length / pageSize.value)
  
  // 确保当前页在有效范围内
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value
  }
  if (currentPage.value < 1) {
    currentPage.value = 1
  }
  
  // 计算当前页的数据
  const startIndex = (currentPage.value - 1) * pageSize.value
  const endIndex = startIndex + pageSize.value
  paginatedRecords.value = historyRecords.value.slice(startIndex, endIndex)
}

const goToPage = (page) => {
  currentPage.value = page
  updatePagination()
}

const goToPreviousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    updatePagination()
  }
}

const goToNextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    updatePagination()
  }
}

// 监听历史日期变化，当用户选择不同日期时加载对应的历史数据
watch(historyDate, (newDate) => {
  if (newDate) {
    console.log('历史日期变更，新日期:', newDate)
    currentPage.value = 1 // 重置到第一页
    loadHistoryData()
  }
})

// 组件挂载时加载数据
onMounted(async () => {
  console.log('[INFO] 限速管理页面加载，开始初始化数据...')
  
  // 设置默认历史日期为今天
  const today = new Date()
  historyDate.value = today.toISOString().split('T')[0]
  
  // 等待DOM完全渲染
  await nextTick()
  
  // 加载数据
  await loadRateLimitData()
  
  // 设置定时刷新数据 - 30秒刷新一次，避免频繁请求
  const refreshInterval = setInterval(() => {
    console.log('[INFO] 定时刷新限速数据...')
    loadRateLimitData()
  }, 30000) // 30秒刷新一次
  
  // 组件卸载时清除定时器
  return () => {
    clearInterval(refreshInterval)
  }
})

</script>

<style scoped>
/* 波浪容器样式 */
.wave-container {
  width: 100%;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

.wave-svg {
  width: 100%;
  height: 100%;
}

.wave-path {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

/* 速度仪表盘样式 */
.speed-gauge-container {
  width: 100%;
  height: 120px;
  position: relative;
}

.speed-gauge {
  width: 100%;
  height: 100%;
}

/* 限速卡片样式 */
.rate-limit-card {
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.rate-limit-card.high-traffic {
  border: 2px solid #ef4444;
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
}

/* 热力波纹效果 */
.ripple-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.ripple {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(239, 68, 68, 0.6);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: ripple-expand 2s infinite;
}

@keyframes ripple-expand {
  0% {
    width: 20px;
    height: 20px;
    opacity: 1;
  }
  100% {
    width: 200px;
    height: 200px;
    opacity: 0;
  }
}

/* 高流量闪烁效果 */
.high-traffic {
  animation: traffic-pulse 2s infinite;
}

@keyframes traffic-pulse {
  0%, 100% {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }
  50% {
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.5), 0 0 40px rgba(239, 68, 68, 0.3);
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .rate-limit-card {
    background-color: #1f2937;
    color: #f9fafb;
  }
  
  .wave-svg rect[fill="#f3f4f6"] {
    fill: #374151;
  }
  
  .wave-text {
    fill: #f9fafb;
  }
}

/* 响应式设计 */
@media (max-width: 640px) {
  .speed-gauge-container {
    height: 100px;
  }
  
  .wave-container {
    height: 50px;
  }
}

/* 折叠动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
  max-height: 0;
  overflow: hidden;
}

.slide-fade-enter-to,
.slide-fade-leave-from {
  transform: translateY(0);
  opacity: 1;
  max-height: 500px;
}
</style>