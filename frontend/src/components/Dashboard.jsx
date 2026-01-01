import React, { useState } from 'react'

const API_BASE = import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1'

function useApi() {
    const [token, setToken] = useState(null)

    async function login(payload) {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
        })
        return res.json()
    }

    async function getMembers(groupId) {
        const res = await fetch(`${API_BASE}/groups/${groupId}/members`, { headers: { 'Authorization': token ? `Bearer ${token}` : '' } })
        return res.json()
    }

    async function getBlacklist(groupId) {
        const res = await fetch(`${API_BASE}/groups/${groupId}/blacklist`, { headers: { 'Authorization': token ? `Bearer ${token}` : '' } })
        return res.json()
    }

    return { token, setToken, login, getMembers, getBlacklist }
}

export default function Dashboard() {
    const api = useApi()
    const [status, setStatus] = useState('Ready')
    const [user, setUser] = useState({ user_id: '', username: '', first_name: '' })
    const [groupId, setGroupId] = useState('')
    const [members, setMembers] = useState([])
    const [blacklist, setBlacklist] = useState([])

    async function handleLogin(e) {
        e.preventDefault()
        setStatus('Logging in...')
        const resp = await api.login({ user_id: Number(user.user_id), username: user.username, first_name: user.first_name })
        if (resp.ok) {
            api.setToken(resp.token)
            setStatus(`Logged in as ${resp.role}`)
        } else {
            setStatus('Login failed')
        }
    }

    async function loadMembers() {
        setStatus('Loading members...')
        const resp = await api.getMembers(Number(groupId))
        if (resp.ok) { setMembers(resp.members); setStatus(`Loaded ${resp.members.length} members`) }
        else setStatus('Failed to load members')
    }

    async function loadBlacklist() {
        setStatus('Loading blacklist...')
        const resp = await api.getBlacklist(Number(groupId))
        if (resp.ok) { setBlacklist(resp.entries); setStatus(`Loaded ${resp.entries.length} entries`) }
        else setStatus('Failed to load blacklist')
    }

    return (
        <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-1">
                    <h2 className="text-lg font-medium">Login</h2>
                    <form onSubmit={handleLogin} className="space-y-3 mt-3">
                        <input required value={user.user_id} onChange={e => setUser({ ...user, user_id: e.target.value })} className="w-full border p-2 rounded" placeholder="Telegram user id" />
                        <input required value={user.username} onChange={e => setUser({ ...user, username: e.target.value })} className="w-full border p-2 rounded" placeholder="username" />
                        <input required value={user.first_name} onChange={e => setUser({ ...user, first_name: e.target.value })} className="w-full border p-2 rounded" placeholder="first name" />
                        <button className="w-full py-2 bg-indigo-600 text-white rounded">Login</button>
                    </form>
                </div>

                <div className="md:col-span-2">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-medium">Actions</h2>
                        <div className="text-sm text-gray-500">Status: {status}</div>
                    </div>
                    <div className="mt-3 flex gap-3">
                        <input value={groupId} onChange={e => setGroupId(e.target.value)} className="flex-1 border p-2 rounded" placeholder="group id" />
                        <button onClick={loadMembers} className="px-4 py-2 bg-green-600 text-white rounded">Members</button>
                        <button onClick={loadBlacklist} className="px-4 py-2 bg-red-600 text-white rounded">Blacklist</button>
                    </div>

                    <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-gray-50 p-4 rounded">
                            <h3 className="font-semibold mb-2">Members</h3>
                            <div className="space-y-2 max-h-64 overflow-auto">
                                {members.length === 0 && <div className="text-sm text-gray-500">No members loaded</div>}
                                {members.map(m => (
                                    <div key={m.user_id} className="p-2 bg-white rounded shadow-sm">{m.user_id} — {m.username || m.first_name}</div>
                                ))}
                            </div>
                        </div>

                        <div className="bg-gray-50 p-4 rounded">
                            <h3 className="font-semibold mb-2">Blacklist</h3>
                            <div className="space-y-2 max-h-64 overflow-auto">
                                {blacklist.length === 0 && <div className="text-sm text-gray-500">No blacklist entries</div>}
                                {blacklist.map(e => (
                                    <div key={e.user_id} className="p-2 bg-white rounded shadow-sm">{e.user_id} — {e.username} — {e.reason}</div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
