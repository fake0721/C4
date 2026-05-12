<template>
  <div>
    <!-- 页面标题和时间筛选 -->
    <div class="mb-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-[clamp(1.5rem,3vw,2rem)] font-bold text-dark">异常检测</h2>
          <p class="text-dark-2 mt-1">实时监控网络异常行为</p>
        </div>
        <div class="flex space-x-2">
          <button 
            v-for="period in timePeriods" 
            :key="period.value"
            @click="changeTimePeriod(period.value)"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
              selectedPeriod === period.value 
                ? 'bg-blue-600 text-white shadow-md' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            ]"
          >
            {{ period.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-lg p-6 shadow-md">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-blue-100 text-blue-600 mr-4">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
            </svg>
          </div>
          <div>
            <p class="text-sm text-gray-500">活跃攻击源</p>
            <p class="text-2xl font-bold text-gray-900">{{ stats.activeSources }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg p-6 shadow-md">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-red-100 text-red-600 mr-4">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>
          </div>
          <div>
            <p class="text-sm text-gray-500">总异常数据包</p>
            <p class="text-2xl font-bold text-gray-900">{{ stats.totalAnomalies }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg p-6 shadow-md">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-yellow-100 text-yellow-600 mr-4">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
          </div>
          <div>
            <p class="text-sm text-gray-500">异常次数</p>
            <p class="text-2xl font-bold text-gray-900">{{ stats.attackCount }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg p-6 shadow-md">
        <div class="flex items-center">
          <div class="p-3 rounded-full bg-green-100 text-green-600 mr-4">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <div>
            <p class="text-sm text-gray-500">管理员已处理异常</p>
            <p class="text-2xl font-bold text-gray-900">{{ stats.handledAnomalies }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 可视化图表区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <!-- 异常类型分布饼图 -->
      <div class="bg-white rounded-lg p-6 shadow-md">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">异常类型分布</h3>
        <div ref="typeChart" class="h-80"></div>
      </div>
      
      <!-- 攻击源IP分布柱状图 -->
      <div class="bg-white rounded-lg p-6 shadow-md">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">攻击源IP分布</h3>
        <div ref="sourceChart" class="h-80"></div>
      </div>
      
      <!-- 异常时间趋势图 -->
      <div class="bg-white rounded-lg p-6 shadow-md lg:col-span-2">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">异常时间趋势</h3>
        <div ref="trendChart" class="h-80"></div>
      </div>
    </div>

    <!-- 各类攻击数据包统计 -->
    <div class="bg-white rounded-lg p-6 shadow-md">
      <div class="flex justify-between items-center mb-6">
        <h3 class="text-xl font-bold text-gray-900">各类攻击数据包统计</h3>
        <div class="text-sm text-gray-500">
          共 {{ anomalies.length }} 条异常事件
        </div>
      </div>
      
      <!-- 图表 -->
      <div class="mb-8">
        <div ref="timelineChart" class="h-64"></div>
      </div>
      
      <!-- 异常事件表格 - 优化配色版 -->
      <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <div class="overflow-x-auto" style="max-height: 500px; overflow-y: auto;">
          <table class="min-w-full">
            <thead class="bg-gradient-to-r from-blue-50 to-indigo-50 sticky top-0 z-10">
              <tr>
                <th class="px-5 py-3.5 text-left text-xs font-bold text-gray-700 uppercase">
                  风险
                </th>
                <th class="px-5 py-3.5 text-left text-xs font-bold text-gray-700 uppercase">
                  攻击类型
                </th>
                <th class="px-5 py-3.5 text-left text-xs font-bold text-gray-700 uppercase">
                  攻击来源
                </th>
                <th class="px-5 py-3.5 text-left text-xs font-bold text-gray-700 uppercase">
                  检测时间
                </th>
                <th class="px-5 py-3.5 text-right text-xs font-bold text-gray-700 uppercase">
                  操作
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr 
                v-for="(anomaly, index) in getUniqueAnomaliesForCards()" 
                :key="index"
                class="hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 transition-all duration-200"
              >
                <!-- 风险等级 -->
                <td class="px-5 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold" 
                        :class="getSeverityBadgeClass(anomaly.severity)">
                    <div :class="getSeverityDotClass(anomaly.severity)" class="w-1.5 h-1.5 rounded-full mr-1.5"></div>
                    {{ getSeverityText(anomaly.severity) }}
                  </span>
                </td>
                
                <!-- 攻击类型 -->
                <td class="px-5 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2">
                    <i class="fa fa-shield-alt text-orange-500"></i>
                    <span class="text-sm font-semibold text-gray-900">{{ anomaly.type }}</span>
                  </div>
                </td>
                
                <!-- 攻击来源 -->
                <td class="px-5 py-4 whitespace-nowrap">
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                      <i class="fa fa-laptop text-blue-600 text-xs"></i>
                    </div>
                    <span class="text-sm font-mono font-medium text-gray-900">{{ anomaly.src_ip }}</span>
                  </div>
                </td>
                
                <!-- 检测时间 -->
                <td class="px-5 py-4 whitespace-nowrap">
                  <div class="text-sm text-gray-600 flex items-center gap-1.5">
                    <i class="fa fa-clock text-gray-400 text-xs"></i>
                    {{ formatRelativeTime(anomaly.timestamp) }}
                  </div>
                </td>
                
                <!-- 操作按钮 -->
                <td class="px-5 py-4 whitespace-nowrap text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button 
                      @click="handleAction(anomaly.src_ip, 'blacklist')"
                      class="px-3 py-1.5 text-xs font-bold text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors duration-200 flex items-center gap-1.5"
                    >
                      <i class="fa fa-ban text-xs"></i>
                      <span>封禁</span>
                    </button>
                    <button 
                      @click="handleAction(anomaly.src_ip, 'ratelimit')"
                      class="px-3 py-1.5 text-xs font-bold text-white bg-amber-500 rounded-lg hover:bg-amber-600 transition-colors duration-200 flex items-center gap-1.5"
                    >
                      <i class="fa fa-tachometer-alt text-xs"></i>
                      <span>限速</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- 无数据提示 -->
        <div v-if="getUniqueAnomaliesForCards().length === 0" class="text-center py-16 bg-gradient-to-br from-gray-50 to-blue-50">
          <i class="fa fa-check-circle text-green-400 text-6xl mb-4"></i>
          <p class="text-gray-700 font-semibold text-lg mb-1">系统运行正常</p>
          <p class="text-gray-500 text-sm">暂无异常事件</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import axios from 'axios';
import * as echarts from 'echarts';
import ryuApi from '@/api/ryu';

// 定义数据结构
interface Anomaly {
  id: string;
  timestamp: number;
  src_ip: string;
  dst_ip?: string;  // ✅ 新增：目标IP（可选）
  type: string;
  details: string;
  rate_kbps: number;
  severity: string;
  anomaly_type: string;
  detect_time: string;
  time: string;
}

// 响应式数据
const anomalies = ref<Anomaly[]>([]);  // 用于列表显示（只显示pending状态）
const allAnomalies = ref<Anomaly[]>([]);  // ✅ 用于图表显示（显示所有状态）
// ✅ 时间范围：hours=24时后端查询"今日"（从0点到现在），与Dashboard一致
const selectedPeriod = ref<number>(24); // 默认最近一天（实际查询：今日从0点到现在）

// 时间筛选选项
const timePeriods = ref([
  { label: '最近一天', value: 24 },  // 实际查询：今日（从0点到现在）
  { label: '最近三天', value: 72 },
  { label: '最近七天', value: 168 }
]);

// 统计信息
const stats = ref({
  activeSources: 0,        // 活跃攻击源数量
  totalAnomalies: 0,       // 总异常数据包数量（从anomaly_log数据库实际记录数，与Dashboard一致）
  attackCount: 0,          // 异常次数（从attack_sessions）
  handledAnomalies: 0      // 已处理异常数量
});

// 已处理的IP集合（限速+黑名单）
const handledIPs = ref<Set<string>>(new Set());

// 图表实例
const typeChart = ref<HTMLElement>();
const sourceChart = ref<HTMLElement>();
const trendChart = ref<HTMLElement>();
const timelineChart = ref<HTMLElement>();
let typeChartInstance: echarts.ECharts;
let sourceChartInstance: echarts.ECharts;
let trendChartInstance: echarts.ECharts;
let timelineChartInstance: echarts.ECharts;

// 定时器
let anomaliesTimer: number | null = null;





// 严重程度文本
const getSeverityText = (severity: string): string => {
  const texts: Record<string, string> = {
    'high': '高',
    'medium': '中',
    'low': '低'
  };
  return texts[severity] || '未知';
};

// 异常卡片样式
// 严重程度圆点样式
const getSeverityDotClass = (severity: string): string => {
  const classes: Record<string, string> = {
    'high': 'bg-red-500',
    'medium': 'bg-yellow-500',
    'low': 'bg-green-500'
  };
  return classes[severity] || 'bg-gray-500';
};

// ✅ 新增：严重程度徽章样式
const getSeverityBadgeClass = (severity: string): string => {
  const classes: Record<string, string> = {
    'high': 'bg-red-100 text-red-700',
    'medium': 'bg-amber-100 text-amber-700',
    'low': 'bg-green-100 text-green-700'
  };
  return classes[severity] || 'bg-gray-100 text-gray-700';
};

// 格式化相对时间
const formatRelativeTime = (timestamp: number): string => {
  const now = Date.now();
  const diff = now - timestamp;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) return `${days}天前`;
  if (hours > 0) return `${hours}小时前`;
  if (minutes > 0) return `${minutes}分钟前`;
  return '刚刚';
};

// ✅ 获取已处理的IP列表（从limit_sessions历史记录 + 黑名单）
const fetchHandledIPs = async () => {
  try {
    const handled = new Set<string>();
    
    // ✅ 方法1：从limit_sessions表获取历史限速记录（包括已过期的）
    // 这样统计的是"处理过的"而不是"正在处理的"
    try {
      // 将小时数转换为天数
      const days = Math.ceil(selectedPeriod.value / 24); // 24小时=1天, 72小时=3天, 168小时=7天
      
      // 直接查询limit_sessions表（需要创建新的API）
      const response = await axios.get('/v1/handled-ips', {
        params: { days }
      });
      
      if (response.data.ips && Array.isArray(response.data.ips)) {
        response.data.ips.forEach((ip: string) => handled.add(ip));
        console.log('[Anomalies] 从limit_sessions获取已处理IP:', response.data.ips.length, '个');
      }
    } catch (error) {
      console.warn('[Anomalies] limit_sessions API不可用，降级使用rate_limit_active');
      // 降级方案：使用当前限速列表
      const rateLimitResponse = await ryuApi.getRateLimit();
      if (rateLimitResponse && rateLimitResponse.data) {
        rateLimitResponse.data.forEach((item: any) => {
          if (item.src_ip) handled.add(item.src_ip);
        });
      }
    }
    
    // ✅ 方法2：获取黑名单（从acl_entries表）
    const aclResponse = await axios.get('/v1/acl');
    if (aclResponse.data.success && aclResponse.data.data.black_list) {
      aclResponse.data.data.black_list.forEach((item: any) => {
        if (item.ip) {
          handled.add(item.ip);
        }
      });
      console.log('[Anomalies] 黑名单IP:', aclResponse.data.data.black_list.length, '个');
    }
    
    handledIPs.value = handled;
    console.log('[Anomalies] 已处理IP总数:', handled.size, '个');
  } catch (error) {
    console.error('[Anomalies] 获取已处理IP失败:', error);
  }
};

// 计算统计数据
const calculateStats = async (data: Anomaly[], totalPackets = 0) => {
  const uniqueSources = new Set(data.map(item => item.src_ip));
  
  // ✅ 从attack_sessions表获取攻击会话列表和统计
  let attackCount = 0;
  let handledCount = 0;
  
  try {
    // 1️⃣ 获取攻击会话统计（用于显示"异常次数"）
    const countData = await ryuApi.getAttackSessionsCount();
    if (selectedPeriod.value === 24) {
      attackCount = countData.day || 0;
    } else if (selectedPeriod.value === 72) {
      attackCount = countData.three_days || 0;
    } else if (selectedPeriod.value === 168) {
      attackCount = countData.week || 0;
    }
    
    // 2️⃣ 获取已处理的攻击会话统计（status='handled'）
    const handledData = await ryuApi.getHandledSessionsCount();
    if (selectedPeriod.value === 24) {
      handledCount = handledData.day || 0;
    } else if (selectedPeriod.value === 72) {
      handledCount = handledData.three_days || 0;
    } else if (selectedPeriod.value === 168) {
      handledCount = handledData.week || 0;
    }
    
    console.log('[Anomalies] 攻击会话统计:', {
      待处理: attackCount,
      已处理: handledCount,
      合计: attackCount + handledCount
    });
    
  } catch (error) {
    console.error('[Anomalies] 获取攻击会话统计失败:', error);
  }
  
  stats.value = {
    activeSources: uniqueSources.size,
    totalAnomalies: totalPackets,       // ✅ 使用anomaly_log的数据包总数
    attackCount: attackCount,           // attack_sessions中status='pending'的数量
    handledAnomalies: handledCount      // attack_sessions中status='handled'的数量
  };
  
  console.log('[Anomalies] 最终统计数据:', {
    活跃攻击源: uniqueSources.size,
    总异常数据包: totalPackets,          // ✅ 显示anomaly_log的数据包总数
    异常次数: attackCount,
    已处理异常: handledCount
  });
};

// 去重异常数据 - 基于IP和攻击类型进行去重，保留最新的记录
const deduplicateAnomalies = (data: Anomaly[]): Anomaly[] => {
  const uniqueMap = new Map();
  
  data.forEach(anomaly => {
    const key = `${anomaly.src_ip}_${anomaly.type}`;
    const existing = uniqueMap.get(key);
    
    // 如果不存在或者当前记录时间更新，则更新
    if (!existing || anomaly.timestamp > existing.timestamp) {
      uniqueMap.set(key, anomaly);
    }
  });
  
  // 按时间倒序排序
  return Array.from(uniqueMap.values()).sort((a, b) => b.timestamp - a.timestamp);
};

// 获取去重后的异常数据用于卡片显示
const getUniqueAnomaliesForCards = () => {
  return deduplicateAnomalies(anomalies.value);
};

// 初始化图表
const initCharts = () => {
  nextTick(() => {
    // 确保DOM元素存在且可见
    if (typeChart.value && typeChart.value.offsetParent !== null) {
      typeChartInstance = echarts.init(typeChart.value);
    }
    if (sourceChart.value && sourceChart.value.offsetParent !== null) {
      sourceChartInstance = echarts.init(sourceChart.value);
    }
    if (trendChart.value && trendChart.value.offsetParent !== null) {
      trendChartInstance = echarts.init(trendChart.value);
    }
    if (timelineChart.value && timelineChart.value.offsetParent !== null) {
      timelineChartInstance = echarts.init(timelineChart.value);
    }
    updateCharts();
  });
};

// 更新图表
const updateCharts = () => {
  // ✅ 图表使用allAnomalies（显示所有攻击，包括pending和handled）
  // 异常类型分布饼图
  const typeData = allAnomalies.value.reduce((acc: Record<string, number>, item: Anomaly) => {
    acc[item.type] = (acc[item.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  const typeChartOption = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center'
    },
    series: [
      {
        name: '异常类型',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 18,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: Object.entries(typeData).map(([name, value]) => ({
          name,
          value
        }))
      }
    ]
  };
  
  // 攻击源IP分布柱状图
  const sourceData = allAnomalies.value.reduce((acc: Record<string, number>, item: Anomaly) => {
    acc[item.src_ip] = (acc[item.src_ip] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  const sortedSources = Object.entries(sourceData)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 10);
  
  const sourceChartOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: sortedSources.map(([ip]) => ip),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '异常数量',
        type: 'bar',
        data: sortedSources.map(([,count]) => count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        }
      }
    ]
  };
  
  if (typeChartInstance && !typeChartInstance.isDisposed()) typeChartInstance.setOption(typeChartOption);
  if (sourceChartInstance && !sourceChartInstance.isDisposed()) sourceChartInstance.setOption(sourceChartOption);
};

// ✅ 更新异常时间趋势图（使用attack_sessions数据，显示会话数趋势）
const updateTrendChart = async () => {
  if (!trendChartInstance || trendChartInstance.isDisposed()) return;
  
  try {
    // 从backend获取attack_sessions的时间趋势
    const response = await axios.get('/v1/attack-sessions/trend', {
      params: { hours: selectedPeriod.value }
    });
    
    if (response.data.success && response.data.data) {
      const trendData = response.data.data;
      const hours = trendData.map((item: any) => item.hour);
      const counts = trendData.map((item: any) => item.count);
      
      // ✅ 根据数据点数量动态调整X轴标签显示策略
      const dataPointCount = hours.length;
      let xAxisLabelConfig: any = { 
        fontSize: 11,
        rotate: 0  // 默认不旋转
      };
      
      // 如果数据点较多（>30），启用自动间隔显示
      if (dataPointCount > 30) {
        xAxisLabelConfig.interval = Math.floor(dataPointCount / 15);  // 显示约15个标签
        xAxisLabelConfig.rotate = 45;  // 旋转45度避免重叠
      } else if (dataPointCount > 15) {
        xAxisLabelConfig.rotate = 30;  // 中等旋转
      }
      
      const trendChartOption = {
        tooltip: {
          trigger: 'axis',
          formatter: function (params: any) {
            const data = params[0];
            return `${data.axisValue}<br/>${data.marker}攻击会话: <strong>${data.value}</strong>次`;
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: dataPointCount > 15 ? '15%' : '3%',  // ✅ 旋转时增加底部空间
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: hours,
          axisLabel: xAxisLabelConfig
        },
        yAxis: {
          type: 'value',
          name: '会话数量',
          minInterval: 1,
          axisLabel: { fontSize: 11 }
        },
        series: [
          {
            name: '攻击会话',
            type: 'line',
            smooth: true,
            lineStyle: { width: 3, color: '#3b82f6' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(59,130,246,0.3)' },
                { offset: 1, color: 'rgba(59,130,246,0.05)' }
              ])
            },
            itemStyle: { color: '#3b82f6' },
            data: counts
          }
        ]
      };
      
      trendChartInstance.setOption(trendChartOption);
      console.log('[Anomalies] 异常时间趋势图更新成功（attack_sessions）:', trendData.length, '个时间点');
    }
  } catch (error) {
    console.error('[Anomalies] 更新异常时间趋势图失败:', error);
  }
};

// ✅ 更新各类攻击数据包统计图（按攻击类型统计，使用原始anomaly_log数据）
const updateTimelineChart = async () => {
  if (!timelineChartInstance || timelineChartInstance.isDisposed()) return;

  try {
    // 获取原始的anomaly_log数据（不去重）
    const response = await axios.get('/v1/anomalies', {
      params: { 
        hours: selectedPeriod.value,
        raw: true  // 获取原始数据
      }
    });
    
    let rawData = [];
    if (response.data.success && response.data.raw_data) {
      rawData = response.data.raw_data;  // 使用原始数据（1258条）
    } else {
      // 降级：使用去重后的显示数据
      rawData = anomalies.value || [];
    }
    
    console.log('[Anomalies] 各类攻击数据包统计使用数据:', rawData.length, '条');
  
    // ✅ 按攻击类型统计数据包数量
    const attackTypeStats: Record<string, number> = {};
    
    rawData.forEach((item: any) => {
      const type = item.type || item.anomaly_type || '其他';
      attackTypeStats[type] = (attackTypeStats[type] || 0) + 1;
    });
    
    // 转换为数组并排序（按数量降序）
    const sortedTypes = Object.entries(attackTypeStats)
      .sort((a, b) => b[1] - a[1])
      .map(([type, count]) => ({ type, count }));
    
    const attackTypes = sortedTypes.map(item => item.type);
    const attackCounts = sortedTypes.map(item => item.count);
    
    // 为不同攻击类型分配颜色
    const colors = ['#ff4d4f', '#faad14', '#52c41a', '#1890ff', '#722ed1', '#eb2f96', '#13c2c2'];
    const barColors = attackTypes.map((_, index) => colors[index % colors.length]);
    
    const timelineChartOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function (params: any) {
          const data = params[0];
          return `<strong>${data.axisValue}</strong><br/>${data.marker}数据包数量: <strong>${data.value}</strong>个`;
        }
      },
      grid: {
        left: '80px',  // ✅ 给Y轴标签留出足够空间
        right: '4%',
        bottom: '3%',
        top: '5%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: attackTypes,
        axisLabel: {
          rotate: attackTypes.length > 5 ? 30 : 0,
          fontSize: 12,
          fontWeight: 'bold'
        },
        axisTick: {
          alignWithLabel: true
        }
      },
      yAxis: {
        type: 'value',
        name: '数据包数量',
        minInterval: 1,
        axisLabel: { 
          fontSize: 11,
          formatter: '{value}'
        }
      },
      series: [
        {
          name: '数据包数量',
          type: 'bar',
          barWidth: '60%',
          data: attackCounts.map((count, index) => ({
            value: count,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: barColors[index] },
                { offset: 1, color: barColors[index] + '80' }
              ]),
              borderRadius: [6, 6, 0, 0]
            }
          })),
          label: {
            show: true,
            position: 'top',
            fontSize: 12,
            fontWeight: 'bold',
            formatter: '{c}'
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0,0,0,0.3)'
            }
          }
        }
      ]
    };
    
    timelineChartInstance.setOption(timelineChartOption);
    console.log('[Anomalies] 各类攻击数据包统计图更新成功:', sortedTypes);
    
  } catch (error) {
    console.error('[Anomalies] 更新各类攻击数据包统计图失败:', error);
  }
};

// 切换时间周期
const changeTimePeriod = (hours: number) => {
  selectedPeriod.value = hours;
  fetchAnomalies();
};

// 获取异常数据
const fetchAnomalies = async () => {
  try {
    // ✅ 先获取已处理的IP列表（限速+黑名单）
    await fetchHandledIPs();
    
    // ✅ 获取summary数据（包含anomaly_log的总数据包数）
    const { data: summaryData } = await ryuApi.getSummary();
    const totalPackets = summaryData?.today_anomalies || 0;  // anomaly_log的数据包总数
    console.log(`[Anomalies] anomaly_log今日数据包总数: ${totalPackets}`);
    
    // ✅ 查询attack_sessions表（获取所有数据，包括pending和handled）
    const response = await ryuApi.getAttackSessions(selectedPeriod.value, 1000);
    
    if (response && Array.isArray(response)) {
      console.log(`[Anomalies] 从attack_sessions获取到 ${response.length} 条记录（包括所有status）`);
      
      // ✅ 分离数据：全部数据用于图表，pending数据用于列表
      allAnomalies.value = response;  // 所有数据（用于图表）
      anomalies.value = response.filter(item => item.status === 'pending' || !item.status);  // pending数据（用于列表）
      
      console.log(`[Anomalies] 图表数据: ${allAnomalies.value.length} 条（全部）`);
      console.log(`[Anomalies] 列表数据: ${anomalies.value.length} 条（pending）`);
      
      // ✅ 计算统计（使用全部数据，并传入数据包总数）
      await calculateStats(allAnomalies.value, totalPackets);
      
      // 更新图表（使用allAnomalies，即全部数据）
      updateCharts();
      await updateTrendChart();
      await updateTimelineChart();
      
      console.log(`[Anomalies] 时间范围: 最近${selectedPeriod.value}小时（${selectedPeriod.value === 24 ? '今日0点至今' : ''}）`);
    }
  } catch (error) {
    console.error('[Anomalies] 获取异常数据失败:', error);
  }
};

// 处理操作按钮
const handleAction = async (ip: string, action: 'blacklist' | 'ratelimit') => {
  try {
    let result;
    
    if (action === 'blacklist') {
      // 加黑操作
      result = await ryuApi.addBlacklist(ip);
      if (result.success) {
        // ✅ 更新attack_sessions表的status为'handled'
        try {
          const statusResult = await ryuApi.updateAttackStatus(ip, 'blacklist');
          console.log(`[Anomalies] ✅ 已更新IP ${ip} 的攻击状态为handled，影响${statusResult.affected_rows}条记录`);
        } catch (error) {
          console.error(`[Anomalies] ⚠️ 更新攻击状态失败:`, error);
        }
        
        alert(`✅ IP ${ip} 已成功加入黑名单`);
        
        // ✅ 重新获取数据（数据库已过滤掉handled状态的记录）
        await fetchAnomalies();
      } else {
        alert(`❌ 加黑失败: ${result.message}`);
      }
    } else if (action === 'ratelimit') {
      // 限速操作
      result = await ryuApi.addRateLimit(ip);
      if (result.success) {
        // ✅ 更新attack_sessions表的status为'handled'
        try {
          const statusResult = await ryuApi.updateAttackStatus(ip, 'ratelimit');
          console.log(`[Anomalies] ✅ 已更新IP ${ip} 的攻击状态为handled，影响${statusResult.affected_rows}条记录`);
        } catch (error) {
          console.error(`[Anomalies] ⚠️ 更新攻击状态失败:`, error);
        }
        
        alert(`✅ IP ${ip} 已成功限速`);
        
        // ✅ 重新获取数据（数据库已过滤掉handled状态的记录）
        await fetchAnomalies();
      } else {
        alert(`❌ 限速失败: ${result.message}`);
      }
    }
  } catch (error) {
    console.error('操作失败:', error);
    alert('❌ 操作失败，请重试');
  }
};

// ✅ 从列表中移除指定IP的所有异常事件
// 窗口大小变化时重绘图表
const handleResize = () => {
  if (typeChartInstance && !typeChartInstance.isDisposed()) typeChartInstance.resize();
  if (sourceChartInstance && !sourceChartInstance.isDisposed()) sourceChartInstance.resize();
  if (trendChartInstance && !trendChartInstance.isDisposed()) trendChartInstance.resize();
  if (timelineChartInstance && !timelineChartInstance.isDisposed()) timelineChartInstance.resize();
};

onMounted(() => {
  // 初始加载数据
  fetchAnomalies();
  
  // 初始化图表
  initCharts();
  
  // 设置定时器
  anomaliesTimer = window.setInterval(fetchAnomalies, 5000); // 每5秒更新异常
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  // 清除定时器
  if (anomaliesTimer) window.clearInterval(anomaliesTimer);
  
  // 销毁图表实例
  if (typeChartInstance && !typeChartInstance.isDisposed()) typeChartInstance.dispose();
  if (sourceChartInstance && !sourceChartInstance.isDisposed()) sourceChartInstance.dispose();
  if (trendChartInstance && !trendChartInstance.isDisposed()) trendChartInstance.dispose();
  if (timelineChartInstance && !timelineChartInstance.isDisposed()) timelineChartInstance.dispose();
  
  // 移除事件监听
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
/* 样式通过Tailwind工具类实现 */
</style>