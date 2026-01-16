import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
    Group,
    GroupMember,
    Action,
    ActionType,
    ActionResponse,
    BatchActionResponse,
    GroupListResponse,
    PaginatedResponse,
    FilterOptions,
} from '../types'

// ============ AXIOS INSTANCE SETUP ============

const API_BASE_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8001/api'
const WEB_API_BASE = `${API_BASE_URL}/web`

const api: AxiosInstance = axios.create({
    baseURL: WEB_API_BASE,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// ============ INTERCEPTORS ============

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Response interceptor - handle errors
api.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        if (error.response?.status === 401) {
            // Redirect to login
            localStorage.removeItem('auth_token')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

// ============ AUTHENTICATION ENDPOINTS ============

export const authService = {
    login: async (userId: number, username: string) => {
        const response = await api.post('/auth/login', {
            user_id: userId,
            username,
        })
        return response.data
    },

    logout: async () => {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_data')
    },

    getCurrentUser: async () => {
        const response = await api.get('/auth/me')
        return response.data
    },

    refreshToken: async () => {
        const response = await api.post('/auth/refresh')
        return response.data
    },
}

// ============ GROUPS ENDPOINTS ============

export const groupsService = {
    // List all groups (with pagination)
    list: async (page: number = 1, pageSize: number = 20, filters?: FilterOptions) => {
        const response = await api.get<GroupListResponse>('/groups/list', {
            params: {
                page,
                page_size: pageSize,
                ...filters,
            },
        })
        return response.data
    },

    // Get group details
    getGroup: async (groupId: number) => {
        const response = await api.get<Group>(`/groups/${groupId}`)
        return response.data
    },

    // Get group statistics
    getStats: async (groupId: number, period: 'day' | 'week' | 'month' = 'week') => {
        const response = await api.get(`/groups/${groupId}/stats`, {
            params: { period },
        })
        return response.data
    },

    // Get group members
    getMembers: async (groupId: number, page: number = 1, pageSize: number = 50) => {
        const response = await api.get<PaginatedResponse<GroupMember>>(
            `/groups/${groupId}/members`,
            {
                params: { page, page_size: pageSize },
            }
        )
        return response.data
    },

    // Search members in group
    searchMembers: async (groupId: number, query: string) => {
        const response = await api.get<GroupMember[]>(
            `/groups/${groupId}/members/search`,
            {
                params: { q: query },
            }
        )
        return response.data
    },

    // Get member details
    getMember: async (groupId: number, userId: number) => {
        const response = await api.get<GroupMember>(
            `/groups/${groupId}/members/${userId}`
        )
        return response.data
    },

    // Get member action history
    getMemberHistory: async (
        groupId: number,
        userId: number,
        limit: number = 50
    ) => {
        const response = await api.get<Action[]>(
            `/groups/${groupId}/members/${userId}/history`,
            {
                params: { limit },
            }
        )
        return response.data
    },
}

// ============ ACTIONS ENDPOINTS ============

export const actionsService = {
    // Ban user
    ban: async (groupId: number, userInput: string, reason?: string) => {
        const response = await api.post<ActionResponse>('/actions/ban', {
            group_id: groupId,
            user_input: userInput,
            reason,
            initiated_by: parseInt(localStorage.getItem('user_id') || '0'),
        })
        return response.data
    },

    // Kick user
    kick: async (groupId: number, userInput: string, reason?: string) => {
        const response = await api.post<ActionResponse>('/actions/kick', {
            group_id: groupId,
            user_input: userInput,
            reason,
            initiated_by: parseInt(localStorage.getItem('user_id') || '0'),
        })
        return response.data
    },

    // Mute user
    mute: async (
        groupId: number,
        userInput: string,
        duration?: number,
        reason?: string
    ) => {
        const response = await api.post<ActionResponse>('/actions/mute', {
            group_id: groupId,
            user_input: userInput,
            duration,
            reason,
            initiated_by: parseInt(localStorage.getItem('user_id') || '0'),
        })
        return response.data
    },

    // Unmute user
    unmute: async (groupId: number, userInput: string) => {
        const response = await api.post<ActionResponse>('/actions/unmute', {
            group_id: groupId,
            user_input: userInput,
            initiated_by: parseInt(localStorage.getItem('user_id') || '0'),
        })
        return response.data
    },

    // Restrict user
    restrict: async (
        groupId: number,
        userInput: string,
        duration?: number,
        reason?: string
    ) => {
        const response = await api.post<ActionResponse>('/actions/restrict', {
            group_id: groupId,
            user_input: userInput,
            duration,
            reason,
            initiated_by: parseInt(localStorage.getItem('user_id') || '0'),
        })
        return response.data
    },

    // Unrestrict user
    unrestrict: async (groupId: number, userInput: string) => {
        const response = await api.post<ActionResponse>('/actions/unrestrict', {
            group_id: groupId,
            user_input: userInput,
            initiated_by: parseInt(localStorage.getItem('user_id') || '0'),
        })
        return response.data
    },

    // Warn user
    warn: async (groupId: number, userInput: string, reason?: string) => {
        const response = await api.post<ActionResponse>('/actions/warn', {
            group_id: groupId,
            user_input: userInput,
            reason,
            initiated_by: parseInt(localStorage.getItem('user_id') || '0'),
        })
        return response.data
    },

    // Promote to admin
    promote: async (
        groupId: number,
        userInput: string,
        title?: string
    ) => {
        const response = await api.post<ActionResponse>('/actions/promote', {
            group_id: groupId,
            user_input: userInput,
            title,
            initiated_by: parseInt(localStorage.getItem('user_id') || '0'),
        })
        return response.data
    },

    // Demote from admin
    demote: async (groupId: number, userInput: string) => {
        const response = await api.post<ActionResponse>('/actions/demote', {
            group_id: groupId,
            user_input: userInput,
            initiated_by: parseInt(localStorage.getItem('user_id') || '0'),
        })
        return response.data
    },

    // Unban user
    unban: async (groupId: number, userInput: string) => {
        const response = await api.post<ActionResponse>('/actions/unban', {
            group_id: groupId,
            user_input: userInput,
            initiated_by: parseInt(localStorage.getItem('user_id') || '0'),
        })
        return response.data
    },

    // Execute batch actions
    batch: async (actions: Array<{
        group_id: number
        user_input: string
        action_type: ActionType
        reason?: string
        duration?: number
    }>) => {
        const response = await api.post<BatchActionResponse>('/actions/batch', {
            actions: actions.map(a => ({
                ...a,
                initiated_by: parseInt(localStorage.getItem('user_id') || '0'),
            })),
        })
        return response.data
    },

    // Get action status
    getStatus: async (actionId: string) => {
        const response = await api.get<Action>(`/actions/status/${actionId}`)
        return response.data
    },

    // Get user action history
    getUserHistory: async (
        userId: number,
        filters?: FilterOptions,
        limit: number = 100
    ) => {
        const response = await api.get<PaginatedResponse<Action>>(
            '/actions/user-history',
            {
                params: {
                    user_id: userId,
                    limit,
                    ...filters,
                },
            }
        )
        return response.data
    },

    // Get group statistics
    getGroupStats: async (groupId: number) => {
        const response = await api.get(`/actions/group-stats`, {
            params: { group_id: groupId },
        })
        return response.data
    },
}

// ============ ANALYTICS ENDPOINTS ============

export const analyticsService = {
    // Get system-wide analytics (superadmin only)
    getSystemAnalytics: async (period: 'day' | 'week' | 'month' = 'week') => {
        const response = await api.get('/analytics/system', {
            params: { period },
        })
        return response.data
    },

    // Get group analytics
    getGroupAnalytics: async (
        groupId: number,
        period: 'day' | 'week' | 'month' = 'week'
    ) => {
        const response = await api.get(`/analytics/groups/${groupId}`, {
            params: { period },
        })
        return response.data
    },

    // Get action trends
    getActionTrends: async (
        days: number = 30,
        groupId?: number
    ) => {
        const response = await api.get('/analytics/trends', {
            params: {
                days,
                group_id: groupId,
            },
        })
        return response.data
    },

    // Get top users
    getTopUsers: async (
        limit: number = 10,
        sortBy: 'actions' | 'warnings' | 'bans' = 'actions'
    ) => {
        const response = await api.get('/analytics/top-users', {
            params: { limit, sort_by: sortBy },
        })
        return response.data
    },
}

// ============ UTILITY ENDPOINTS ============

export const utilService = {
    // Parse user reference
    parseUser: async (userInput: string) => {
        const response = await api.post('/parse-user', {
            text: userInput,
        })
        return response.data
    },

    // Health check
    health: async () => {
        const response = await api.get('/health')
        return response.data
    },

    // API info
    info: async () => {
        const response = await api.get('/info')
        return response.data
    },

    // Export data
    export: async (
        format: 'csv' | 'json' | 'pdf',
        dataType: 'actions' | 'members' | 'groups',
        filters?: FilterOptions
    ) => {
        const response = await api.get('/export', {
            params: {
                format,
                data_type: dataType,
                ...filters,
            },
            responseType: 'blob',
        })
        return response.data
    },
}

// ============ ERROR HANDLING ============

export const handleApiError = (error: unknown): string => {
    if (axios.isAxiosError(error)) {
        const status = error.response?.status
        const data = error.response?.data as any

        switch (status) {
            case 400:
                return data?.message || 'Bad request'
            case 401:
                return 'Unauthorized. Please login again.'
            case 403:
                return 'Permission denied'
            case 404:
                return 'Resource not found'
            case 409:
                return 'Conflict. Resource already exists.'
            case 429:
                return 'Too many requests. Please try again later.'
            case 500:
                return 'Server error. Please try again later.'
            default:
                return data?.message || 'An error occurred'
        }
    }
    return 'An unexpected error occurred'
}

export default api
