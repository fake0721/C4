export function filterExportRowsByHours<T extends Record<string, any>>(
  rows: T[] | undefined,
  hours: number | undefined,
  now?: Date,
): T[]

export function buildTimeFilteredExportPayload<T extends Record<string, any>>(
  payload: T | undefined,
  hours: number | undefined,
  now?: Date,
): T

export function countTimeFilteredExportRows(
  payload: Record<string, any> | undefined,
  hours: number | undefined,
  now?: Date,
): number
