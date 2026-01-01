export const API_BASE = (import.meta as any).env?.DEV ? 'http://localhost:8000/api/v1' : '/api/v1'

type LoginRequest = { user_id: number; username: string; first_name: string }
type LoginResponse = { ok: boolean; token?: string; role?: string; message?: string }

type MembersResponse = { ok: boolean; group_id: number; members: any[]; total_count: number; page: number; page_size: number }
type BlacklistResponse = { ok: boolean; group_id: number; entries: any[]; total_count: number; page: number; page_size: number }
type GroupsResponse = { ok: boolean; groups: any[]; total_count: number }
type AuditLogsResponse = { ok: boolean; group_id: number; logs: any[]; total_count: number; page: number; page_size: number }
type MetricsResponse = { ok: boolean; group_id: number; total_actions: number; actions_breakdown: Record<string, number>; last_action_at?: string }

function authHeaders(token?: string | null) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, { method: 'POST', headers: authHeaders(), body: JSON.stringify(payload) })
  return res.json()
}

export async function getGroups(token?: string | null): Promise<GroupsResponse> {
  const res = await fetch(`${API_BASE}/groups`, { headers: authHeaders(token) })
  return res.json()
}

export async function getMembers(groupId: number, token?: string | null): Promise<MembersResponse> {
  const res = await fetch(`${API_BASE}/groups/${groupId}/members?page=1&page_size=200`, { headers: authHeaders(token) })
  return res.json()
}

export async function getBlacklist(groupId: number, token?: string | null): Promise<BlacklistResponse> {
  const res = await fetch(`${API_BASE}/groups/${groupId}/blacklist?page=1&page_size=200`, { headers: authHeaders(token) })
  return res.json()
}

export async function getAuditLogs(groupId: number, token?: string | null): Promise<AuditLogsResponse> {
  const res = await fetch(`${API_BASE}/groups/${groupId}/logs?page=1&page_size=50`, { headers: authHeaders(token) })
  return res.json()
}

export async function getMetrics(groupId: number, token?: string | null): Promise<MetricsResponse> {
  const res = await fetch(`${API_BASE}/groups/${groupId}/metrics`, { headers: authHeaders(token) })
  return res.json()
}

export async function postAction(groupId: number, action: any, token?: string | null) {
  const res = await fetch(`${API_BASE}/groups/${groupId}/actions`, { method: 'POST', headers: authHeaders(token), body: JSON.stringify(action) })
  return res.json()
}
