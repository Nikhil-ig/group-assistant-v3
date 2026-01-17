import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import type { Notification, NotificationType } from '../types'

interface NotificationContextType {
    notifications: Notification[]
    addNotification: (
        title: string,
        message: string,
        type: NotificationType,
        duration?: number,
        action?: { label: string; callback: () => void }
    ) => string
    removeNotification: (id: string) => void
    clearAll: () => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export const NotificationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [notifications, setNotifications] = useState<Notification[]>([])

    const addNotification = useCallback(
        (
            title: string,
            message: string,
            type: NotificationType,
            duration: number = 5000,
            action?: { label: string; callback: () => void }
        ) => {
            const id = Date.now().toString()
            const notification: Notification = {
                id,
                title,
                message,
                type,
                duration,
                action,
                timestamp: Date.now(),
            }

            setNotifications((prev) => [...prev, notification])

            // Auto-remove after duration
            if (duration > 0) {
                setTimeout(() => {
                    removeNotification(id)
                }, duration)
            }

            return id
        },
        []
    )

    const removeNotification = useCallback((id: string) => {
        setNotifications((prev) => prev.filter((notif) => notif.id !== id))
    }, [])

    const clearAll = useCallback(() => {
        setNotifications([])
    }, [])

    return (
        <NotificationContext.Provider
            value={{
                notifications,
                addNotification,
                removeNotification,
                clearAll,
            }}
        >
            {children}
        </NotificationContext.Provider>
    )
}

export const useNotification = (): NotificationContextType => {
    const context = useContext(NotificationContext)
    if (context === undefined) {
        throw new Error('useNotification must be used within NotificationProvider')
    }
    return context
}

// Helper hook for common notifications
export const useNotificationHelper = () => {
    const { addNotification } = useNotification()

    return {
        success: (title: string, message: string) =>
            addNotification(title, message, 'success', 5000),
        error: (title: string, message: string) =>
            addNotification(title, message, 'error', 7000),
        warning: (title: string, message: string) =>
            addNotification(title, message, 'warning', 6000),
        info: (title: string, message: string) =>
            addNotification(title, message, 'info', 4000),
    }
}
