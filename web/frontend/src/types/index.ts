// ============ AUTHENTICATION ============
export type UserRole = 'superadmin' | 'admin' | 'member' | 'guest'

export interface User {
    id: number
    username: string
    first_name?: string
    last_name?: string
    is_bot?: boolean
    language_code?: string
    profile_picture_url?: string
}

export interface AuthUser extends User {
    role: UserRole
    managed_groups?: number[]
    permissions: Permission[]
    token?: string
    expires_at?: number
}

export interface Permission {
    action: string
    scope: 'self' | 'group' | 'system'
    allowed: boolean
}

export interface AuthResponse {
    success: boolean
    user: AuthUser
    token: string
    refresh_token?: string
    expires_at: number
}

export interface LoginCredentials {
    user_id: number
    username: string
    telegram_auth_token?: string
}

// ============ GROUPS ============
export interface Group {
    id: number
    name: string
    description?: string
    member_count: number
    admin_count: number
    created_at: string
    updated_at: string
    settings?: GroupSettings
    stats?: GroupStats
}

export interface GroupSettings {
    auto_moderation_enabled: boolean
    strict_mode: boolean
    welcome_message_enabled: boolean
    welcome_message?: string
    antispam_enabled: boolean
    profile_required: boolean
}

export interface GroupStats {
    total_bans: number
    total_kicks: number
    total_mutes: number
    total_warnings: number
    total_restricts: number
    actions_today: number
    actions_this_week: number
    last_action_at?: string
}

export interface GroupListResponse {
    success: boolean
    groups: Group[]
    total: number
    page: number
    page_size: number
}

// ============ MEMBERS ============
export type MemberStatus = 'active' | 'banned' | 'muted' | 'restricted' | 'warned' | 'left'

export interface GroupMember {
    id: number
    user_id: number
    group_id: number
    username?: string
    first_name?: string
    is_admin: boolean
    is_superadmin: boolean
    joined_at: string
    status: MemberStatus
    warnings: number
    restrictions?: Restriction[]
    last_action?: Action
    profile_url?: string
}

export interface Restriction {
    type: 'mute' | 'ban' | 'restrict' | 'warn'
    reason?: string
    until?: string
    issued_at: string
    issued_by: number
}

export interface UserProfile {
    user: User
    joined_groups: number[]
    managed_groups?: number[]
    total_warnings: number
    total_restrictions: number
    account_created_at: string
    last_active: string
    action_history: Action[]
}

// ============ ACTIONS ============
export type ActionType = 'ban' | 'kick' | 'mute' | 'unmute' | 'restrict' | 'unrestrict' | 'warn' | 'promote' | 'demote' | 'unban'
export type ActionStatus = 'pending' | 'completed' | 'failed' | 'cancelled'

export interface Action {
    id?: string
    action_type: ActionType
    group_id: number
    user_id: number
    username?: string
    initiated_by: number
    initiated_by_username?: string
    reason?: string
    duration?: number
    duration_unit?: 'seconds' | 'minutes' | 'hours' | 'days'
    status: ActionStatus
    created_at: string
    expires_at?: string
    notes?: string
}

export interface ActionResponse {
    success: boolean
    action_id: string
    user_id?: number
    username?: string
    message: string
    error?: string
}

export interface BatchActionRequest {
    actions: Omit<Action, 'id' | 'status' | 'created_at'>[]
}

export interface BatchActionResponse {
    success: boolean
    total: number
    successful: number
    failed: number
    results: ActionResponse[]
}

// ============ ANALYTICS ============
export interface ActionStats {
    timestamp: string
    users_count: number
    groups_count: number
    status: string
    recent_actions?: Action[]
    active_groups?: number
    total_actions?: number
}

export interface DashboardStats extends ActionStats {
    actions_today: number
    actions_this_week: number
    total_bans: number
    total_mutes: number
    total_warns: number
}

export interface HealthResponse {
    status: 'healthy' | 'unhealthy'
    service: string
    version: string
    database?: string
    api_v2?: string
}

// ============ FILTERS & PAGINATION ============
export interface FilterOptions {
    action_type?: ActionType
    status?: ActionStatus | MemberStatus
    group_id?: number
    user_id?: number
    date_from?: string
    date_to?: string
    sort_by?: string
    sort_order?: 'asc' | 'desc'
}

export interface PaginationParams {
    page: number
    page_size: number
    sort_by?: string
    sort_order?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
    success: boolean
    data: T[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface PaginationState {
    currentPage: number
    pageSize: number
    total: number
    totalPages: number
}

// ============ NOTIFICATIONS ============
export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface Notification {
    id: string
    type: NotificationType
    title: string
    message: string
    duration?: number
    action?: {
        label: string
        callback: () => void
    }
    timestamp: number
}

// ============ SETTINGS ============
export interface UserSettings {
    theme: 'light' | 'dark' | 'auto'
    notifications_enabled: boolean
    email_notifications: boolean
    session_timeout: number
    language: string
    timezone: string
    show_confirmations: boolean
    auto_refresh_dashboard: boolean
    refresh_interval: number
}

export interface DashboardCustomization {
    visible_widgets: string[]
    widget_order: string[]
    widget_sizes: Record<string, 'small' | 'medium' | 'large'>
    saved_filters: SavedFilter[]
}

export interface SavedFilter {
    id: string
    name: string
    filters: FilterOptions
    created_at: string
}

// ============ NAVIGATION ============
export interface Breadcrumb {
    label: string
    href?: string
    icon?: React.ReactNode
}

export interface NavItem {
    label: string
    href: string
    icon?: React.ReactNode
    badge?: number
    children?: NavItem[]
    requiredRole?: UserRole[]
}

// ============ TABLE CONFIGURATION ============
export interface TableColumn<T> {
    key: keyof T
    label: string
    sortable?: boolean
    filterable?: boolean
    width?: string
    render?: (value: any, row: T) => React.ReactNode
}

export interface TableState {
    sort_by?: string
    sort_order?: 'asc' | 'desc'
    page: number
    page_size: number
    filters?: FilterOptions
}

// ============ FORMS ============
export interface ExecuteActionForm {
    group_id: number
    user_input: string
    reason?: string
    duration?: number
    duration_unit?: 'minutes' | 'hours' | 'days'
    additional_options?: Record<string, boolean>
}

export interface BulkActionForm {
    group_id: number
    action_type: ActionType
    user_ids: number[]
    reason?: string
    duration?: number
}

// ============ EXPORT ============
export interface ExportOptions {
    format: 'csv' | 'json' | 'pdf' | 'excel'
    data_type: 'actions' | 'members' | 'groups' | 'analytics'
    filters?: FilterOptions
    include_headers?: boolean
    date_format?: string
}

export interface ExportResponse {
    success: boolean
    download_url: string
    file_name: string
    file_size: number
    created_at: string
}
