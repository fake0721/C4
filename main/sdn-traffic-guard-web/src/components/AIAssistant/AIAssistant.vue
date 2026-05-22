<template>
  <div class="h-screen flex bg-gray-50">
    <!-- 左侧对话列表 -->
    <div class="w-64 bg-white flex flex-col border-r border-gray-200 shadow-sm">
      <!-- Logo区域 -->
      <div class="p-4 border-b border-gray-200">
        <div class="flex items-center space-x-3">
          <div class="relative">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg">
              <i class="fas fa-robot text-white text-base"></i>
            </div>
            <div class="absolute -bottom-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white shadow-sm"></div>
          </div>
  <div>
            <h1 class="text-sm font-semibold text-gray-900">SDN Guardian</h1>
            <p class="text-xs text-gray-500">AI 助手</p>
          </div>
        </div>
      </div>
      
      <!-- 新建对话按钮 -->
      <div class="p-3">
        <button 
          @click="createNewChat"
          class="w-full px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all flex items-center justify-center space-x-2 text-sm font-medium shadow-md">
          <i class="fas fa-plus"></i>
          <span>新建对话</span>
        </button>
      </div>
      
      <!-- 对话历史列表 -->
      <div class="flex-1 overflow-y-auto px-3 py-2">
        <div class="text-xs font-semibold text-gray-500 mb-2 px-2">对话历史</div>
        <div 
          v-for="(conv, index) in conversations" 
          :key="index"
          @click="switchConversation(index)"
          :class="currentConversationIndex === index ? 'bg-blue-50 text-blue-700 border-l-3 border-blue-600' : 'text-gray-700 hover:bg-gray-50'"
          class="px-3 py-2.5 rounded-lg cursor-pointer transition-all mb-1 group">
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium truncate">{{ conv.title || '新对话' }}</p>
              <p class="text-xs text-gray-500 truncate mt-0.5">{{ conv.preview || '开始对话...' }}</p>
            </div>
            <button 
              @click.stop="deleteConversation(index)"
              class="opacity-0 group-hover:opacity-100 ml-2 text-gray-400 hover:text-red-500 transition-opacity">
              <i class="fas fa-trash text-xs"></i>
            </button>
          </div>
        </div>
        
        <!-- 空状态 -->
        <div v-if="conversations.length === 0" class="text-center py-8 text-gray-400 text-sm">
          <i class="fas fa-comments text-2xl mb-2"></i>
          <p>暂无对话历史</p>
        </div>
      </div>
      
      <!-- 底部功能按钮 -->
      <div class="p-3 border-t border-gray-200">
        <button 
          @click="showCommandList = !showCommandList"
          :class="showCommandList ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'"
          class="w-full px-3 py-2 rounded-lg transition-all flex items-center space-x-2 text-sm mb-2">
          <i class="fas fa-book"></i>
          <span>指令列表</span>
        </button>
        <button 
          @click="clearHistory"
          class="w-full px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-all flex items-center space-x-2 text-sm">
          <i class="fas fa-trash-alt"></i>
          <span>清空当前对话</span>
        </button>
      </div>
    </div>
    
    <!-- 右侧主内容区 -->
    <div class="flex-1 flex flex-col">
      <!-- 顶部导航栏 -->
      <div class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm">
        <div class="flex items-center space-x-3">
          <h2 class="text-base font-semibold text-gray-900">
            {{ currentConversation.title || '新对话' }}
          </h2>
          <span class="text-xs text-gray-500">Qwen2.5</span>
        </div>
        
        <div class="flex items-center space-x-2 text-xs text-gray-500">
          <button
            @click="showExportDialog = true"
            class="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 border border-blue-100 hover:bg-blue-100 transition-colors font-medium"
          >
            <i class="fas fa-download mr-1"></i>导出本次分析结果
          </button>
          <span v-if="isAdmin" class="px-2 py-1 bg-yellow-50 text-yellow-700 rounded-md border border-yellow-200 font-medium">
            <i class="fas fa-crown mr-1"></i>管理员
          </span>
          <span>{{ currentUser?.username || '游客' }}</span>
        </div>
      </div>

      <ExportDialog
        v-model="showExportDialog"
        title="导出 AI 研判报告"
        default-type="ai_analysis"
        :default-hours="24"
        :export-types="aiExportTypes"
        :filters="{ source: 'ai-assistant', conversation_id: currentConversation.id, title: currentConversation.title }"
        :payload="aiExportPayload"
      />

      <!-- 指令列表面板 - 卡片设计 -->
      <div v-if="showCommandList" class="bg-white border-b border-gray-200">
        <div class="max-w-4xl mx-auto px-6 py-6">
          <div class="flex items-center justify-between mb-5">
            <div>
              <h3 class="text-base font-semibold text-gray-900">常用指令</h3>
              <p class="text-xs text-gray-500 mt-1">快速了解AI助手的能力</p>
            </div>
            <button @click="showCommandList = false" class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
              <i class="fas fa-times"></i>
            </button>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- 管理员指令 -->
          <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
            <div class="flex items-center mb-3">
              <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center mr-2">
                <i class="fas fa-user-shield text-white text-sm"></i>
              </div>
              <h4 class="font-semibold text-gray-900">管理员指令</h4>
            </div>
            <ul class="space-y-2 text-sm text-gray-700">
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-blue-500 text-xs mt-1 mr-2"></i>
                <div>
                  <div class="font-medium">手动限速 IP 速率 原因</div>
                  <div class="text-xs text-gray-500">例: 手动限速 192.168.1.100 1024 SYN Flood</div>
                </div>
              </li>
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-blue-500 text-xs mt-1 mr-2"></i>
                <div>
                  <div class="font-medium">加黑 IP 原因</div>
                  <div class="text-xs text-gray-500">例: 加黑 192.168.1.99 ARP欺骗</div>
                </div>
              </li>
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-blue-500 text-xs mt-1 mr-2"></i>
                <div>
                  <div class="font-medium">解除限速 IP</div>
                  <div class="text-xs text-gray-500">例: 解除限速 192.168.1.100</div>
                </div>
              </li>
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-blue-500 text-xs mt-1 mr-2"></i>
                <span>查询黑名单 / 查询白名单</span>
              </li>
              <li class="flex items-start">
                <i class="fas fa-lightbulb text-yellow-500 text-xs mt-1 mr-2"></i>
                <span class="text-xs text-gray-600">💡 直接输入命令，无需 "ai:" 前缀和 "原因:" 关键字</span>
              </li>
            </ul>
          </div>
          
          <!-- 智能对话 -->
          <div class="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-100">
            <div class="flex items-center mb-3">
              <div class="w-8 h-8 rounded-lg bg-purple-600 flex items-center justify-center mr-2">
                <i class="fas fa-comments text-white text-sm"></i>
              </div>
              <h4 class="font-semibold text-gray-900">智能对话</h4>
            </div>
            <ul class="space-y-2 text-sm text-gray-700">
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-purple-500 text-xs mt-1 mr-2"></i>
                <span>你好，请介绍一下自己</span>
              </li>
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-purple-500 text-xs mt-1 mr-2"></i>
                <span>当前网络状态如何？</span>
              </li>
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-purple-500 text-xs mt-1 mr-2"></i>
                <span>最近有哪些异常？</span>
              </li>
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-purple-500 text-xs mt-1 mr-2"></i>
                <span>我叫[你的名字]</span>
              </li>
            </ul>
          </div>
          
          <!-- 系统查询 -->
          <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100">
            <div class="flex items-center mb-3">
              <div class="w-8 h-8 rounded-lg bg-green-600 flex items-center justify-center mr-2">
                <i class="fas fa-chart-line text-white text-sm"></i>
              </div>
              <h4 class="font-semibold text-gray-900">系统查询</h4>
            </div>
            <ul class="space-y-2 text-sm text-gray-700">
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-green-500 text-xs mt-1 mr-2"></i>
                <span>查看当前限速IP</span>
              </li>
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-green-500 text-xs mt-1 mr-2"></i>
                <span>查看黑名单列表</span>
              </li>
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-green-500 text-xs mt-1 mr-2"></i>
                <span>查看白名单列表</span>
              </li>
              <li class="flex items-start">
                <i class="fas fa-chevron-right text-green-500 text-xs mt-1 mr-2"></i>
                <span>生成安全报告</span>
              </li>
            </ul>
          </div>
          </div>
        </div>
      </div>

      <!-- 聊天区域 -->
      <div class="flex-1 overflow-hidden flex flex-col bg-gray-50">
        <div ref="chatHistoryRef" class="flex-1 overflow-y-auto">
          <div class="max-w-4xl mx-auto px-6 py-8">
          <!-- 欢迎消息 - 有特色的设计 -->
          <div v-if="currentConversation.messages.length === 0 && !isLoading" class="text-center py-16">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-600 shadow-xl shadow-blue-500/30 mb-6">
              <i class="fas fa-robot text-white text-2xl"></i>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-2">欢迎使用 SDN Guardian AI</h3>
            <p class="text-gray-600 mb-6">我可以帮助您管理网络、执行指令和回答问题</p>
            <div class="flex flex-wrap justify-center gap-2 max-w-2xl mx-auto">
              <div class="px-4 py-2 bg-white rounded-lg shadow-sm border border-gray-200 text-sm text-gray-700 hover:shadow-md transition-shadow cursor-pointer">
                💬 查看当前限速IP
              </div>
              <div class="px-4 py-2 bg-white rounded-lg shadow-sm border border-gray-200 text-sm text-gray-700 hover:shadow-md transition-shadow cursor-pointer">
                🛡️ 查看黑名单列表
              </div>
              <div class="px-4 py-2 bg-white rounded-lg shadow-sm border border-gray-200 text-sm text-gray-700 hover:shadow-md transition-shadow cursor-pointer">
                📊 生成安全报告
              </div>
            </div>
          </div>
          
          <!-- 消息列表 -->
          <div v-for="(message, index) in currentConversation.messages" :key="index" class="mb-6">
            <!-- AI消息（左边） -->
            <div v-if="message.role === 'assistant'" class="flex justify-start">
              <div class="flex items-start space-x-3 max-w-[85%]">
                <div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-600 flex items-center justify-center flex-shrink-0 shadow-lg">
                  <i class="fas fa-robot text-white text-sm"></i>
                </div>
                <div class="flex-1">
            <!-- Agent分析结果界面 -->
            <div v-if="isAgentAnalysis(message.content)" class="bg-white rounded-2xl rounded-tl-md p-5 shadow-sm border border-blue-200">
              <div v-if="parseAgentAnalysis(message.content)" class="space-y-4">
                <!-- 标题 -->
                <div class="flex items-center space-x-2 pb-3 border-b border-gray-200">
                  <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                    <i class="fas fa-robot text-white text-sm"></i>
                  </div>
                  <div>
                    <h3 class="text-base font-semibold text-gray-900">Agent 智能分析报告</h3>
                    <p class="text-xs text-gray-500">RAG + MCP + LLM</p>
                  </div>
                </div>

                <div v-bind="parseAgentAnalysis(message.content)" class="space-y-3">
                  <!-- 基本信息 -->
                  <div class="bg-gray-50 rounded-lg p-3">
                    <div class="grid grid-cols-2 gap-2 text-sm">
                      <div><span class="text-gray-600">异常类型:</span> <span class="font-medium">{{ parseAgentAnalysis(message.content).anomaly_type }}</span></div>
                      <div><span class="text-gray-600">源IP:</span> <span class="font-medium">{{ parseAgentAnalysis(message.content).src_ip }}</span></div>
                    </div>
                  </div>

                  <!-- 分析结果 -->
                  <div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-3 border border-blue-100">
                    <h4 class="font-semibold text-gray-900 mb-2 flex items-center">
                      <i class="fas fa-brain text-blue-500 mr-2"></i>
                      智能分析结果
                    </h4>
                    <div class="space-y-2 text-sm">
                      <div class="flex items-center space-x-2">
                        <span class="text-gray-600">风险等级:</span>
                        <span :class="getRiskLevelClass(parseAgentAnalysis(message.content).analysis?.risk_level)" class="px-2 py-0.5 rounded font-medium">
                          {{ parseAgentAnalysis(message.content).analysis?.risk_level }}
                        </span>
                      </div>
                      <div class="flex items-center space-x-2">
                        <span class="text-gray-600">置信度:</span>
                        <div class="flex-1 bg-white rounded-full h-2 overflow-hidden">
                          <div :style="{width: parseAgentAnalysis(message.content).analysis?.confidence + '%'}" class="h-full bg-gradient-to-r from-blue-500 to-purple-500"></div>
                        </div>
                        <span class="font-medium">{{ parseAgentAnalysis(message.content).analysis?.confidence }}%</span>
                      </div>
                      <div class="flex items-start space-x-2">
                        <span class="text-gray-600">建议措施:</span>
                        <span class="font-medium text-blue-600">{{ parseAgentAnalysis(message.content).analysis?.recommended_action }}</span>
                      </div>
                      <div v-if="parseAgentAnalysis(message.content).analysis?.reason" class="pt-2 border-t border-blue-100">
                        <p class="text-gray-700 text-xs leading-relaxed">{{ parseAgentAnalysis(message.content).analysis?.reason }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- RAG知识源 -->
                  <div v-if="parseAgentAnalysis(message.content).knowledge_count > 0" class="bg-green-50 rounded-lg p-3 border border-green-100">
                    <h4 class="font-semibold text-gray-900 mb-2 flex items-center">
                      <i class="fas fa-book text-green-500 mr-2"></i>
                      知识库检索 ({{ parseAgentAnalysis(message.content).knowledge_count }}条)
                    </h4>
                    <div class="space-y-1 text-xs text-gray-600">
                      <div v-for="(source, idx) in parseAgentAnalysis(message.content).knowledge_sources?.slice(0, 2)" :key="idx" class="bg-white rounded p-2">
                        {{ source.substring(0, 100) }}...
                      </div>
                    </div>
                  </div>

                  <!-- MCP工具调用 -->
                  <div class="bg-yellow-50 rounded-lg p-3 border border-yellow-100">
                    <h4 class="font-semibold text-gray-900 mb-2 flex items-center">
                      <i class="fas fa-tools text-yellow-500 mr-2"></i>
                      MCP工具调用
                    </h4>
                    <div class="flex flex-wrap gap-1">
                      <span v-for="tool in parseAgentAnalysis(message.content).tools_used" :key="tool" class="px-2 py-1 bg-white rounded text-xs font-medium text-gray-700">
                        {{ tool }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 交互式数据界面 -->
            <div v-else-if="isInteractiveData(message.content)" class="bg-white rounded-2xl rounded-tl-md p-4 shadow-sm border border-gray-200">
              <template v-if="parseInteractiveData(message.content)">
                <!-- 周报下载界面 -->
                <div v-if="parseInteractiveData(message.content).type === 'report_download'" class="text-center py-6">
                  <div class="mb-4">
                    <i class="fas fa-file-pdf text-6xl text-red-500 mb-3"></i>
                  </div>
                  <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ parseInteractiveData(message.content).title }}</h3>
                  <p class="text-sm text-gray-600 mb-6">{{ parseInteractiveData(message.content).message }}</p>
                  <button 
                    @click="downloadReport(parseInteractiveData(message.content).download_url, parseInteractiveData(message.content).filename)"
                    class="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors flex items-center space-x-2 mx-auto shadow-lg">
                    <i class="fas fa-download"></i>
                    <span>下载PDF周报</span>
                  </button>
                </div>
                
                <!-- 列表数据界面（黑白名单、限速） -->
                <div v-else>
                  <div class="mb-3 pb-3 border-b border-gray-200">
                    <h3 class="text-base font-semibold text-gray-900">{{ parseInteractiveData(message.content).title }}</h3>
                  </div>
                  <div class="space-y-3">
                    <div 
                      v-for="item in parseInteractiveData(message.content).data" 
                      :key="item.index"
                      class="flex items-start justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      <div class="flex-1 space-y-1">
                        <div class="font-medium text-gray-900">【{{ item.index }}】{{ item.ip }}</div>
                        <div class="text-sm text-gray-600">
                          <span v-if="item.status">状态：{{ item.status }}</span>
                          <span v-if="item.expire_str"> | 过期：{{ item.expire_str }}</span>
                          <span v-if="item.kbps">限速：{{ item.kbps }} KB/s</span>
                          <span v-if="item.reason"> | 原因：{{ item.reason }}</span>
                          <span v-if="item.ttl_str"> | 剩余：{{ item.ttl_str }}</span>
                        </div>
                      </div>
                      <button 
                        @click="handleInteractiveAction(item.action, item.ip)"
                        class="ml-3 px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white text-sm rounded-lg transition-colors flex items-center space-x-1">
                        <i class="fas fa-trash text-xs"></i>
                        <span>删除</span>
                      </button>
                    </div>
                  </div>
                  <div class="mt-3 pt-3 border-t border-gray-200 text-sm text-gray-500">
                    共 {{ parseInteractiveData(message.content).total }} 项
                  </div>
                </div>
              </template>
            </div>
                  <!-- 普通文本消息 -->
                  <div v-else class="bg-white rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-gray-200">
                    <p class="text-sm leading-relaxed text-gray-900 whitespace-pre-wrap">{{ message.content }}</p>
                  </div>
                  <div class="flex items-center mt-1 px-2">
                    <span class="text-xs text-gray-500">{{ formatTime(message.timestamp) }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 用户消息（右边） -->
            <div v-else class="flex justify-end">
              <div class="flex items-start space-x-3 max-w-[75%]">
                <div class="flex-1">
                  <div class="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-2xl rounded-tr-md px-4 py-3 shadow-md">
                    <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ message.content }}</p>
                  </div>
                  <div class="flex items-center justify-end mt-1 px-2">
                    <span class="text-xs text-gray-400">{{ formatTime(message.timestamp) }}</span>
                  </div>
                </div>
                <!-- 用户头像 -->
                <div v-if="currentUser?.avatar" class="w-9 h-9 rounded-full flex-shrink-0 shadow-md overflow-hidden border-2 border-blue-200">
                  <img :src="currentUser.avatar" :alt="currentUser.username" class="w-full h-full object-cover" />
                </div>
                <div v-else class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-sm font-semibold flex-shrink-0 shadow-md">
                  {{ (currentUser?.username || 'U').charAt(0).toUpperCase() }}
                </div>
            </div>
          </div>
        </div>
        
        <!-- 加载中指示器 -->
          <div v-if="isLoading" class="flex justify-start mb-6">
            <div class="flex items-start space-x-3 max-w-[75%]">
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 via-purple-600 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-sm">
                <i class="fas fa-robot text-white text-sm"></i>
              </div>
              <div class="flex-1">
                <div class="bg-white rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-gray-200">
                  <div class="flex space-x-1.5">
              <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></div>
              <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 0.2s"></div>
              <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 0.4s"></div>
                  </div>
                </div>
              </div>
            </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="border-t border-gray-200 bg-white shadow-lg">
        <!-- 上传的文件预览 -->
        <div v-if="uploadedFile" class="border-b border-gray-200 px-6 py-3 bg-blue-50">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <i class="fas fa-file-pdf text-blue-600"></i>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-900">{{ uploadedFile.name }}</p>
                <p class="text-xs text-gray-600">{{ (uploadedFile.size / 1024).toFixed(2) }} KB</p>
              </div>
            </div>
            <button 
              @click="uploadedFile = null"
              class="p-2 text-gray-400 hover:text-red-500 transition-colors">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
        
        <div class="max-w-4xl mx-auto px-6 py-4">
          <div class="flex items-end space-x-3">
            <!-- 文件上传按钮 -->
            <div class="relative">
              <input 
                ref="fileInputRef"
                type="file"
                accept=".pdf,.txt,.csv,.docx"
                @change="handleFileUpload"
                style="display: none"
              />
              <button 
                @click="fileInputRef?.click()"
                :class="uploadedFile ? 'bg-green-500 hover:bg-green-600' : 'bg-gray-500 hover:bg-gray-600'"
                class="p-3.5 rounded-xl text-white transition-all shadow-md hover:shadow-lg transform hover:scale-105 active:scale-95"
                :title="uploadedFile ? '已选择文件' : '上传文档'">
                <i :class="uploadedFile ? 'fas fa-check' : 'fas fa-paperclip'"></i>
              </button>
            </div>
            
            <div class="flex-1">
              <div class="relative">
                <textarea 
            v-model="userInput" 
                  placeholder="直接输入命令，例如：加黑 192.168.1.100 ARP欺骗 | 手动限速 192.168.1.99 1024 SYN Flood (Ctrl+Enter 发送)" 
                  class="w-full border-2 border-gray-200 rounded-xl px-4 py-3 pr-12 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 resize-none text-sm transition-all"
                  :class="userInput.length > 450 ? 'border-orange-300' : ''"
                  rows="1"
                  @keydown.ctrl.enter="sendMessage"
                  @keydown.enter.exact.prevent
                  @input="autoResize"
                ></textarea>
                <!-- 字数提示 -->
                <div class="absolute right-3 bottom-3 text-xs" :class="userInput.length > 450 ? 'text-orange-500 font-medium' : 'text-gray-400'">
                  {{ userInput.length }}/500
                </div>
              </div>
            </div>
          <button 
            @click="sendMessage" 
              class="p-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-blue-600 disabled:hover:to-blue-700 transition-all shadow-md hover:shadow-lg transform hover:scale-105 active:scale-95"
              :disabled="isLoading || !userInput.trim() || userInput.length > 500"
              title="发送消息">
              <i class="fas fa-paper-plane text-base"></i>
          </button>
        </div>
          <div class="flex items-center justify-between mt-2.5 px-1">
            <div class="flex items-center space-x-3 text-xs text-gray-500">
              <span v-if="isAdmin" class="flex items-center px-2 py-1 bg-yellow-50 text-yellow-700 rounded-md border border-yellow-200">
                <i class="fas fa-crown mr-1.5"></i>管理员权限
              </span>
              <span class="flex items-center">
                <i class="fas fa-keyboard mr-1.5"></i>Ctrl+Enter 快速发送
              </span>
            </div>
            <span class="text-xs text-gray-400">
              <i class="fas fa-shield-alt mr-1"></i>对话已加密
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import axios from 'axios'
import ryuApi from '@/api/ryu'
import ExportDialog from '@/components/common/ExportDialog.vue'

// 定义消息结构
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

interface FrontendAction {
  type: 'navigate' | 'open_export_dialog' | 'open_report_export_dialog' | 'execute_report_export' | 'show_command_list' | string
  path?: string
  page?: string
  reason?: string
  export_type?: string
  title?: string
  hours?: number
  format?: string
}

// 定义对话结构
interface Conversation {
  id: string
  title: string
  preview: string
  messages: ChatMessage[]
  createdAt: number
  updatedAt: number
}

// Store
const userStore = useUserStore()
const router = useRouter()

// 响应式数据
const conversations = ref<Conversation[]>([])
const currentConversationIndex = ref(0)
const userInput = ref('')
const isLoading = ref(false)
const chatHistoryRef = ref<HTMLElement | null>(null)
const showCommandList = ref(false)
const uploadedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const showExportDialog = ref(false)
const aiExportTypes = [
  { label: 'AI 研判报告', value: 'ai_analysis' }
]

// 计算属性
const currentUser = computed(() => userStore.user)
const isAdmin = computed(() => userStore.user?.role === 'admin')
const userId = computed(() => userStore.user?.id?.toString() || 'anonymous')
// ✅ 使用username而不是id，因为数据库id字段和模型定义不一致
const username = computed(() => userStore.user?.username || 'anonymous')
const currentConversation = computed(() => {
  if (conversations.value.length === 0) {
    return {
      id: 'default',
      title: '新对话',
      preview: '',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
  }
  return conversations.value[currentConversationIndex.value] || conversations.value[0]
})
const aiExportPayload = computed(() => ({
  messages: currentConversation.value.messages.map(message => ({
    role: message.role === 'assistant' ? 'AI助手' : '用户',
    content: message.content
      .replace('__INTERACTIVE_DATA__\n', '')
      .replace('__AGENT_ANALYSIS__\n', ''),
    timestamp: formatTime(message.timestamp)
  }))
}))

// 格式化时间
const formatTime = (timestamp: number): string => {
  const date = new Date(timestamp * 1000)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  
  if (messageDate.getTime() === today.getTime()) {
    // 今天的消息只显示时间
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
      minute: '2-digit'
    })
  } else {
    // 其他日期显示日期+时间
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

// 生成对话标题
const generateTitle = (message: string): string => {
  // 简单的标题生成逻辑：取前20个字符
  if (message.length > 20) {
    return message.substring(0, 20) + '...'
  }
  return message
}

// 创建新对话
const createNewChat = () => {
  const newConversation: Conversation = {
    id: Date.now().toString(),
    title: '新对话',
    preview: '开始对话...',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now()
  }
  conversations.value.unshift(newConversation)
  currentConversationIndex.value = 0
  saveConversations()
}

// 切换对话
const switchConversation = (index: number) => {
  currentConversationIndex.value = index
  nextTick(() => {
    scrollToBottom()
  })
}

// 删除对话
const deleteConversation = (index: number) => {
  conversations.value.splice(index, 1)
  if (currentConversationIndex.value >= conversations.value.length) {
    currentConversationIndex.value = Math.max(0, conversations.value.length - 1)
  }
  if (conversations.value.length === 0) {
    createNewChat()
  }
  saveConversations()
}

// 保存对话到 localStorage
const saveConversations = () => {
  try {
    localStorage.setItem(`ai_conversations_${userId.value}`, JSON.stringify(conversations.value))
  } catch (error) {
    console.error('[AI助手] 保存对话失败:', error)
  }
}

// 加载对话从 localStorage
const loadConversations = () => {
  try {
    const saved = localStorage.getItem(`ai_conversations_${userId.value}`)
    if (saved) {
      conversations.value = JSON.parse(saved)
    }
    if (conversations.value.length === 0) {
      createNewChat()
    }
  } catch (error) {
    console.error('[AI助手] 加载对话失败:', error)
    createNewChat()
  }
}

// 处理文件上传
const handleFileUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    const file = input.files[0]
    
    // 验证文件大小（10MB）
    if (file.size > 10 * 1024 * 1024) {
      alert('文件大小不能超过10MB')
      return
    }
    
    // 验证文件类型
    const allowedTypes = ['application/pdf', 'text/plain', 'text/csv', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if (!allowedTypes.includes(file.type)) {
      alert('不支持的文件格式，请上传 PDF、TXT、CSV 或 DOCX 文件')
      return
    }
    
    console.log('[📄] 文件已选择:', file.name, file.size)
    
    // 【新增】先检查知识库中是否已存在该文件
    console.log('[🔍] 检查知识库中是否已存在该文件...')
    try {
      const checkResponse = await fetch(`/v1/knowledge/check?filename=${encodeURIComponent(file.name)}`)
      const checkData = await checkResponse.json()
      
      if (checkData.exists) {
        // 文件已存在，直接使用，不下载
        console.log('[✅] 文件已在知识库中:', file.name)
        uploadedFile.value = file
        console.log('[💡] 知识库中已有该文件，无需重复下载')
        return
      }
    } catch (error) {
      console.warn('[⚠️] 检查文件失败:', error)
      // 继续上传
    }
    
    // 【新增】文件不存在，才进行上传
    console.log('[📤] 文件不在知识库中，开始上传...')
    const uploadResult = await uploadFileToRAG(file)
    
    if (uploadResult.success) {
      console.log('[✅] 文件已上传到知识库:', uploadResult)
      uploadedFile.value = file
      // 【新增】只有新上传的文件才显示提示
      alert(`✅ 新文件已添加到知识库\n📄 文件: ${file.name}\n📦 分块数: ${uploadResult.chunks_count}`)
    } else {
      console.warn('[⚠️] 文件上传失败:', uploadResult.message)
      alert(`❌ 文件上传失败: ${uploadResult.message}`)
    }
  }
}

// 上传文件到RAG知识库
const uploadFileToRAG = async (file: File) => {
  try {
    console.log('[📤] 开始上传文件到RAG:', file.name)
    
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch('/v1/knowledge/upload', {
      method: 'POST',
      body: formData
    })
    
    const data = await response.json()
    
    if (data.success) {
      console.log('[✅] 文件上传成功:', data)
      return {
        success: true,
        filename: data.filename,
        chunks_count: data.chunks_count
      }
    } else {
      console.error('[❌] 文件上传失败:', data.message)
      return {
        success: false,
        message: data.message
      }
    }
  } catch (error: any) {
    console.error('[❌] 文件上传异常:', error)
    return {
      success: false,
      message: error.message
    }
  }
}

const normalizeExportFormat = (format?: string) => {
  return (format || '').toLowerCase() === 'docx' ? 'docx' : 'pdf'
}

const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

const buildReportExportPayload = async (exportType: string, hours: number) => {
  if (exportType === 'anomalies' || exportType === 'attack_sessions') {
    const records = await ryuApi.getAttackSessions(hours, 1000)
    const items = Array.isArray(records) ? records : []
    return {
      items: items.map((item: any) => ({
        src_ip: item.src_ip,
        type: item.type || item.anomaly_type,
        severity: item.severity,
        detect_time: item.detect_time || item.time,
        status: item.status || 'pending',
        details: item.details,
        rate_kbps: item.rate_kbps
      }))
    }
  }

  return { items: [] }
}

const executeReportExport = async (action: FrontendAction) => {
  const exportType = action.export_type || 'anomalies'
  const format = normalizeExportFormat(action.format)
  const hours = typeof action.hours === 'number' ? action.hours : 24
  const payload = await buildReportExportPayload(exportType, hours)

  const response = await ryuApi.createExportTask({
    export_type: exportType,
    format,
    filters: {
      source: 'ai-assistant-functioncalling',
      hours
    },
    payload
  })

  const downloadResponse = await ryuApi.downloadExportFile(response.download_url)
  const filename = response.task?.filename || `${exportType}.${format}`
  downloadBlob(downloadResponse.data, filename)
}

const handleFrontendActions = async (actions: FrontendAction[]) => {
  for (const action of actions) {
    if (action.type === 'navigate' && action.path) {
      showNotification('success', '正在跳转页面', action.reason || `即将打开 ${action.path}`)
      await router.push(action.path)
      continue
    }

    if (action.type === 'execute_report_export') {
      try {
        showNotification('success', '正在导出报告', action.reason || '正在生成并下载报告文件')
        await executeReportExport(action)
        showNotification('success', '导出完成', `${action.title || '报告'} 已开始下载`)
      } catch (error: any) {
        console.error('[AI助手] 报告导出失败:', error)
        showNotification('error', '导出失败', error.response?.data?.detail || error.message || '请稍后重试')
      }
      continue
    }

    if (action.type === 'open_report_export_dialog') {
      const exportRequest = {
        path: action.path,
        export_type: action.export_type,
        title: action.title,
        hours: action.hours,
        format: action.format,
        reason: action.reason,
        requested_at: Date.now()
      }

      sessionStorage.setItem('ai_pending_export_dialog', JSON.stringify(exportRequest))
      showNotification('success', '正在打开业务报表导出', action.reason || '即将打开对应页面的导出窗口')

      if (action.path && router.currentRoute.value.path !== action.path) {
        await router.push(action.path)
      } else {
        window.dispatchEvent(new CustomEvent('ai:open-export-dialog', { detail: exportRequest }))
      }
      continue
    }

    if (action.type === 'open_export_dialog') {
      showExportDialog.value = true
      showNotification('success', '已打开导出面板', action.reason || '可以继续选择导出范围和格式')
      continue
    }

    if (action.type === 'show_command_list') {
      showCommandList.value = true
      showNotification('success', '已展开功能列表', action.reason || '你可以查看 AI 助手可执行的系统操作')
      continue
    }

    console.warn('[AI助手] 未识别的前端动作:', action)
  }
}

// 发送消息
const sendMessage = async () => {
  const message = userInput.value.trim()
  if (!message || isLoading.value || message.length > 500) return
  
  // 确保有当前对话
  if (conversations.value.length === 0) {
    createNewChat()
  }
  
  const conv = conversations.value[currentConversationIndex.value]
  
  // 如果是新对话的第一条消息，更新标题
  if (conv.messages.length === 0) {
    conv.title = generateTitle(message)
  }
  
  // 添加用户消息到当前对话
  const userMessage: ChatMessage = {
    role: 'user',
    content: message,
    timestamp: Math.floor(Date.now() / 1000)
  }
  conv.messages.push(userMessage)
  conv.preview = message.length > 30 ? message.substring(0, 30) + '...' : message
  conv.updatedAt = Date.now()
  
  // 清空输入框
  userInput.value = ''
  
  // 设置加载状态
  isLoading.value = true
  
  // 滚动到底部
  await scrollToBottom()
  
  try {
    // 保存上传的文件名（在清空前）
    const uploadedFileName = uploadedFile.value ? uploadedFile.value.name : null
    const hasUploadedFile = uploadedFile.value ? true : false
    
    // 先添加一个临时的AI消息，用于流式更新
    const aiMessage: ChatMessage = {
      role: 'assistant',
      content: hasUploadedFile ? '📄 正在分析您上传的文档...' : '🤔 正在分析问题...',
      timestamp: Math.floor(Date.now() / 1000)
    }
    conv.messages.push(aiMessage)
    conv.updatedAt = Date.now()
    
    // 清空已上传的文件
    uploadedFile.value = null
    
    // 发送请求到后端（包含上传的文件信息）
    const response = await fetch('/v1/chat/with-tools', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: username.value,
        user: message,
        has_uploaded_file: hasUploadedFile,
        uploaded_filename: uploadedFileName
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('[AI助手] 后端响应:', data)

    if (Array.isArray(data.frontend_actions) && data.frontend_actions.length > 0) {
      aiMessage.content = data.response || '正在执行界面操作...'
      await handleFrontendActions(data.frontend_actions)
      return
    }
    
    if (data.status === 'success') {
      // 成功响应
      aiMessage.content = data.response
      const toolsCalled = data.tools_called || []
      const toolResults = data.tool_results || {}
      
      console.log('[AI助手] 调用的工具:', toolsCalled)
      console.log('[AI助手] 工具结果:', toolResults)
    } else if (data.status === 'error') {
      // 错误响应
      aiMessage.content = `错误: ${data.message || data.response || '未知错误'}`
    } else {
      // 其他响应
      aiMessage.content = data.response || '无法获取响应'
    }
    
  } catch (error: any) {
    console.error('[AI助手] 发送消息失败:', error)
    
    // 添加错误消息
    const errorMessage: ChatMessage = {
      role: 'assistant',
      content: `抱歉，处理您的请求时出现了错误：${error.response?.data?.message || error.message || '未知错误'}`,
      timestamp: Math.floor(Date.now() / 1000)
    }
    conv.messages.push(errorMessage)
    
  } finally {
    // 取消加载状态
    isLoading.value = false
    
    // 保存对话
    saveConversations()
    
    // 滚动到底部
    await scrollToBottom()
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatHistoryRef.value) {
    chatHistoryRef.value.scrollTo({
      top: chatHistoryRef.value.scrollHeight,
      behavior: 'smooth'
    })
  }
}


// 清空当前对话记录
const clearHistory = async () => {
  if (!confirm('确定要清空当前对话记录吗？这将删除所有消息，但不会删除对话本身。')) return
  
  try {
    // 清空当前对话的消息
    const conv = conversations.value[currentConversationIndex.value]
    if (conv) {
      conv.messages = []
      conv.title = '新对话'
      conv.preview = '开始对话...'
      conv.updatedAt = Date.now()
      saveConversations()
    }
    
    // 同时清空后端记录
    // ✅ 使用username而不是user_id
    await axios.post('/v1/chat', {
      username: username.value,
      user: 'ai: 清空记忆'
    })
    
    console.log('[AI助手] 聊天记录已清空')
    
  } catch (error: any) {
    console.error('[AI助手] 清空记录失败:', error)
    alert('清空记录失败：' + (error.response?.data?.message || error.message))
  }
}

// 检查是否是交互式数据
const isInteractiveData = (content: string): boolean => {
  return content.startsWith('__INTERACTIVE_DATA__')
}

// 解析交互式数据
const parseInteractiveData = (content: string): any => {
  try {
    const jsonStr = content.replace('__INTERACTIVE_DATA__\n', '')
    return JSON.parse(jsonStr)
  } catch (error) {
    console.error('[AI助手] 解析交互式数据失败:', error)
    return null
  }
}

// 检查是否是Agent分析结果
const isAgentAnalysis = (content: string): boolean => {
  return content.startsWith('__AGENT_ANALYSIS__')
}

// 解析Agent分析结果
const parseAgentAnalysis = (content: string): any => {
  try {
    const jsonStr = content.replace('__AGENT_ANALYSIS__\n', '')
    return JSON.parse(jsonStr)
  } catch (error) {
    console.error('[AI助手] 解析Agent分析失败:', error)
    return null
  }
}

// 获取风险等级样式
const getRiskLevelClass = (level: string): string => {
  const levelMap: Record<string, string> = {
    '低': 'bg-green-100 text-green-700',
    '中': 'bg-yellow-100 text-yellow-700',
    '高': 'bg-orange-100 text-orange-700',
    '严重': 'bg-red-100 text-red-700',
    '极高': 'bg-purple-100 text-purple-700'
  }
  return levelMap[level] || 'bg-gray-100 text-gray-700'
}

// 处理交互式操作（直接调用DELETE API，不通过聊天接口）
const handleInteractiveAction = async (action: string, ip: string) => {
  console.log(`[AI助手] 执行操作: ${action} on ${ip}`)
  
  let apiUrl = ''
  let actionName = ''
  
  if (action === 'delete_black') {
    apiUrl = `/v1/acl/black/${ip}`
    actionName = '从黑名单移除'
  } else if (action === 'delete_white') {
    apiUrl = `/v1/acl/white/${ip}`
    actionName = '从白名单移除'
  } else if (action === 'release_limit') {
    apiUrl = `/v1/limit/ip/${ip}`
    actionName = '解除限速'
  }
  
  if (!apiUrl) return
  
  if (!confirm(`确定要${actionName} ${ip} 吗？`)) return
  
  isLoading.value = true
  
  try {
    // ✅ 直接调用DELETE API（不通过聊天接口）
    const response = await axios.delete(apiUrl)
    
    console.log('[AI助手] API响应:', response.data)
    
    // 检查操作结果
    const isSuccess = response.data.success === true
    const message = response.data.message || ''
    
    // 显示操作结果提示
    if (isSuccess) {
      // 成功提示（绿色）
      showNotification('success', `✅ ${actionName}成功`, message)
    } else {
      // 失败提示（红色）
      showNotification('error', `❌ ${actionName}失败`, message)
    }
    
    // 如果成功，刷新列表
    if (isSuccess) {
      // 找到当前显示的交互式消息
      const conv = conversations.value[currentConversationIndex.value]
      const lastMessage = conv.messages[conv.messages.length - 1]
      
      // 如果最后一条消息是交互式数据，直接替换它
      if (lastMessage && isInteractiveData(lastMessage.content)) {
        let queryCommand = ''
        if (action.includes('black')) {
          queryCommand = '查看黑名单列表'
        } else if (action.includes('white')) {
          queryCommand = '查看白名单列表'
        } else if (action.includes('limit')) {
          queryCommand = '查看当前限速'
        }
        
        if (queryCommand) {
          // 直接调用后端查询，获取新数据
          // ✅ 使用username而不是user_id
          const queryResponse = await axios.post('/v1/chat', {
            username: username.value,
            user: queryCommand
          })
          
          // 更新最后一条消息的内容为新的查询结果
          lastMessage.content = queryResponse.data.reply || queryResponse.data.response || ''
          lastMessage.timestamp = Math.floor(Date.now() / 1000)
          
          saveConversations()
          await scrollToBottom()
        }
      }
    }
    
  } catch (error: any) {
    console.error('[AI助手] 操作失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '未知错误'
    showNotification('error', `❌ 操作失败`, errorMsg)
  } finally {
    isLoading.value = false
  }
}

// 下载周报PDF
const downloadReport = async (downloadUrl: string, filename: string) => {
  try {
    showNotification('success', '正在生成周报...', '请稍候，正在生成PDF文件')
    
    // 调用后端API生成PDF
    const response = await axios.get(downloadUrl, {
      responseType: 'blob'  // 重要：以blob格式接收
    })
    
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    
    // 清理
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    showNotification('success', '✅ 下载成功', `周报 ${filename} 已保存到您的下载文件夹`)
    
  } catch (error: any) {
    console.error('[AI助手] 下载周报失败:', error)
    showNotification('error', '❌ 下载失败', error.response?.data?.error || error.message || '未知错误')
  }
}

// 显示通知提示
const showNotification = (type: 'success' | 'error', title: string, message: string) => {
  // 创建通知元素
  const notification = document.createElement('div')
  notification.className = `fixed top-20 right-6 z-50 px-6 py-4 rounded-lg shadow-lg border transition-all duration-300 max-w-md ${
    type === 'success' 
      ? 'bg-green-50 border-green-200 text-green-800' 
      : 'bg-red-50 border-red-200 text-red-800'
  }`
  
  notification.innerHTML = `
    <div class="flex items-start space-x-3">
      <div class="flex-shrink-0">
        ${type === 'success' 
          ? '<i class="fas fa-check-circle text-green-500 text-xl"></i>' 
          : '<i class="fas fa-exclamation-circle text-red-500 text-xl"></i>'
        }
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-semibold">${title}</p>
        <p class="text-xs mt-1 opacity-90">${message}</p>
      </div>
      <button onclick="this.parentElement.parentElement.remove()" class="flex-shrink-0 text-gray-400 hover:text-gray-600">
        <i class="fas fa-times"></i>
      </button>
    </div>
  `
  
  document.body.appendChild(notification)
  
  // 3秒后自动消失
  setTimeout(() => {
    notification.style.opacity = '0'
    notification.style.transform = 'translateX(100%)'
    setTimeout(() => notification.remove(), 300)
  }, 3000)
}

// 自动调整输入框高度
const autoResize = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  target.style.height = 'auto'
  target.style.height = Math.min(target.scrollHeight, 200) + 'px'
}

// 监听当前对话变化，自动滚动到底部
watch(() => currentConversation.value.messages, () => {
  scrollToBottom()
}, { deep: true })

// 生命周期
onMounted(async () => {
  console.log('[AI助手] 组件挂载，当前用户:', currentUser.value)
  
  // 加载对话列表
  loadConversations()
  
  // 初始滚动到底部
  await scrollToBottom()
})

onUnmounted(() => {
  console.log('[AI助手] 组件卸载')
})
</script>

<style scoped>
/* 样式通过Tailwind工具类实现 */
</style>
