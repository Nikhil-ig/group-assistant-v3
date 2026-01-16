import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { NotificationProvider } from './context/NotificationContext'
import { SettingsProvider } from './context/SettingsContext'
import { ErrorBoundary } from './components/ErrorBoundary'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
import { Signup } from './pages/Signup'
import { Dashboard } from './pages/Dashboard'
import { Groups } from './pages/Groups'
import { Users } from './pages/Users'
import { Actions } from './pages/Actions'

const AppContent: React.FC = () => {
  console.log('AppContent rendering - START')
  const { isAuthenticated, isLoading } = useAuth()

  console.log('isAuthenticated:', isAuthenticated, 'isLoading:', isLoading)

  // If still loading, show a simple spinner
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#1a1a2e',
        color: '#f3f4f6',
        fontSize: '18px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '50px',
            height: '50px',
            border: '3px solid #e94560',
            borderTop: '3px solid transparent',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          <p>Loading...</p>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      </div>
    )
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Root redirect */}
      <Route path="/" element={<Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />} />

      {/* Protected Routes */}
      {isAuthenticated && (
        <Route
          path="/*"
          element={
            <Layout>
              <Routes>
                {/* Dashboard */}
                <Route path="/dashboard" element={<Dashboard />} />

                {/* Groups Management */}
                <Route path="/dashboard/groups" element={<Groups />} />

                {/* Users Management */}
                <Route path="/dashboard/users" element={<Users />} />

                {/* Actions */}
                <Route path="/dashboard/actions" element={<Actions />} />

                {/* Catch all */}
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Layout>
          }
        />
      )}
    </Routes>
  )
}

const App: React.FC = () => {
  console.log('App component rendering')
  return (
    <ErrorBoundary>
      <AuthProvider>
        <NotificationProvider>
          <SettingsProvider>
            <Router>
              <AppContent />
            </Router>
          </SettingsProvider>
        </NotificationProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
