import { useEffect, useState } from 'react'
import { Send, History } from 'lucide-react'
import { Card, Button, Input, LoadingSpinner, Alert, Badge } from '../components/ui'
import { apiClient } from '../api/client'
import type { Action, ActionResponse, ActionType } from '../types'

// Demo data
const demoActions: Action[] = [
    {
        id: '1',
        action_type: 'ban',
        group_id: 1,
        user_id: 123,
        username: 'spammer123',
        initiated_by: 456,
        initiated_by_username: 'admin',
        reason: 'Spam behavior',
        status: 'completed',
        created_at: new Date().toISOString(),
    },
    {
        id: '2',
        action_type: 'mute',
        group_id: 1,
        user_id: 789,
        username: 'troll456',
        initiated_by: 456,
        initiated_by_username: 'admin',
        reason: 'Off-topic messages',
        duration: 3600,
        duration_unit: 'seconds',
        status: 'completed',
        created_at: new Date().toISOString(),
    },
]

export function Actions() {
    const [actions, setActions] = useState<Action[]>(demoActions)
    const [loading, setLoading] = useState(false)
    const [executing, setExecuting] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)
    const [formData, setFormData] = useState({
        action_type: 'ban' as ActionType,
        group_id: '',
        user_id: '',
        reason: '',
        duration: '',
    })

    useEffect(() => {
        fetchActions()
    }, [])

    const fetchActions = async () => {
        try {
            setLoading(true)
            const data = await apiClient.getActions()
            setActions(data)
            setError(null)
        } catch (err) {
            // Use demo data on error
            setActions(demoActions)
            setError(null)
            console.log('Using demo actions')
        } finally {
            setLoading(false)
        }
    }

    const handleExecuteAction = async () => {
        try {
            if (!formData.group_id || !formData.user_id || !formData.action_type) {
                setError('Please fill in all required fields')
                return
            }
            setExecuting(true)
            const payload: Partial<Action> = {
                action_type: formData.action_type,
                group_id: Number(formData.group_id),
                user_id: Number(formData.user_id),
                reason: formData.reason,
                duration: formData.duration ? Number(formData.duration) : undefined,
                initiated_by: 0,
                status: 'pending',
                created_at: new Date().toISOString(),
            }
            const response: ActionResponse = await apiClient.executeAction(payload as Action)
            setSuccess(`Action executed: ${response.message}`)
            setFormData({
                action_type: 'ban',
                group_id: '',
                user_id: '',
                reason: '',
                duration: '',
            })
            fetchActions()
        } catch (err) {
            setError('Failed to execute action')
            console.error(err)
        } finally {
            setExecuting(false)
        }
    }

    if (loading) {
        return (
            <div className="flex justify-center items-center h-96">
                <LoadingSpinner size="lg" />
            </div>
        )
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-4xl font-bold text-white">Moderation Actions</h1>
                <p className="text-dark-400 mt-1">Execute and track moderation actions</p>
            </div>

            {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
            {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

            <Card className="bg-dark-700 border border-dark-600">
                <h2 className="text-2xl font-bold text-white mb-4 flex items-center">
                    <Send className="w-6 h-6 mr-2 text-primary-500" />
                    Execute Action
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-semibold text-dark-200 mb-2">Action Type</label>
                        <select
                            value={formData.action_type}
                            onChange={(e) => setFormData({ ...formData, action_type: e.target.value as ActionType })}
                            className="w-full px-4 py-2 border border-dark-600 rounded-lg bg-dark-800 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                            <option value="ban">Ban</option>
                            <option value="kick">Kick</option>
                            <option value="mute">Mute</option>
                            <option value="unmute">Unmute</option>
                            <option value="promote">Promote</option>
                            <option value="demote">Demote</option>
                            <option value="warn">Warn</option>
                            <option value="pin">Pin Message</option>
                            <option value="unpin">Unpin Message</option>
                        </select>
                    </div>
                    <Input
                        label="Group ID"
                        type="number"
                        value={formData.group_id}
                        onChange={(v) => setFormData({ ...formData, group_id: String(v) })}
                        placeholder="123456789"
                    />
                    <Input
                        label="User ID"
                        type="number"
                        value={formData.user_id}
                        onChange={(v) => setFormData({ ...formData, user_id: String(v) })}
                        placeholder="987654321"
                    />
                    <Input
                        label="Duration (minutes)"
                        type="number"
                        value={formData.duration}
                        onChange={(v) => setFormData({ ...formData, duration: String(v) })}
                        placeholder="60"
                    />
                    <div className="md:col-span-2">
                        <Input
                            label="Reason"
                            type="textarea"
                            value={formData.reason}
                            onChange={(v) => setFormData({ ...formData, reason: String(v) })}
                            placeholder="Reason for action"
                            rows={3}
                        />
                    </div>
                </div>
                <Button
                    onClick={handleExecuteAction}
                    disabled={executing}
                    variant="primary"
                    size="lg"
                    className="mt-4 w-full"
                >
                    {executing ? 'Executing...' : 'Execute Action'}
                </Button>
            </Card>

            <Card>
                <h2 className="text-xl font-bold text-white mb-4 flex items-center">
                    <History className="w-5 h-5 mr-2" />
                    Recent Actions ({actions.length})
                </h2>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-dark-700">
                                <th className="text-left py-3 px-4 font-semibold text-dark-200">Type</th>
                                <th className="text-left py-3 px-4 font-semibold text-dark-200">User ID</th>
                                <th className="text-left py-3 px-4 font-semibold text-dark-200">Group ID</th>
                                <th className="text-left py-3 px-4 font-semibold text-dark-200">Reason</th>
                                <th className="text-left py-3 px-4 font-semibold text-dark-200">Status</th>
                                <th className="text-left py-3 px-4 font-semibold text-dark-200">Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {actions.slice(0, 10).map((action) => (
                                <tr key={action.id} className="border-b border-dark-700 hover:bg-dark-700 transition">
                                    <td className="py-3 px-4">
                                        <Badge variant="primary">{action.action_type}</Badge>
                                    </td>
                                    <td className="py-3 px-4 text-dark-300 font-mono">{action.user_id}</td>
                                    <td className="py-3 px-4 text-dark-300 font-mono">{action.group_id}</td>
                                    <td className="py-3 px-4 text-dark-300 truncate max-w-xs">{action.reason || '-'}</td>
                                    <td className="py-3 px-4">
                                        <span
                                            className={`px-3 py-1 rounded-full text-xs font-semibold ${action.status === 'completed'
                                                ? 'bg-green-100 text-green-800'
                                                : action.status === 'pending'
                                                    ? 'bg-yellow-100 text-yellow-800'
                                                    : 'bg-red-100 text-red-800'
                                                }`}
                                        >
                                            {action.status}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-dark-300 text-xs">N/A</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </Card>
        </div>
    )
}

export default Actions
