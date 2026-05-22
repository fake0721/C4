export const buildAnomalyExportPayload = (records = []) => ({
  items: Array.isArray(records)
    ? records.map((item) => ({
        src_ip: item.src_ip,
        type: item.type || item.anomaly_type,
        severity: item.severity,
        detect_time: item.detect_time || item.time,
        status: item.status || 'pending',
        details: item.details,
        rate_kbps: item.rate_kbps,
      }))
    : [],
})
