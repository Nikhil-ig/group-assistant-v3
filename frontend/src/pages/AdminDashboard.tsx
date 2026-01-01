import React, { useEffect, useState } from 'react'
import { getGroups, getMembers, getBlacklist, postAction, getAuditLogs, getMetrics } from '../api/client'
import { UserCircleIcon, ArrowLeftOnRectangleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import ActionModal from '../components/ActionModal'

type AdminDashboardProps = {
    token: string
    userId: number
    username: string
    role: string
    onLogout: () => void
}

type Group = {
    group_id: number
    group_name: string
    created_at: string
    is_active: boolean
}

type Member = {
    user_id: number
    username?: string
    first_name?: string
    is_bot?: boolean
    last_seen?: string
}

type AuditLog = {
    action_type: string
    admin_username: string
    target_username?: string
    reason?: string
    timestamp: string
}

type Metrics = {
    total_actions: number
    actions_breakdown: Record<string, number>
    last_action_at?: string
}

export default function AdminDashboard({ token, userId, username, role, onLogout }: AdminDashboardProps) {
    const [groups, setGroups] = useState<Group[]>([])
    const [selectedGroup, setSelectedGroup] = useState<Group | null>(null)
    const [members, setMembers] = useState<Member[]>([])
    const [blacklist, setBlacklist] = useState<any[]>([])
    const [logs, setLogs] = useState<AuditLog[]>([])
    const [metrics, setMetrics] = useState<Metrics | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [activeTab, setActiveTab] = useState('members')
    const [actionModalOpen, setActionModalOpen] = useState(false)
    const [selectedMember, setSelectedMember] = useState<Member | null>(null)
    const [actionType, setActionType] = useState<'ban' | 'mute' | 'unmute' | 'kick'>('ban')

    // Load groups on mount
    useEffect(() => {
        loadGroups()
    }, [])

    async function loadGroups() {
        setLoading(true)
        setError('')
        try {
            const response = await getGroups(token)
            if (response.ok) {
                setGroups(response.groups)
                if (response.groups.length > 0 && !selectedGroup) {
                    selectGroup(response.groups[0])
                }
            } else {
                setError('Failed to load groups')
            }
        } catch (err: any) {
            setError(err.message || 'Error loading groups')
        } finally {
            setLoading(false)
        }
    }

    async function selectGroup(group: Group) {
        setSelectedGroup(group)
        setActiveTab('members')
        loadGroupData(group.group_id)
    }

    async function loadGroupData(groupId: number) {
        setLoading(true)
        setError('')
        try {
            const [membersRes, blacklistRes, logsRes, metricsRes] = await Promise.all([
                getMembers(groupId, token),
                getBlacklist(groupId, token),
                getAuditLogs(groupId, token),
                getMetrics(groupId, token),
            ])

            if (membersRes.ok) setMembers(membersRes.members)
            if (blacklistRes.ok) setBlacklist(blacklistRes.entries)
            if (logsRes.ok) setLogs(logsRes.logs)
            if (metricsRes.ok) setMetrics(metricsRes)
        } catch (err: any) {
            setError(err.message || 'Error loading group data')
        } finally {
            setLoading(false)
        }
    }

    async function handleAction(action: any) {
        if (!selectedGroup || !selectedMember) return
        setLoading(true)
        try {
            const response = await postAction(selectedGroup.group_id, action, token)
            if (response.ok) {
                setActionModalOpen(false)
                // Reload group data
                loadGroupData(selectedGroup.group_id)
            } else {
                setError('Action failed')
            }
        } catch (err: any) {
            setError(err.message || 'Error performing action')
        } finally {
            setLoading(false)
        }
    }

    function openActionModal(member: Member, type: 'ban' | 'mute' | 'unmute' | 'kick') {
        setSelectedMember(member)
        setActionType(type)
        setActionModalOpen(true)
    }

    if (!selectedGroup) {
        return (
            <div className="min-h-screen bg-gray-50">
                <nav className="bg-white shadow-sm">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                        <h1 className="text-2xl font-bold text-gray-900">Guardian Bot Admin</h1>
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                                <UserCircleIcon className="h-5 w-5" />
                                <span className="text-sm">{username}</span>
                                <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded">{role}</span>
                            </div>
                            <button onClick={onLogout} className="flex items-center gap-2 text-red-600 hover:text-red-700">
                                <ArrowLeftOnRectangleIcon className="h-5 w-5" />
                                Logout
                            </button>
                        </div>
                    </div>
                </nav>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <h2 className="text-lg font-semibold mb-4">Select a Group</h2>
                    {loading && <p className="text-gray-500">Loading groups...</p>}
                    {error && <div className="p-4 bg-red-50 text-red-700 rounded-lg mb-4">{error}</div>}

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {groups.map((group) => (
                            <button
                                key={group.group_id}
                                onClick={() => selectGroup(group)}
                                className="text-left p-4 bg-white rounded-lg shadow hover:shadow-md transition border-2 border-transparent hover:border-indigo-500"
                            >
                                <h3 className="font-semibold text-gray-900">{group.group_name}</h3>
                                <p className="text-sm text-gray-500">ID: {group.group_id}</p>
                                <p className="text-xs text-gray-400 mt-2">Created: {new Date(group.created_at).toLocaleDateString()}</p>
                            </button>
                        ))}
                    </div>

                    {groups.length === 0 && !loading && (
                        <div className="text-center py-8">
                            <ExclamationTriangleIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                            <p className="text-gray-500">No groups found. You may not have permission to manage any groups.</p>
                        </div>
                    )}
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <nav className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                    <div>
                        <button onClick={() => setSelectedGroup(null)} className="text-indigo-600 hover:text-indigo-700 text-sm font-medium">
                            ← Back to Groups
                        </button>
                        <h1 className="text-2xl font-bold text-gray-900 mt-1">{selectedGroup.group_name}</h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <UserCircleIcon className="h-5 w-5" />
                            <span className="text-sm">{username}</span>
                            <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded">{role}</span>
                        </div>
                        <button onClick={onLogout} className="flex items-center gap-2 text-red-600 hover:text-red-700">
                            <ArrowLeftOnRectangleIcon className="h-5 w-5" />
                            Logout
                        </button>
                    </div>
                </div>
            </nav>

            {/* Stats */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {error && <div className="p-4 bg-red-50 text-red-700 rounded-lg mb-4">{error}</div>}

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-white rounded-lg shadow p-6">
                        <p className="text-gray-500 text-sm">Total Members</p>
                        <p className="text-3xl font-bold text-gray-900">{members.length}</p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <p className="text-gray-500 text-sm">Banned</p>
                        <p className="text-3xl font-bold text-red-600">{blacklist.length}</p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <p className="text-gray-500 text-sm">Total Actions</p>
                        <p className="text-3xl font-bold text-indigo-600">{metrics?.total_actions || 0}</p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <p className="text-gray-500 text-sm">Recent Logs</p>
                        <p className="text-3xl font-bold text-blue-600">{logs.length}</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="bg-white rounded-lg shadow">
                    <div className="border-b border-gray-200 flex">
                        {['members', 'blacklist', 'logs', 'metrics'].map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`px-4 py-3 font-medium text-sm ${activeTab === tab
                                        ? 'text-indigo-600 border-b-2 border-indigo-600'
                                        : 'text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            </button>
                        ))}
                    </div>

                    <div className="p-6">
                        {loading && <p className="text-gray-500">Loading...</p>}

                        {/* Members Tab */}
                        {activeTab === 'members' && (
                            <div>
                                <h3 className="text-lg font-semibold mb-4">Group Members</h3>
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead>
                                            <tr className="border-b border-gray-200">
                                                <th className="text-left py-3 px-4 font-semibold text-gray-900">User ID</th>
                                                <th className="text-left py-3 px-4 font-semibold text-gray-900">Username</th>
                                                <th className="text-left py-3 px-4 font-semibold text-gray-900">Name</th>
                                                <th className="text-right py-3 px-4 font-semibold text-gray-900">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {members.map((member) => (
                                                <tr key={member.user_id} className="border-b border-gray-100 hover:bg-gray-50">
                                                    <td className="py-3 px-4 text-gray-900">{member.user_id}</td>
                                                    <td className="py-3 px-4 text-gray-600">@{member.username}</td>
                                                    <td className="py-3 px-4 text-gray-600">{member.first_name}</td>
                                                    <td className="py-3 px-4 text-right">
                                                        <div className="flex gap-2 justify-end">
                                                            <button
                                                                onClick={() => openActionModal(member, 'ban')}
                                                                className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition"
                                                            >
                                                                Ban
                                                            </button>
                                                            <button
                                                                onClick={() => openActionModal(member, 'mute')}
                                                                className="px-3 py-1 text-sm bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 transition"
                                                            >
                                                                Mute
                                                            </button>
                                                            <button
                                                                onClick={() => openActionModal(member, 'kick')}
                                                                className="px-3 py-1 text-sm bg-orange-100 text-orange-700 rounded hover:bg-orange-200 transition"
                                                            >
                                                                Kick
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {/* Blacklist Tab */}
                        {activeTab === 'blacklist' && (
                            <div>
                                <h3 className="text-lg font-semibold mb-4">Blacklist</h3>
                                <div className="space-y-2">
                                    {blacklist.length === 0 && <p className="text-gray-500">No banned users</p>}
                                    {blacklist.map((entry) => (
                                        <div key={entry.user_id} className="p-4 bg-red-50 rounded-lg border border-red-200">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <p className="font-semibold text-gray-900">ID: {entry.user_id}</p>
                                                    <p className="text-sm text-gray-600">@{entry.username}</p>
                                                    {entry.reason && <p className="text-sm text-gray-500 mt-1">Reason: {entry.reason}</p>}
                                                </div>
                                                <button
                                                    onClick={() => {
                                                        const member: Member = {
                                                            user_id: entry.user_id,
                                                            username: entry.username,
                                                        }
                                                        openActionModal(member, 'unmute')
                                                    }}
                                                    className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 transition"
                                                >
                                                    Unban
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Logs Tab */}
                        {activeTab === 'logs' && (
                            <div>
                                <h3 className="text-lg font-semibold mb-4">Audit Logs</h3>
                                <div className="space-y-2">
                                    {logs.length === 0 && <p className="text-gray-500">No logs found</p>}
                                    {logs.map((log, idx) => (
                                        <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <p className="font-semibold text-gray-900">
                                                        {log.action_type.toUpperCase()} by @{log.admin_username}
                                                    </p>
                                                    <p className="text-sm text-gray-600">Target: @{log.target_username}</p>
                                                    {log.reason && <p className="text-sm text-gray-500 mt-1">Reason: {log.reason}</p>}
                                                    <p className="text-xs text-gray-400 mt-2">{new Date(log.timestamp).toLocaleString()}</p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Metrics Tab */}
                        {activeTab === 'metrics' && (
                            <div>
                                <h3 className="text-lg font-semibold mb-4">Metrics & Statistics</h3>
                                {metrics ? (
                                    <div>
                                        <div className="mb-6 p-4 bg-indigo-50 rounded-lg">
                                            <p className="text-gray-600">Total Actions</p>
                                            <p className="text-3xl font-bold text-indigo-600">{metrics.total_actions}</p>
                                            {metrics.last_action_at && (
                                                <p className="text-sm text-gray-500 mt-2">Last action: {new Date(metrics.last_action_at).toLocaleString()}</p>
                                            )}
                                        </div>

                                        <h4 className="font-semibold text-gray-900 mb-3">Actions Breakdown</h4>
                                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                            {Object.entries(metrics.actions_breakdown).map(([action, count]) => (
                                                <div key={action} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                                                    <p className="text-sm text-gray-600">{action}</p>
                                                    <p className="text-2xl font-bold text-gray-900">{count as number}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ) : (
                                    <p className="text-gray-500">No metrics available</p>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Action Modal */}
            {selectedMember && (
                <ActionModal
                    isOpen={actionModalOpen}
                    onClose={() => setActionModalOpen(false)}
                    onConfirm={handleAction}
                    member={selectedMember}
                    defaultActionType={actionType}
                    groupId={selectedGroup.group_id}
                />
            )}
        </div>
    )
}
