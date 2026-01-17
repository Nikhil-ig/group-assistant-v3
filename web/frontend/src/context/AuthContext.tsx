import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react'
import type { AuthUser, UserRole } from '../types'
import { authService } from '../services/api'

interface AuthContextType {
    user: AuthUser | null
    isAuthenticated: boolean
    isLoading: boolean
    error: string | null
    login: (userId: number, username: string) => Promise<void>
    logout: () => Promise<void>
    checkAuth: () => Promise<void>
    hasRole: (role: UserRole | UserRole[]) => boolean
    hasPermission: (action: string, scope?: 'self' | 'group' | 'system') => boolean
    canManageGroup: (groupId: number) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<AuthUser | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const checkAuth = useCallback(async () => {
        try {
            setIsLoading(true)
            const token = localStorage.getItem('auth_token')
            const userData = localStorage.getItem('user_data')

            if (token && userData) {
                try {
                    const user = JSON.parse(userData) as AuthUser
                    setUser(user)
                    console.log('Auth check passed, user:', user)
                } catch (e) {
                    console.error('Failed to parse user data:', e)
                    setUser(null)
                }
            } else {
                console.log('No auth token or user data found')
                setUser(null)
            }
        } catch (err) {
            console.error('Auth check failed:', err)
            setUser(null)
        } finally {
            setIsLoading(false)
        }
    }, [])

    // Check authentication on mount AND listen for storage changes
    useEffect(() => {
        const timer = setTimeout(async () => {
            await checkAuth()
        }, 100)

        // Listen for storage changes from other tabs/windows or same page
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === 'auth_token' || e.key === 'user_data') {
                console.log('Storage changed, checking auth...')
                checkAuth()
            }
        }

        // Also listen for custom storage events
        const handleCustomStorageChange = () => {
            console.log('Custom storage event, checking auth...')
            checkAuth()
        }

        window.addEventListener('storage', handleStorageChange)
        window.addEventListener('auth-update', handleCustomStorageChange)

        return () => {
            clearTimeout(timer)
            window.removeEventListener('storage', handleStorageChange)
            window.removeEventListener('auth-update', handleCustomStorageChange)
        }
    }, [checkAuth])

    const login = useCallback(async (userId: number, username: string) => {
        try {
            setIsLoading(true)
            setError(null)

            const response = await authService.login(userId, username)

            if (response.success) {
                const authUser = response.user as AuthUser
                setUser(authUser)
                localStorage.setItem('auth_token', response.token)
                localStorage.setItem('user_data', JSON.stringify(authUser))
                localStorage.setItem('user_id', userId.toString())
            } else {
                throw new Error('Login failed')
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Login failed'
            setError(message)
            throw err
        } finally {
            setIsLoading(false)
        }
    }, [])

    const logout = useCallback(async () => {
        try {
            setIsLoading(true)
            await authService.logout()
            setUser(null)
            localStorage.clear()
        } catch (err) {
            console.error('Logout failed:', err)
        } finally {
            setIsLoading(false)
        }
    }, [])

    const hasRole = useCallback(
        (roles: UserRole | UserRole[]): boolean => {
            if (!user) return false
            const roleArray = Array.isArray(roles) ? roles : [roles]
            return roleArray.includes(user.role)
        },
        [user]
    )

    const hasPermission = useCallback(
        (action: string, scope?: 'self' | 'group' | 'system'): boolean => {
            if (!user) return false
            return user.permissions?.some(
                (perm) => perm.action === action && (!scope || perm.scope === scope) && perm.allowed
            ) ?? false
        },
        [user]
    )

    const canManageGroup = useCallback(
        (groupId: number): boolean => {
            if (!user) return false
            if (user.role === 'superadmin') return true
            return user.managed_groups?.includes(groupId) ?? false
        },
        [user]
    )

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user,
                isLoading,
                error,
                login,
                logout,
                checkAuth,
                hasRole,
                hasPermission,
                canManageGroup,
            }}
        >
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within AuthProvider')
    }
    return context
}
