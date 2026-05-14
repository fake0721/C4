<template>
  <div v-if="modelValue" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
    <div class="w-full max-w-lg rounded-2xl bg-white shadow-2xl">
      <div class="flex items-center justify-between border-b border-gray-100 px-6 py-4">
        <div>
          <h3 class="text-lg font-bold text-gray-900">{{ title }}</h3>
          <p class="mt-1 text-sm text-gray-500">选择导出内容、时间范围和文件格式</p>
        </div>
        <button class="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600" @click="close">
          <i class="fa fa-times"></i>
        </button>
      </div>

      <div class="space-y-5 px-6 py-5">
        <div>
          <label class="mb-2 block text-sm font-semibold text-gray-700">导出内容</label>
          <select
            v-model="selectedType"
            class="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
          >
            <option v-for="item in exportTypes" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
        </div>

        <div>
          <label class="mb-2 block text-sm font-semibold text-gray-700">时间范围</label>
          <select
            v-model.number="selectedHours"
            class="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
          >
            <option :value="24">最近一天</option>
            <option :value="72">最近三天</option>
            <option :value="168">最近七天</option>
            <option :value="0">不限时间</option>
          </select>
        </div>

        <div>
          <label class="mb-2 block text-sm font-semibold text-gray-700">文件格式</label>
          <div class="grid grid-cols-2 gap-3">
            <button
              v-for="format in formats"
              :key="format"
              type="button"
              class="rounded-xl border px-4 py-3 text-sm font-semibold transition"
              :class="selectedFormat === format ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
              @click="selectedFormat = format"
            >
              {{ format.toUpperCase() }}
            </button>
          </div>
        </div>

        <div class="rounded-xl bg-gray-50 p-4 text-sm text-gray-600">
          <div class="flex items-center justify-between">
            <span>预计导出记录</span>
            <span class="font-bold text-gray-900">{{ rowCount }} 条</span>
          </div>
          <p class="mt-2 text-xs text-gray-500">导出完成后会自动下载，并在后端记录任务与审计日志。</p>
        </div>

        <div v-if="message" class="rounded-xl px-4 py-3 text-sm" :class="messageClass">
          {{ message }}
        </div>
      </div>

      <div class="flex justify-end gap-3 border-t border-gray-100 px-6 py-4">
        <button class="rounded-xl px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100" :disabled="loading" @click="close">
          取消
        </button>
        <button
          class="rounded-xl bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-500/20 transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="loading"
          @click="submitExport"
        >
          <span v-if="loading">正在导出...</span>
          <span v-else>开始导出</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ryuApi from '@/api/ryu'

interface ExportTypeOption {
  label: string
  value: string
}

const props = withDefaults(defineProps<{
  modelValue: boolean
  title?: string
  exportTypes: ExportTypeOption[]
  defaultType?: string
  defaultHours?: number
  payload?: Record<string, any>
  filters?: Record<string, any>
}>(), {
  title: '导出报告',
  defaultHours: 24,
  payload: () => ({}),
  filters: () => ({})
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: [task: Record<string, any>]
}>()

const formats = ['pdf', 'docx']
const selectedType = ref(props.defaultType || props.exportTypes[0]?.value || 'anomalies')
const selectedFormat = ref('pdf')
const selectedHours = ref(props.defaultHours)
const loading = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error' | 'info'>('info')

const rowCount = computed(() => {
  const items = props.payload?.items || props.payload?.messages || []
  return Array.isArray(items) ? items.length : 0
})

const messageClass = computed(() => {
  if (messageType.value === 'success') return 'bg-green-50 text-green-700'
  if (messageType.value === 'error') return 'bg-red-50 text-red-700'
  return 'bg-blue-50 text-blue-700'
})

watch(() => props.modelValue, (visible) => {
  if (visible) {
    selectedType.value = props.defaultType || props.exportTypes[0]?.value || 'anomalies'
    selectedHours.value = props.defaultHours
    selectedFormat.value = 'pdf'
    message.value = ''
    messageType.value = 'info'
  }
})

const close = () => {
  if (!loading.value) emit('update:modelValue', false)
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

const submitExport = async () => {
  loading.value = true
  message.value = '正在生成导出文件，请稍候...'
  messageType.value = 'info'

  try {
    const filters = {
      ...props.filters,
      hours: selectedHours.value || undefined
    }
    const response = await ryuApi.createExportTask({
      export_type: selectedType.value,
      format: selectedFormat.value,
      filters,
      payload: props.payload
    })

    const downloadResponse = await ryuApi.downloadExportFile(response.download_url)
    const filename = response.task?.filename || `export.${selectedFormat.value}`
    downloadBlob(downloadResponse.data, filename)

    message.value = response.audit_warning || '导出成功，文件已开始下载。'
    messageType.value = response.audit_warning ? 'info' : 'success'
    emit('success', response.task)
    setTimeout(() => emit('update:modelValue', false), 800)
  } catch (error: any) {
    message.value = error.response?.data?.detail || error.message || '导出失败，请稍后重试'
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}
</script>
