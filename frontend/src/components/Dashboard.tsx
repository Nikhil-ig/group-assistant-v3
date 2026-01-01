import React, { useEffect, useState } from 'react'
import * as api from '../api/client'
import ActionModal from './ActionModal'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { UserMinusIcon } from '@heroicons/react/20/solid'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement)

type Member = {
    user_id: number
    username?: string | null
    first_name?: string | null
}

type BlacklistEntry = {
    user_id: number
    username?: string | null
    reason?: string | null
}

export default function Dashboard() {
    const [status, setStatus] = useState('Ready')
    const [user, setUser] = useState({ user_id: '', username: '', first_name: '' })
    const [groupId, setGroupId] = useState('')
    const [members, setMembers] = useState<Member[]>([])
    const [blacklist, setBlacklist] = useState<BlacklistEntry[]>([])
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
    const [actionModalOpen, setActionModalOpen] = useState(false)
    const [selectedMember, setSelectedMember] = useState<Member | null>(null)
    const [actionType, setActionType] = useState<'ban' | 'mute' | 'unmute' | 'kick'>('ban')
    const [metrics, setMetrics] = useState<any>(null)

    useEffect(() => { localStorage.setItem('token', token || '') }, [token])

    async function handleLogin(e: React.FormEvent) {
        e.preventDefault()
        setStatus('Logging in...')
        try {
            const resp = await api.login({ user_id: Number(user.user_id), username: user.username, first_name: user.first_name })
            if (resp.ok) { setToken(resp.token || null); setStatus(`Logged in as ${resp.role}`) }
            else setStatus(`Login failed: ${resp.message || 'unknown'}`)
        } catch (err: any) { setStatus(`Login error: ${err.message || String(err)}`) }
    }

    function handleLogout() {
        setToken(null)
        localStorage.removeItem('token')
        setStatus('Logged out')
    }

    async function loadMembers() {
        setStatus('Loading members...')
        try {
            const resp = await api.getMembers(Number(groupId), token)
            if (resp.ok) { setMembers(resp.members); setStatus(`Loaded ${resp.members.length} members`) }
            else setStatus(`Failed to load members: ${resp}`)
        } catch (err: any) { setStatus(`Members error: ${err.message || String(err)}`) }
    }

    async function loadBlacklist() {
        setStatus('Loading blacklist...')
        try {
            const resp = await api.getBlacklist(Number(groupId), token)
            if (resp.ok) { setBlacklist(resp.entries); setStatus(`Loaded ${resp.entries.length} entries`) }
            else setStatus(`Failed to load blacklist: ${resp}`)
        } catch (err: any) { setStatus(`Blacklist error: ${err.message || String(err)}`) }
    }

    async function loadMetrics() {
        try {
            const res = await fetch(`${api.API_BASE}/groups/${groupId}/metrics`, { headers: { 'Authorization': token ? `Bearer ${token}` : '' } })
            const j = await res.json()
            if (j.ok) setMetrics(j)
        } catch (e) { }
    }

    function openActionModal(actionType: 'ban' | 'mute' | 'unmute' | 'kick', targetMember: Member) {
        setSelectedMember(targetMember)
        setActionType(actionType)
        setActionModalOpen(true)
    }

    async function confirmAction(action: any) {
        setStatus('Performing action...')
        try {
            const resp = await api.postAction(Number(groupId), action, token)
            if (resp.ok) {
                setStatus('Action success')
                setActionModalOpen(false)
                loadMembers()
                loadBlacklist()
                loadMetrics()
            }
            else setStatus('Action failed')
        } catch (e: any) {
            setStatus(`Action error: ${e.message || String(e)}`)
        }
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
                        <div className="flex gap-2">
                            <button className="flex-1 py-2 bg-indigo-600 text-white rounded">Login</button>
                            <button type="button" onClick={handleLogout} className="py-2 px-3 bg-gray-200 rounded">Logout</button>
                        </div>
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
                        <button onClick={loadMetrics} className="px-4 py-2 bg-sky-600 text-white rounded">Metrics</button>
                    </div>

                    <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-gray-50 p-4 rounded">
                            <h3 className="font-semibold mb-2">Members</h3>
                            <div className="space-y-2 max-h-64 overflow-auto">
                                {members.length === 0 && <div className="text-sm text-gray-500">No members loaded</div>}
                                {members.map(m => (
                                    <div key={m.user_id} className="p-2 bg-white rounded shadow-sm flex items-center justify-between">
                                        <div>{m.user_id} — {m.username || m.first_name}</div>
                                        <div className="flex gap-2">
                                            <button title="Ban" onClick={() => openActionModal('ban', m)} className="p-1 rounded bg-red-600 text-white">
                                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                                                    <path d="M12 2a10 10 0 100 20 10 10 0 000-20zm4.95 13.95A8 8 0 1110.05 7.05l6.9 6.9z" />
                                                    <path d="M7.05 6.05l10.9 10.9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                                                </svg>
                                            </button>
                                            <button title="Mute" onClick={() => openActionModal('mute', m)} className="p-1 rounded bg-yellow-500 text-white"><UserMinusIcon className="h-5 w-5" /></button>
                                        </div>
                                    </div>
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
            <div className="p-6">
                {metrics && (
                    <div className="bg-white p-4 rounded shadow">
                        <h4 className="font-semibold mb-2">Actions (recent)</h4>
                        <Bar data={{ labels: Object.keys(metrics.actions || {}), datasets: [{ label: 'Actions', data: Object.values(metrics.actions || {}), backgroundColor: 'rgba(59,130,246,0.6)' }] }} />
                    </div>
                )}
            </div>
            {selectedMember && (
                <ActionModal
                    isOpen={actionModalOpen}
                    onClose={() => setActionModalOpen(false)}
                    onConfirm={confirmAction}
                    member={{
                        user_id: selectedMember.user_id,
                        username: selectedMember.username ?? undefined,
                        first_name: selectedMember.first_name ?? undefined
                    }}
                    defaultActionType={actionType}
                    groupId={Number(groupId)}
                />
            )}
        </div>
    )
}
