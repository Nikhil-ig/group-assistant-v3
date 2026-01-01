import React, { useState } from 'react'
import { login } from '../api/client'

type LoginPageProps = {
    onLoginSuccess: (token: string, role: string, userId: number, username: string) => void
}

export default function LoginPage({ onLoginSuccess }: LoginPageProps) {
    const [userId, setUserId] = useState('')
    const [username, setUsername] = useState('')
    const [firstName, setFirstName] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    async function handleLogin(e: React.FormEvent) {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            const response = await login({
                user_id: parseInt(userId),
                username,
                first_name: firstName,
            })

            if (response.ok && response.token) {
                localStorage.setItem('token', response.token)
                localStorage.setItem('userId', userId)
                localStorage.setItem('username', username)
                localStorage.setItem('role', response.role || 'user')
                onLoginSuccess(response.token, response.role || 'user', parseInt(userId), username)
            } else {
                setError(response.message || 'Login failed')
            }
        } catch (err: any) {
            setError(err.message || 'An error occurred during login')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-600 to-blue-800 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg shadow-2xl w-full max-w-md p-8">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">Guardian Bot</h1>
                    <p className="text-gray-600">Admin Dashboard</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Telegram User ID</label>
                        <input
                            type="number"
                            required
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                            placeholder="e.g., 12345"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                        <input
                            type="text"
                            required
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="e.g., admin"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                        <input
                            type="text"
                            required
                            value={firstName}
                            onChange={(e) => setFirstName(e.target.value)}
                            placeholder="e.g., Admin"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        />
                    </div>

                    {error && <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium transition"
                    >
                        {loading ? 'Logging in...' : 'Login'}
                    </button>
                </form>

                <div className="mt-6 pt-6 border-t border-gray-200">
                    <p className="text-sm text-gray-600 text-center mb-3">Demo Credentials:</p>
                    <div className="bg-gray-50 rounded-lg p-3 text-xs space-y-1">
                        <div>
                            <span className="font-semibold">Superadmin:</span>
                            <div className="text-gray-600">ID: 12345 | Username: testadmin</div>
                        </div>
                        <div>
                            <span className="font-semibold">Group Admin:</span>
                            <div className="text-gray-600">ID: 111 | Username: user_one</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
