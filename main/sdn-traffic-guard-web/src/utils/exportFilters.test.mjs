import assert from 'node:assert/strict'

import {
  buildTimeFilteredExportPayload,
  countTimeFilteredExportRows,
} from './exportFilters.js'

const now = new Date('2026-05-17T12:00:00')
const payload = {
  items: [
    { src_ip: '10.0.0.1', detect_time: '2026-05-17 10:00:00' },
    { src_ip: '10.0.0.2', detect_time: '2026-05-15 10:00:00' },
  ],
}

assert.equal(countTimeFilteredExportRows(payload, 24, now), 1)
assert.deepEqual(buildTimeFilteredExportPayload(payload, 24, now), {
  items: [{ src_ip: '10.0.0.1', detect_time: '2026-05-17 10:00:00' }],
})
assert.equal(countTimeFilteredExportRows(payload, 0, now), 2)
