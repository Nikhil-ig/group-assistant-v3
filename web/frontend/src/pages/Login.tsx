import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiClient } from '../api/client'

declare global {
    interface Window {
        onTelegramAuth?: (user: any) => void
        Telegram?: any
    }
}

export function Login() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const navigate = useNavigate()

    // Setup Telegram auth callback
    useEffect(() => {
        window.onTelegramAuth = (user: any) => {
            handleTelegramAuth(user)
        }

        // Load Telegram widget script
        const script = document.createElement('script')
        script.async = true
        script.src = 'https://telegram.org/js/telegram-widget.js?22'
        document.body.appendChild(script)

        return () => {
            try {
                document.body.removeChild(script)
            } catch (e) {
                // Already removed
            }
        }
    }, [])

    const handleLogin = async () => {
        try {
            if (!email || !password) {
                setError('Please fill in all fields')
                return
            }

            setLoading(true)
            setError(null)

            const response = await fetch('http://localhost:8001/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            })

            if (!response.ok) throw new Error('Login failed')

            const data = await response.json()
            apiClient.setAuthHeader(data.access_token)
            localStorage.setItem('auth_token', data.access_token)
            localStorage.setItem('user_data', JSON.stringify(data.user))
            navigate('/')
        } catch (err) {
            setError('Invalid credentials')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleTelegramAuth = async (user: any) => {
        try {
            setLoading(true)
            setError(null)
            console.log('Telegram user data:', user)

            // Send telegram auth data to backend
            const response = await fetch('http://localhost:8001/api/auth/telegram', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    telegram_id: user.id,
                    first_name: user.first_name,
                    last_name: user.last_name || '',
                    username: user.username || '',
                    photo_url: user.photo_url || '',
                    auth_date: user.auth_date,
                    hash: user.hash,
                }),
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Telegram login failed')
            }

            const data = await response.json()
            apiClient.setAuthHeader(data.access_token)
            localStorage.setItem('auth_token', data.access_token)
            localStorage.setItem('user_data', JSON.stringify(data.user))
            navigate('/')
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Telegram login failed')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleDemoLogin = () => {
        try {
            // Set token and user data
            const demoToken = 'demo-token-' + Date.now()
            const demoUser = {
                id: 123456789,
                username: 'demo_user',
                role: 'superadmin',
                permissions: []
            }

            // Save to localStorage
            localStorage.setItem('auth_token', demoToken)
            localStorage.setItem('user_data', JSON.stringify(demoUser))

            // Set auth header
            if (apiClient.setAuthHeader) {
                apiClient.setAuthHeader(demoToken)
            }

            console.log('Demo login successful:', demoUser)

            // Trigger auth context update
            window.dispatchEvent(new Event('auth-update'))

            // Force navigation with a small delay to allow state to update
            setTimeout(() => {
                navigate('/dashboard', { replace: true })
            }, 200)
        } catch (err) {
            setError('Demo login failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
            console.error('Demo login error:', err)
        }
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
                        backgroundColor: '#e94560',
                        borderRadius: '50%',
                        margin: '0 auto 15px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '30px',
                        color: 'white'
                    }}>
                        🤖
                    </div>
                    <h1 style={{ fontSize: '28px', fontWeight: 'bold', color: 'white', margin: '0' }}>
                        Bot Manager
                    </h1>
                    <p style={{ color: '#888', marginTop: '10px' }}>
                        Admin Dashboard
                    </p>
                </div>

                {error && (
                    <div style={{
                        backgroundColor: '#8b0000',
                        color: '#ffcccc',
                        padding: '10px',
                        borderRadius: '5px',
                        marginBottom: '15px',
                        fontSize: '14px'
                    }}>
                        {error}
                    </div>
                )}

                {/* Telegram Login Widget - Replace YOUR_BOT_USERNAME */}
                <div style={{ marginBottom: '20px', textAlign: 'center' }}>
                    <p style={{ color: '#888', fontSize: '12px', marginBottom: '10px' }}>Quick Login with Telegram</p>
                    <div style={{ minHeight: '60px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <script
                            async
                            src="https://telegram.org/js/telegram-widget.js?22"
                            data-telegram-login="YOUR_BOT_USERNAME"
                            data-size="large"
                            data-userpic="true"
                            data-onauth="onTelegramAuth(user)"
                            data-request-access="write"
                        ></script>
                    </div>
                    <p style={{ color: '#555', fontSize: '11px', marginTop: '8px' }}>
                        ⚠️ Replace YOUR_BOT_USERNAME in index.html script tag
                    </p>
                </div>

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

                <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', color: 'white', marginBottom: '5px', fontSize: '14px' }}>
                        Email
                    </label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
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

                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', color: 'white', marginBottom: '5px', fontSize: '14px' }}>
                        Password
                    </label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
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
                    onClick={handleLogin}
                    disabled={loading}
                    style={{
                        width: '100%',
                        padding: '12px',
                        backgroundColor: '#e94560',
                        border: 'none',
                        borderRadius: '5px',
                        color: 'white',
                        fontSize: '16px',
                        fontWeight: 'bold',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        marginBottom: '15px',
                        opacity: loading ? 0.6 : 1
                    }}
                    onMouseOver={(e) => !loading && (e.currentTarget.style.backgroundColor = '#d63547')}
                    onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#e94560')}
                >
                    {loading ? 'Logging in...' : 'Login with Email'}
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
                    onClick={handleDemoLogin}
                    style={{
                        width: '100%',
                        padding: '12px',
                        backgroundColor: '#0f3460',
                        border: '1px solid #0f3460',
                        borderRadius: '5px',
                        color: 'white',
                        fontSize: '16px',
                        fontWeight: 'bold',
                        cursor: 'pointer'
                    }}
                    onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#1a4d6d')}
                    onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#0f3460')}
                >
                    Demo Login
                </button>

                <p style={{ textAlign: 'center', color: '#666', fontSize: '12px', marginTop: '20px' }}>
                    Default: admin@example.com / password123
                </p>

                <div style={{ textAlign: 'center', marginTop: '20px', borderTop: '1px solid #333', paddingTop: '20px' }}>
                    <p style={{ color: '#888', fontSize: '14px', margin: '0 0 10px 0' }}>
                        New admin?
                    </p>
                    <Link
                        to="/signup"
                        style={{
                            color: '#10b981',
                            textDecoration: 'none',
                            fontSize: '14px',
                            fontWeight: '500',
                            cursor: 'pointer'
                        }}
                        onMouseOver={(e) => (e.currentTarget.style.color = '#059669')}
                        onMouseOut={(e) => (e.currentTarget.style.color = '#10b981')}
                    >
                        Create a new account →
                    </Link>
                </div>
            </div>
        </div>
    )
}

export default Login
