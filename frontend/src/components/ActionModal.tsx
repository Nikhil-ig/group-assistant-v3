import React, { useState } from 'react'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

type Member = {
  user_id: number
  username?: string
  first_name?: string
}

type Props = {
  isOpen: boolean
  onClose: () => void
  onConfirm: (action: any) => void
  member: Member
  defaultActionType: 'ban' | 'mute' | 'unmute' | 'kick'
  groupId: number
}

export default function ActionModal({
  isOpen,
  onClose,
  onConfirm,
  member,
  defaultActionType,
  groupId,
}: Props) {
  const [actionType, setActionType] = useState(defaultActionType)
  const [reason, setReason] = useState('')
  const [durationHours, setDurationHours] = useState('24')

  if (!isOpen) return null

  const handleConfirm = () => {
    const action: any = {
      action_type: actionType,
      target_user_id: member.user_id,
      target_username: member.username,
      reason: reason || undefined,
    }

    if (actionType === 'mute' && durationHours) {
      action.duration_hours = parseInt(durationHours)
    }

    onConfirm(action)
    setReason('')
    setDurationHours('24')
    setActionType(defaultActionType)
  }

  const getActionColor = () => {
    switch (actionType) {
      case 'ban':
        return 'bg-red-600 hover:bg-red-700'
      case 'mute':
        return 'bg-yellow-600 hover:bg-yellow-700'
      case 'unmute':
        return 'bg-green-600 hover:bg-green-700'
      case 'kick':
        return 'bg-orange-600 hover:bg-orange-700'
      default:
        return 'bg-indigo-600 hover:bg-indigo-700'
    }
  }

  const getActionDescription = () => {
    switch (actionType) {
      case 'ban':
        return 'Permanently ban this user from the group'
      case 'mute':
        return `Restrict user for ${durationHours} hours`
      case 'unmute':
        return 'Remove restrictions for this user'
      case 'kick':
        return 'Remove user from the group'
      default:
        return ''
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-md">
        {/* Header */}
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center gap-3">
          <ExclamationTriangleIcon className="h-6 w-6 text-orange-500" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Confirm Action</h2>
            <p className="text-sm text-gray-500">User: {member.username || member.first_name || `ID ${member.user_id}`}</p>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {/* Action Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Action</label>
            <select
              value={actionType}
              onChange={(e) => setActionType(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="ban">Ban User</option>
              <option value="mute">Mute User</option>
              <option value="unmute">Unmute User</option>
              <option value="kick">Kick User</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">{getActionDescription()}</p>
          </div>

          {/* Duration (for mute) */}
          {actionType === 'mute' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Duration (hours)</label>
              <input
                type="number"
                value={durationHours}
                onChange={(e) => setDurationHours(e.target.value)}
                min="1"
                max="720"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          )}

          {/* Reason */}
          {actionType !== 'unmute' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Reason (optional)</label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Why are you taking this action?"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
              />
            </div>
          )}

          {/* Warning */}
          {actionType === 'ban' && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">
                ⚠️ This action is <strong>permanent</strong> and cannot be reversed without using the unban function.
              </p>
            </div>
          )}

          {actionType === 'kick' && (
            <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
              <p className="text-sm text-orange-800">
                ⚠️ The user will be removed from the group but can rejoin if invited.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium transition"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className={`px-4 py-2 text-white rounded-lg font-medium transition ${getActionColor()}`}
          >
            {actionType.charAt(0).toUpperCase() + actionType.slice(1)} User
          </button>
        </div>
      </div>
    </div>
  )
}
