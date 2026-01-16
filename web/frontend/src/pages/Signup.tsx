import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiClient } from '../api/client'

export function Signup() {
    console.log('Signup component rendered')
    const [email, setEmail] = useState('')
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)
    const navigate = useNavigate()

    const validateForm = () => {
        if (!email || !username || !password || !confirmPassword) {
            setError('Please fill in all fields')
            return false
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match')
            return false
        }

        if (password.length < 6) {
            setError('Password must be at least 6 characters')
            return false
        }

        if (username.length < 3) {
            setError('Username must be at least 3 characters')
            return false
        }

        if (!email.includes('@')) {
            setError('Please enter a valid email')
            return false
        }

        return true
    }

    const handleSignup = async () => {
        setError(null)
        setSuccess(null)

        if (!validateForm()) {
            return
        }

        try {
            setLoading(true)
            const response = await fetch('http://localhost:8001/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    username,
                    password,
                    role: 'admin'
                }),
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Signup failed')
            }

            setSuccess('Signup successful! Redirecting to login...')

            setTimeout(() => {
                navigate('/login')
            }, 1500)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Signup failed. Please try again.')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleDemoSignup = () => {
        // Demo signup - auto-create and login
        const demoToken = 'demo-admin-token-' + Date.now()
        apiClient.setAuthHeader(demoToken)
        localStorage.setItem('auth_token', demoToken)
        localStorage.setItem('user_data', JSON.stringify({
            id: Math.floor(Math.random() * 1000000),
            username: 'new_admin_' + Date.now(),
            email: `admin_${Date.now()}@example.com`,
            role: 'admin',
            permissions: ['manage_groups', 'manage_users', 'manage_actions']
        }))
        navigate('/')
    }

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#1a1a2e',
            padding: '20px',
            fontFamily: 'Arial, sans-serif'
        }}>
            <div style={{
                width: '100%',
                maxWidth: '450px',
                backgroundColor: '#16213e',
                border: '1px solid #0f3460',
                borderRadius: '10px',
                padding: '30px'
            }}>
                <div style={{ textAlign: 'center', marginBottom: '30px' }}>
                    <div style={{
                        width: '60px',
                        height: '60px',
                        backgroundColor: '#10b981',
                        borderRadius: '50%',
                        margin: '0 auto 15px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '30px',
                        color: 'white'
                    }}>
                        ✨
                    </div>
                    <h1 style={{ fontSize: '28px', fontWeight: 'bold', color: 'white', margin: '0' }}>
                        Create Admin Account
                    </h1>
                    <p style={{ color: '#888', marginTop: '10px' }}>
                        Bot Manager - Admin Dashboard
                    </p>
                </div>

                {error && (
                    <div style={{
                        backgroundColor: '#8b0000',
                        color: '#ffcccc',
                        padding: '12px',
                        borderRadius: '5px',
                        marginBottom: '15px',
                        fontSize: '14px',
                        borderLeft: '4px solid #d32f2f'
                    }}>
                        ⚠️ {error}
                    </div>
                )}

                {success && (
                    <div style={{
                        backgroundColor: '#065f46',
                        color: '#bbf7d0',
                        padding: '12px',
                        borderRadius: '5px',
                        marginBottom: '15px',
                        fontSize: '14px',
                        borderLeft: '4px solid #10b981'
                    }}>
                        ✓ {success}
                    </div>
                )}

                <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', color: 'white', marginBottom: '5px', fontSize: '14px', fontWeight: '500' }}>
                        Email Address
                    </label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="admin@example.com"
                        style={{
                            width: '100%',
                            padding: '10px',
                            backgroundColor: '#0f3460',
                            border: '1px solid #0f3460',
                            borderRadius: '5px',
                            color: 'white',
                            fontSize: '14px',
                            boxSizing: 'border-box'
                        }}
                    />
                </div>

                <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', color: 'white', marginBottom: '5px', fontSize: '14px', fontWeight: '500' }}>
                        Username
                    </label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="admin_username"
                        style={{
                            width: '100%',
                            padding: '10px',
                            backgroundColor: '#0f3460',
                            border: '1px solid #0f3460',
                            borderRadius: '5px',
                            color: 'white',
                            fontSize: '14px',
                            boxSizing: 'border-box'
                        }}
                    />
                </div>

                <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', color: 'white', marginBottom: '5px', fontSize: '14px', fontWeight: '500' }}>
                        Password
                    </label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        style={{
                            width: '100%',
                            padding: '10px',
                            backgroundColor: '#0f3460',
                            border: '1px solid #0f3460',
                            borderRadius: '5px',
                            color: 'white',
                            fontSize: '14px',
                            boxSizing: 'border-box'
                        }}
                    />
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', color: 'white', marginBottom: '5px', fontSize: '14px', fontWeight: '500' }}>
                        Confirm Password
                    </label>
                    <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••"
                        style={{
                            width: '100%',
                            padding: '10px',
                            backgroundColor: '#0f3460',
                            border: '1px solid #0f3460',
                            borderRadius: '5px',
                            color: 'white',
                            fontSize: '14px',
                            boxSizing: 'border-box'
                        }}
                    />
                </div>

                <button
                    onClick={handleSignup}
                    disabled={loading}
                    style={{
                        width: '100%',
                        padding: '12px',
                        backgroundColor: '#10b981',
                        border: 'none',
                        borderRadius: '5px',
                        color: 'white',
                        fontSize: '16px',
                        fontWeight: 'bold',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        marginBottom: '15px',
                        opacity: loading ? 0.6 : 1
                    }}
                    onMouseOver={(e) => !loading && (e.currentTarget.style.backgroundColor = '#059669')}
                    onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#10b981')}
                >
                    {loading ? 'Creating Account...' : 'Create Account'}
                </button>

                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    margin: '15px 0',
                    color: '#666'
                }}>
                    <div style={{ flex: 1, height: '1px', backgroundColor: '#333' }}></div>
                    <span style={{ padding: '0 10px', fontSize: '14px' }}>or</span>
                    <div style={{ flex: 1, height: '1px', backgroundColor: '#333' }}></div>
                </div>

                <button
                    onClick={handleDemoSignup}
                    style={{
                        width: '100%',
                        padding: '12px',
                        backgroundColor: '#1a4d6d',
                        border: '1px solid #0f3460',
                        borderRadius: '5px',
                        color: 'white',
                        fontSize: '16px',
                        fontWeight: 'bold',
                        cursor: 'pointer',
                        marginBottom: '15px'
                    }}
                    onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#2a6d9d')}
                    onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#1a4d6d')}
                >
                    Demo Admin Account
                </button>

                <div style={{ textAlign: 'center', marginTop: '20px' }}>
                    <p style={{ color: '#888', fontSize: '14px', margin: '0 0 10px 0' }}>
                        Already have an account?
                    </p>
                    <Link
                        to="/login"
                        style={{
                            color: '#0ea5e9',
                            textDecoration: 'none',
                            fontSize: '14px',
                            fontWeight: '500',
                            cursor: 'pointer'
                        }}
                        onMouseOver={(e) => (e.currentTarget.style.color = '#06b6d4')}
                        onMouseOut={(e) => (e.currentTarget.style.color = '#0ea5e9')}
                    >
                        Go to Login →
                    </Link>
                </div>

                <p style={{ textAlign: 'center', color: '#555', fontSize: '12px', marginTop: '20px' }}>
                    Password must be at least 6 characters
                </p>
            </div>
        </div>
    )
}

export default Signup
