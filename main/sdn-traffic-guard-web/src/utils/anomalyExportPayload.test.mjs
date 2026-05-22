import assert from 'node:assert/strict'

import { buildAnomalyExportPayload } from './anomalyExportPayload.js'

const records = [
  {
    src_ip: '10.0.0.1',
    anomaly_type: 'SYN Flood',
    severity: 'high',
    time: '2026-05-17 10:00:00',
    details: 'burst traffic',
    rate_kbps: 1024,
  },
]

assert.deepEqual(buildAnomalyExportPayload(records), {
  items: [
    {
      src_ip: '10.0.0.1',
      type: 'SYN Flood',
      severity: 'high',
      detect_time: '2026-05-17 10:00:00',
      status: 'pending',
      details: 'burst traffic',
      rate_kbps: 1024,
    },
  ],
})
