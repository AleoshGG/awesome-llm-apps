const mxnFormatter = new Intl.NumberFormat('es-MX', {
  style: 'currency',
  currency: 'MXN',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const dateFormatter = new Intl.DateTimeFormat('es-MX', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

/**
 * Convierte centavos enteros (ej. 149900) a formato moneda MXN (ej. "$1,499.00").
 */
export function formatCentsToMXN(cents: number): string {
  return mxnFormatter.format(cents / 100)
}

/**
 * Formatea una cadena ISO 8601 a fecha legible en español de México.
 */
export function formatIsoDate(isoDate: string): string {
  const parsed = new Date(isoDate)
  if (Number.isNaN(parsed.getTime())) {
    return isoDate
  }
  return dateFormatter.format(parsed)
}
