const JSON_HEADERS = { 'Content-Type': 'application/json' }

async function request (url, options = {}) {
  const res = await fetch(url, options)
  const isJson = res.headers.get('content-type')?.includes('application/json')
  const payload = isJson ? await res.json() : await res.text()
  if (!res.ok) {
    const detail = typeof payload === 'string' ? payload : payload?.detail
    throw new Error(detail || `请求失败 (${res.status})`)
  }
  return payload
}

export const api = {
  status: () => request('/api/status'),

  browse: (path) => request(`/api/browse${path ? `?path=${encodeURIComponent(path)}` : ''}`),

  run: ({ mode, paths, week }) => request('/api/run', {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({ mode, paths, week: week || null })
  }),

  listHistory: () => request('/api/history'),

  deleteHistory: (id) => request(`/api/history/${id}`, { method: 'DELETE' }),

  clearHistory: () => request('/api/history', { method: 'DELETE' })
}
