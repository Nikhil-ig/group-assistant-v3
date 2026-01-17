import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react'
import type { UserSettings, DashboardCustomization, SavedFilter } from '../types'

interface SettingsContextType {
    settings: UserSettings
    customization: DashboardCustomization
    updateSettings: (settings: Partial<UserSettings>) => void
    updateCustomization: (customization: Partial<DashboardCustomization>) => void
    addSavedFilter: (filter: SavedFilter) => void
    removeSavedFilter: (filterId: string) => void
    resetSettings: () => void
}

const DEFAULT_SETTINGS: UserSettings = {
    theme: 'light',
    notifications_enabled: true,
    email_notifications: false,
    session_timeout: 60,
    language: 'en',
    timezone: 'UTC',
    show_confirmations: true,
    auto_refresh_dashboard: false,
    refresh_interval: 30,
}

const DEFAULT_CUSTOMIZATION: DashboardCustomization = {
    visible_widgets: ['stats', 'recent_actions', 'top_groups', 'trends'],
    widget_order: ['stats', 'recent_actions', 'top_groups', 'trends'],
    widget_sizes: {
        stats: 'small',
        recent_actions: 'large',
        top_groups: 'medium',
        trends: 'large',
    },
    saved_filters: [],
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined)

export const SettingsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS)
    const [customization, setCustomization] = useState<DashboardCustomization>(DEFAULT_CUSTOMIZATION)

    // Load from localStorage on mount
    useEffect(() => {
        const savedSettings = localStorage.getItem('user_settings')
        const savedCustomization = localStorage.getItem('user_customization')

        if (savedSettings) {
            try {
                setSettings(JSON.parse(savedSettings))
            } catch (err) {
                console.error('Failed to parse settings:', err)
            }
        }

        if (savedCustomization) {
            try {
                setCustomization(JSON.parse(savedCustomization))
            } catch (err) {
                console.error('Failed to parse customization:', err)
            }
        }

        // Apply theme
        applyTheme(settings.theme)
    }, [])

    const applyTheme = (theme: 'light' | 'dark' | 'auto') => {
        const html = document.documentElement
        if (theme === 'dark') {
            html.classList.add('dark')
        } else if (theme === 'light') {
            html.classList.remove('dark')
        } else {
            const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
            if (isDark) {
                html.classList.add('dark')
            } else {
                html.classList.remove('dark')
            }
        }
    }

    const updateSettings = useCallback((newSettings: Partial<UserSettings>) => {
        setSettings((prev) => {
            const updated = { ...prev, ...newSettings }
            localStorage.setItem('user_settings', JSON.stringify(updated))

            // Apply theme if changed
            if (newSettings.theme) {
                applyTheme(newSettings.theme)
            }

            return updated
        })
    }, [])

    const updateCustomization = useCallback(
        (newCustomization: Partial<DashboardCustomization>) => {
            setCustomization((prev) => {
                const updated = { ...prev, ...newCustomization }
                localStorage.setItem('user_customization', JSON.stringify(updated))
                return updated
            })
        },
        []
    )

    const addSavedFilter = useCallback((filter: SavedFilter) => {
        updateCustomization({
            saved_filters: [...customization.saved_filters, filter],
        })
    }, [customization.saved_filters, updateCustomization])

    const removeSavedFilter = useCallback(
        (filterId: string) => {
            updateCustomization({
                saved_filters: customization.saved_filters.filter((f) => f.id !== filterId),
            })
        },
        [customization.saved_filters, updateCustomization]
    )

    const resetSettings = useCallback(() => {
        setSettings(DEFAULT_SETTINGS)
        setCustomization(DEFAULT_CUSTOMIZATION)
        localStorage.removeItem('user_settings')
        localStorage.removeItem('user_customization')
    }, [])

    return (
        <SettingsContext.Provider
            value={{
                settings,
                customization,
                updateSettings,
                updateCustomization,
                addSavedFilter,
                removeSavedFilter,
                resetSettings,
            }}
        >
            {children}
        </SettingsContext.Provider>
    )
}

export const useSettings = (): SettingsContextType => {
    const context = useContext(SettingsContext)
    if (context === undefined) {
        throw new Error('useSettings must be used within SettingsProvider')
    }
    return context
}
