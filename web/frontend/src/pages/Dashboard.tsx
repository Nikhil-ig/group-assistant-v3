import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8001/api';

interface DashboardStats {
    total_groups: number;
    total_members: number;
    total_admins: number;
    total_actions: number;
    active_users: number;
    actions_today: number;
    actions_this_week: number;
}

interface Group {
    group_id: number;
    group_name: string;
    description?: string;
    member_count: number;
    admin_count: number;
    created_at: string;
    is_active: boolean;
}

interface User {
    user_id: number;
    username: string;
    first_name: string;
    last_name: string;
    role: string;
    email: string;
    managed_groups: number[];
    is_active: boolean;
}

interface Action {
    action_id: string;
    action_type: string;
    group_id: number;
    target_username: string;
    reason?: string;
    status: string;
    created_at: string;
}

/**
 * Dashboard Component
 * Main dashboard showing groups, users, actions, and statistics
 */
export const Dashboard: React.FC = () => {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [groups, setGroups] = useState<Group[]>([]);
    const [users, setUsers] = useState<User[]>([]);
    const [recentActions, setRecentActions] = useState<Action[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'groups' | 'users' | 'actions'>('overview');

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            setError(null);

            const token = localStorage.getItem('auth_token');
            const headers = token ? { Authorization: `Bearer ${token}` } : {};

            const [statsRes, groupsRes, usersRes, actionsRes] = await Promise.all([
                axios.get(`${API_BASE_URL}/dashboard/stats`, { headers }),
                axios.get(`${API_BASE_URL}/groups?limit=100`, { headers }),
                axios.get(`${API_BASE_URL}/users?limit=100`, { headers }),
                axios.get(`${API_BASE_URL}/actions/recent?limit=20`, { headers }),
            ]);

            setStats(statsRes.data);
            setGroups(groupsRes.data);
            setUsers(usersRes.data);
            setRecentActions(actionsRes.data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
            console.error('Dashboard error:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const getActionColor = (actionType: string) => {
        const colors: Record<string, string> = {
            ban: 'bg-red-100 text-red-800',
            mute: 'bg-orange-100 text-orange-800',
            warn: 'bg-yellow-100 text-yellow-800',
            kick: 'bg-red-100 text-red-800',
            unmute: 'bg-green-100 text-green-800',
            unban: 'bg-green-100 text-green-800',
            delete_message: 'bg-red-100 text-red-800',
            pin_message: 'bg-blue-100 text-blue-800',
        };
        return colors[actionType] || 'bg-gray-100 text-gray-800';
    };

    const StatCard: React.FC<{ label: string; value: number; icon: string }> = ({
        label,
        value,
        icon,
    }) => (
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-gray-600 text-sm font-medium">{label}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{value.toLocaleString()}</p>
                </div>
                <div className="text-4xl">{icon}</div>
            </div>
        </div>
    );

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin text-4xl mb-4">⏳</div>
                    <p className="text-gray-600">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-6 py-8">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                            <p className="text-gray-600 mt-2">Bot management overview and control</p>
                        </div>
                        <button
                            onClick={fetchDashboardData}
                            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                        >
                            🔄 Refresh
                        </button>
                    </div>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="flex gap-8">
                        {['overview', 'groups', 'users', 'actions'].map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab as any)}
                                className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${activeTab === tab
                                    ? 'border-blue-500 text-blue-600'
                                    : 'border-transparent text-gray-600 hover:text-gray-900'
                                    }`}
                            >
                                {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="max-w-7xl mx-auto px-6 py-4 mt-4">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                        <p className="font-medium">Error</p>
                        <p className="text-sm">{error}</p>
                    </div>
                </div>
            )}

            {/* Content */}
            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Overview Tab */}
                {activeTab === 'overview' && stats && (
                    <div className="space-y-8">
                        {/* Stats Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            <StatCard label="Total Groups" value={stats.total_groups} icon="👥" />
                            <StatCard label="Total Members" value={stats.total_members} icon="👤" />
                            <StatCard label="Total Admins" value={stats.total_admins} icon="🛡️" />
                            <StatCard label="Total Actions" value={stats.total_actions} icon="⚡" />
                        </div>

                        {/* Secondary Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <StatCard label="Active Users" value={stats.active_users} icon="✨" />
                            <StatCard label="Actions Today" value={stats.actions_today} icon="📅" />
                            <StatCard label="Actions This Week" value={stats.actions_this_week} icon="📊" />
                        </div>

                        {/* Recent Actions */}
                        <div className="bg-white rounded-lg shadow-md overflow-hidden">
                            <div className="px-6 py-4 border-b border-gray-200">
                                <h2 className="text-lg font-bold text-gray-900">Recent Actions</h2>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50 border-b border-gray-200">
                                        <tr>
                                            <th className="px-6 py-3 text-left font-medium text-gray-700">Type</th>
                                            <th className="px-6 py-3 text-left font-medium text-gray-700">Target</th>
                                            <th className="px-6 py-3 text-left font-medium text-gray-700">Group</th>
                                            <th className="px-6 py-3 text-left font-medium text-gray-700">Reason</th>
                                            <th className="px-6 py-3 text-left font-medium text-gray-700">Time</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200">
                                        {recentActions.length > 0 ? (
                                            recentActions.map((action) => (
                                                <tr key={action.action_id} className="hover:bg-gray-50">
                                                    <td className="px-6 py-4">
                                                        <span
                                                            className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getActionColor(
                                                                action.action_type
                                                            )}`}
                                                        >
                                                            {action.action_type}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 text-gray-900 font-medium">
                                                        @{action.target_username}
                                                    </td>
                                                    <td className="px-6 py-4 text-gray-600">#{action.group_id}</td>
                                                    <td className="px-6 py-4 text-gray-600">
                                                        {action.reason || 'No reason'}
                                                    </td>
                                                    <td className="px-6 py-4 text-gray-600">
                                                        {formatDate(action.created_at)}
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                                                    No recent actions
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* Groups Tab */}
                {activeTab === 'groups' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {groups.length > 0 ? (
                            groups.map((group) => (
                                <div
                                    key={group.group_id}
                                    className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
                                >
                                    <div className="px-6 py-4 bg-blue-50 border-b border-blue-200">
                                        <h3 className="text-lg font-bold text-gray-900">{group.group_name}</h3>
                                        <p className="text-sm text-gray-600">ID: {group.group_id}</p>
                                    </div>
                                    <div className="px-6 py-4 space-y-3">
                                        {group.description && (
                                            <p className="text-gray-700">{group.description}</p>
                                        )}
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <p className="text-sm text-gray-600">Members</p>
                                                <p className="text-2xl font-bold text-gray-900">
                                                    {group.member_count.toLocaleString()}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-sm text-gray-600">Admins</p>
                                                <p className="text-2xl font-bold text-gray-900">{group.admin_count}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                                            <span
                                                className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${group.is_active
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-red-100 text-red-800'
                                                    }`}
                                            >
                                                {group.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                            <span className="text-xs text-gray-600">
                                                Created: {formatDate(group.created_at)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="col-span-full text-center py-8">
                                <p className="text-gray-600">No groups found</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Users Tab */}
                {activeTab === 'users' && (
                    <div className="bg-white rounded-lg shadow-md overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50 border-b border-gray-200">
                                    <tr>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Username</th>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Name</th>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Role</th>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Email</th>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Groups</th>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                    {users.length > 0 ? (
                                        users.map((user) => (
                                            <tr key={user.user_id} className="hover:bg-gray-50">
                                                <td className="px-6 py-4 font-medium text-gray-900">@{user.username}</td>
                                                <td className="px-6 py-4 text-gray-600">
                                                    {user.first_name} {user.last_name}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span
                                                        className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${user.role === 'superadmin'
                                                            ? 'bg-red-100 text-red-800'
                                                            : user.role === 'admin'
                                                                ? 'bg-blue-100 text-blue-800'
                                                                : 'bg-gray-100 text-gray-800'
                                                            }`}
                                                    >
                                                        {user.role}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-gray-600">{user.email}</td>
                                                <td className="px-6 py-4 text-gray-600">{user.managed_groups.length}</td>
                                                <td className="px-6 py-4">
                                                    <span
                                                        className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${user.is_active
                                                            ? 'bg-green-100 text-green-800'
                                                            : 'bg-red-100 text-red-800'
                                                            }`}
                                                    >
                                                        {user.is_active ? 'Active' : 'Inactive'}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                                                No users found
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Actions Tab */}
                {activeTab === 'actions' && (
                    <div className="bg-white rounded-lg shadow-md overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-gray-50 border-b border-gray-200">
                                    <tr>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Type</th>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Target</th>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Group</th>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Reason</th>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Status</th>
                                        <th className="px-6 py-3 text-left font-medium text-gray-700">Time</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                    {recentActions.length > 0 ? (
                                        recentActions.map((action) => (
                                            <tr key={action.action_id} className="hover:bg-gray-50">
                                                <td className="px-6 py-4">
                                                    <span
                                                        className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getActionColor(
                                                            action.action_type
                                                        )}`}
                                                    >
                                                        {action.action_type}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 font-medium text-gray-900">
                                                    @{action.target_username}
                                                </td>
                                                <td className="px-6 py-4 text-gray-600">#{action.group_id}</td>
                                                <td className="px-6 py-4 text-gray-600">
                                                    {action.reason || '-'}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span
                                                        className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${action.status === 'success'
                                                            ? 'bg-green-100 text-green-800'
                                                            : action.status === 'pending'
                                                                ? 'bg-yellow-100 text-yellow-800'
                                                                : 'bg-red-100 text-red-800'
                                                            }`}
                                                    >
                                                        {action.status}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-gray-600">
                                                    {formatDate(action.created_at)}
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                                                No actions found
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard
