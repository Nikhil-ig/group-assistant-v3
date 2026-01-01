import React, { useEffect, useState } from 'react'
import LoginPage from './pages/LoginPage'
import AdminDashboard from './pages/AdminDashboard'
import './App.css'

function App() {
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
    const [userId, setUserId] = useState<number | null>(parseInt(localStorage.getItem('userId') || '0') || null)
    const [username, setUsername] = useState<string | null>(localStorage.getItem('username'))
    const [role, setRole] = useState<string | null>(localStorage.getItem('role'))

    useEffect(() => {
        // Check if token is still valid on mount
        if (token && userId && username && role) {
            // Token is stored, user is logged in
        }
    }, [])

    function handleLoginSuccess(newToken: string, newRole: string, newUserId: number, newUsername: string) {
        setToken(newToken)
        setRole(newRole)
        setUserId(newUserId)
        setUsername(newUsername)
    }

    function handleLogout() {
        setToken(null)
        setRole(null)
        setUserId(null)
        setUsername(null)
        localStorage.removeItem('token')
        localStorage.removeItem('userId')
        localStorage.removeItem('username')
        localStorage.removeItem('role')
    }

    if (!token || !userId || !username || !role) {
        return <LoginPage onLoginSuccess={handleLoginSuccess} />
    }

    return (
        <AdminDashboard
            token={token}
            userId={userId}
            username={username}
            role={role}
            onLogout={handleLogout}
        />
    )
}

export default App
