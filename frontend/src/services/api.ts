const BASE_URL = '/api/v1'

export async function fetchHealth() {
  const res = await fetch(`${BASE_URL}/health`)
  if (!res.ok) throw new Error('API unreachable')
  return res.json() as Promise<{
    status: string
    app: string
    debug: boolean
    weaviate_url: string
  }>
}