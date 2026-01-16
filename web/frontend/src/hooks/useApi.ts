import { useState, useEffect, useCallback } from 'react'
import type { ActionType } from '../types'
import * as apiServices from '../services/api'

// ============ GENERIC FETCH HOOK ============

interface UseQueryOptions {
    enabled?: boolean
    refetchInterval?: number
}

export const useQuery = <T,>(
    queryFn: () => Promise<T>,
    options: UseQueryOptions = {}
) => {
    const { enabled = true, refetchInterval } = options
    const [data, setData] = useState<T | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const refetch = useCallback(async () => {
        if (!enabled) return

        try {
            setIsLoading(true)
            const result = await queryFn()
            setData(result)
            setError(null)
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Unknown error'))
        } finally {
            setIsLoading(false)
        }
    }, [enabled, queryFn])

    useEffect(() => {
        refetch()

        if (refetchInterval && refetchInterval > 0) {
            const interval = setInterval(refetch, refetchInterval)
            return () => clearInterval(interval)
        }
    }, [refetch, refetchInterval])

    return { data, isLoading, error, refetch }
}

// ============ GROUPS HOOKS ============

export const useGroups = (page: number = 1, pageSize: number = 20, filters?: any) => {
    return useQuery(() => apiServices.groupsService.list(page, pageSize, filters))
}

export const useGroup = (groupId: number) => {
    return useQuery(() => apiServices.groupsService.getGroup(groupId), {
        enabled: !!groupId,
    })
}

export const useGroupStats = (groupId: number, period: 'day' | 'week' | 'month' = 'week') => {
    return useQuery(() => apiServices.groupsService.getStats(groupId, period), {
        enabled: !!groupId,
        refetchInterval: 30000, // Refresh every 30s
    })
}

export const useGroupMembers = (groupId: number, page: number = 1, pageSize: number = 50) => {
    return useQuery(() => apiServices.groupsService.getMembers(groupId, page, pageSize), {
        enabled: !!groupId,
    })
}

export const useGroupMemberSearch = (groupId: number, query: string) => {
    return useQuery(() => apiServices.groupsService.searchMembers(groupId, query), {
        enabled: !!groupId && query.length > 0,
    })
}

export const useMember = (groupId: number, userId: number) => {
    return useQuery(() => apiServices.groupsService.getMember(groupId, userId), {
        enabled: !!groupId && !!userId,
    })
}

export const useMemberHistory = (groupId: number, userId: number, limit: number = 50) => {
    return useQuery(() => apiServices.groupsService.getMemberHistory(groupId, userId, limit), {
        enabled: !!groupId && !!userId,
    })
}

// ============ ACTIONS HOOKS ============

export const useActionHistory = (userId: number, filters?: any, limit: number = 100) => {
    return useQuery(
        () => apiServices.actionsService.getUserHistory(userId, filters, limit),
        {
            enabled: !!userId,
        }
    )
}

export const useGroupActionStats = (groupId: number) => {
    return useQuery(() => apiServices.actionsService.getGroupStats(groupId), {
        enabled: !!groupId,
        refetchInterval: 20000,
    })
}

export const useActionStatus = (actionId: string) => {
    return useQuery(() => apiServices.actionsService.getStatus(actionId), {
        enabled: !!actionId,
    })
}

// ============ ANALYTICS HOOKS ============

export const useSystemAnalytics = (period: 'day' | 'week' | 'month' = 'week') => {
    return useQuery(() => apiServices.analyticsService.getSystemAnalytics(period), {
        refetchInterval: 60000, // Refresh every 60s
    })
}

export const useGroupAnalytics = (groupId: number, period: 'day' | 'week' | 'month' = 'week') => {
    return useQuery(() => apiServices.analyticsService.getGroupAnalytics(groupId, period), {
        enabled: !!groupId,
        refetchInterval: 60000,
    })
}

export const useActionTrends = (days: number = 30, groupId?: number) => {
    return useQuery(() => apiServices.analyticsService.getActionTrends(days, groupId), {
        refetchInterval: 120000, // Refresh every 2 min
    })
}

export const useTopUsers = (limit: number = 10, sortBy: 'actions' | 'warnings' | 'bans' = 'actions') => {
    return useQuery(() => apiServices.analyticsService.getTopUsers(limit, sortBy), {
        refetchInterval: 120000,
    })
}

// ============ MUTATION HOOKS ============

interface UseMutationOptions {
    onSuccess?: (data: any) => void
    onError?: (error: Error) => void
}

export const useMutation = <T, R>(
    mutationFn: (data: T) => Promise<R>,
    options: UseMutationOptions = {}
) => {
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<Error | null>(null)
    const [data, setData] = useState<R | null>(null)

    const mutate = useCallback(
        async (variables: T) => {
            try {
                setIsLoading(true)
                setError(null)
                const result = await mutationFn(variables)
                setData(result)
                options.onSuccess?.(result)
                return result
            } catch (err) {
                const error = err instanceof Error ? err : new Error('Unknown error')
                setError(error)
                options.onError?.(error)
                throw error
            } finally {
                setIsLoading(false)
            }
        },
        [mutationFn, options]
    )

    return { mutate, isLoading, error, data }
}

// ============ ACTION MUTATIONS ============

export const useBanUser = (options?: UseMutationOptions) => {
    return useMutation(
        ({ groupId, userInput, reason }: { groupId: number; userInput: string; reason?: string }) =>
            apiServices.actionsService.ban(groupId, userInput, reason),
        options
    )
}

export const useKickUser = (options?: UseMutationOptions) => {
    return useMutation(
        ({ groupId, userInput, reason }: { groupId: number; userInput: string; reason?: string }) =>
            apiServices.actionsService.kick(groupId, userInput, reason),
        options
    )
}

export const useMuteUser = (options?: UseMutationOptions) => {
    return useMutation(
        ({
            groupId,
            userInput,
            duration,
            reason,
        }: {
            groupId: number
            userInput: string
            duration?: number
            reason?: string
        }) => apiServices.actionsService.mute(groupId, userInput, duration, reason),
        options
    )
}

export const useUnmuteUser = (options?: UseMutationOptions) => {
    return useMutation(
        ({ groupId, userInput }: { groupId: number; userInput: string }) =>
            apiServices.actionsService.unmute(groupId, userInput),
        options
    )
}

export const useRestrictUser = (options?: UseMutationOptions) => {
    return useMutation(
        ({
            groupId,
            userInput,
            duration,
            reason,
        }: {
            groupId: number
            userInput: string
            duration?: number
            reason?: string
        }) => apiServices.actionsService.restrict(groupId, userInput, duration, reason),
        options
    )
}

export const useUnrestrictUser = (options?: UseMutationOptions) => {
    return useMutation(
        ({ groupId, userInput }: { groupId: number; userInput: string }) =>
            apiServices.actionsService.unrestrict(groupId, userInput),
        options
    )
}

export const useWarnUser = (options?: UseMutationOptions) => {
    return useMutation(
        ({ groupId, userInput, reason }: { groupId: number; userInput: string; reason?: string }) =>
            apiServices.actionsService.warn(groupId, userInput, reason),
        options
    )
}

export const usePromoteUser = (options?: UseMutationOptions) => {
    return useMutation(
        ({ groupId, userInput, title }: { groupId: number; userInput: string; title?: string }) =>
            apiServices.actionsService.promote(groupId, userInput, title),
        options
    )
}

export const useDemoteUser = (options?: UseMutationOptions) => {
    return useMutation(
        ({ groupId, userInput }: { groupId: number; userInput: string }) =>
            apiServices.actionsService.demote(groupId, userInput),
        options
    )
}

export const useUnbanUser = (options?: UseMutationOptions) => {
    return useMutation(
        ({ groupId, userInput }: { groupId: number; userInput: string }) =>
            apiServices.actionsService.unban(groupId, userInput),
        options
    )
}

export const useBatchActions = (options?: UseMutationOptions) => {
    return useMutation(
        (actions: Array<{
            group_id: number
            user_input: string
            action_type: ActionType
            reason?: string
            duration?: number
        }>) => apiServices.actionsService.batch(actions as any),
        options
    )
}
