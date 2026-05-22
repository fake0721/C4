const TIME_FIELDS = ['detect_time', 'time', 'timestamp', 'created_at', 'start_time']

const toPositiveHours = (hours) => {
  const value = Number(hours)
  return Number.isFinite(value) && value > 0 ? value : null
}

const parseTimeValue = (value) => {
  if (value === null || value === undefined || value === '') return null

  if (typeof value === 'number') {
    const timestamp = value > 1_000_000_000_000 ? value : value * 1000
    const date = new Date(timestamp)
    return Number.isNaN(date.getTime()) ? null : date
  }

  const text = String(value).trim()
  if (!text) return null

  const normalized = text.includes('T') ? text : text.replace(' ', 'T')
  const parsed = new Date(normalized)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

const getRowTime = (row) => {
  if (!row || typeof row !== 'object') return null

  for (const field of TIME_FIELDS) {
    const parsed = parseTimeValue(row[field])
    if (parsed) return parsed
  }

  return null
}

export const filterExportRowsByHours = (rows, hours, now = new Date()) => {
  if (!Array.isArray(rows)) return []

  const positiveHours = toPositiveHours(hours)
  if (!positiveHours) return rows

  const cutoff = now.getTime() - positiveHours * 60 * 60 * 1000
  return rows.filter((row) => {
    const rowTime = getRowTime(row)
    return !rowTime || rowTime.getTime() >= cutoff
  })
}

export const buildTimeFilteredExportPayload = (payload = {}, hours, now = new Date()) => {
  if (Array.isArray(payload.items)) {
    return {
      ...payload,
      items: filterExportRowsByHours(payload.items, hours, now),
    }
  }

  if (Array.isArray(payload.messages)) {
    return {
      ...payload,
      messages: filterExportRowsByHours(payload.messages, hours, now),
    }
  }

  return payload
}

export const countTimeFilteredExportRows = (payload = {}, hours, now = new Date()) => {
  const filteredPayload = buildTimeFilteredExportPayload(payload, hours, now)
  const rows = filteredPayload.items || filteredPayload.messages || []
  return Array.isArray(rows) ? rows.length : 0
}
