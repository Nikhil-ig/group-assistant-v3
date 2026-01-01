/**
 * V3 Telegram Moderation Bot - Frontend Service
 * TypeScript API client for interacting with the backend
 */

// ===== TYPE DEFINITIONS =====

interface LoginRequest {
  user_id: number;
  username: string;
  first_name: string;
}

interface LoginResponse {
  ok: boolean;
  token?: string;
  role?: string;
  message: string;
}

interface ModActionRequest {
  action_type: string;
  target_user_id: number;
  target_username?: string;
  reason?: string;
  duration_hours?: number;
}

interface ModActionResponse {
  ok: boolean;
  action_id?: string;
  message: string;
  timestamp: string;
}

interface AuditLogEntry {
  action_type: string;
  admin_username: string;
  target_username?: string;
  reason?: string;
  timestamp: string;
}

interface AuditLogsResponse {
  ok: boolean;
  group_id: number;
  logs: AuditLogEntry[];
  total_count: number;
  page: number;
  page_size: number;
}

interface MetricsResponse {
  ok: boolean;
  group_id: number;
  total_actions: number;
  actions_breakdown: { [key: string]: number };
  last_action_at?: string;
}

interface GroupInfo {
  group_id: number;
  group_name: string;
  created_at: string;
  is_active: boolean;
}

interface GroupsListResponse {
  ok: boolean;
  groups: GroupInfo[];
  total_count: number;
}


interface MemberEntry {
  user_id: number;
  username?: string;
  first_name?: string;
  is_bot?: boolean;
  last_seen?: string | null;
}

interface MembersListResponse {
  ok: boolean;
  group_id: number;
  members: MemberEntry[];
  total_count: number;
  page: number;
  page_size: number;
}

interface BlacklistEntry {
  user_id: number;
  username?: string;
  reason?: string;
  added_by?: number | null;
  added_at?: string | null;
}

interface BlacklistResponse {
  ok: boolean;
  group_id: number;
  entries: BlacklistEntry[];
  total_count: number;
  page: number;
  page_size: number;
}


// ===== SERVICE CLASS =====

export class V3ModerationService {
  private apiBaseUrl: string;
  private token: string | null = null;
  private apiPrefix = "/api/v1";

  constructor(apiBaseUrl: string = "http://localhost:8000") {
    this.apiBaseUrl = apiBaseUrl;
    this.loadTokenFromStorage();
  }

  /**
   * Load token from localStorage on initialization
   */
  private loadTokenFromStorage(): void {
    if (typeof localStorage !== "undefined") {
      const stored = localStorage.getItem("moderation_token");
      if (stored) {
        this.token = stored;
      }
    }
  }

  /**
   * Save token to localStorage
   */
  private saveTokenToStorage(): void {
    if (typeof localStorage !== "undefined" && this.token) {
      localStorage.setItem("moderation_token", this.token);
    }
  }

  /**
   * Set authentication token
   */
  setToken(token: string): void {
    this.token = token;
    this.saveTokenToStorage();
  }

  /**
   * Get authorization header
   */
  private getAuthHeader(): { Authorization?: string } {
    if (!this.token) {
      return {};
    }
    return {
      Authorization: `Bearer ${this.token}`,
    };
  }

  /**
   * Make authenticated API request
   */
  private async request<T>(
    method: string,
    path: string,
    body?: any
  ): Promise<T> {
    const url = `${this.apiBaseUrl}${this.apiPrefix}${path}`;

    const options: RequestInit = {
      method,
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeader(),
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  }

  // ===== AUTHENTICATION =====

  async login(
    userId: number,
    username: string,
    firstName: string
  ): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>("POST", "/auth/login", {
      user_id: userId,
      username,
      first_name: firstName,
    });

    if (response.ok && response.token) {
      this.setToken(response.token);
    }

    return response;
  }

  // ===== GROUPS =====

  async getGroups(): Promise<GroupsListResponse> {
    return this.request<GroupsListResponse>("GET", "/groups");
  }

  // ===== MODERATION ACTIONS =====

  async ban(
    groupId: number,
    userId: number,
    reason?: string,
    username?: string
  ): Promise<ModActionResponse> {
    return this.request<ModActionResponse>(
      "POST",
      `/groups/${groupId}/actions`,
      {
        action_type: "ban",
        target_user_id: userId,
        target_username: username,
        reason,
      }
    );
  }

  async unban(
    groupId: number,
    userId: number,
    username?: string
  ): Promise<ModActionResponse> {
    return this.request<ModActionResponse>(
      "POST",
      `/groups/${groupId}/actions`,
      {
        action_type: "unban",
        target_user_id: userId,
        target_username: username,
      }
    );
  }

  async kick(
    groupId: number,
    userId: number,
    reason?: string,
    username?: string
  ): Promise<ModActionResponse> {
    return this.request<ModActionResponse>(
      "POST",
      `/groups/${groupId}/actions`,
      {
        action_type: "kick",
        target_user_id: userId,
        target_username: username,
        reason,
      }
    );
  }

  async warn(
    groupId: number,
    userId: number,
    reason?: string,
    username?: string
  ): Promise<ModActionResponse> {
    return this.request<ModActionResponse>(
      "POST",
      `/groups/${groupId}/actions`,
      {
        action_type: "warn",
        target_user_id: userId,
        target_username: username,
        reason,
      }
    );
  }

  async mute(
    groupId: number,
    userId: number,
    durationHours?: number,
    reason?: string,
    username?: string
  ): Promise<ModActionResponse> {
    return this.request<ModActionResponse>(
      "POST",
      `/groups/${groupId}/actions`,
      {
        action_type: "mute",
        target_user_id: userId,
        target_username: username,
        duration_hours: durationHours,
        reason,
      }
    );
  }

  async unmute(
    groupId: number,
    userId: number,
    username?: string
  ): Promise<ModActionResponse> {
    return this.request<ModActionResponse>(
      "POST",
      `/groups/${groupId}/actions`,
      {
        action_type: "unmute",
        target_user_id: userId,
        target_username: username,
      }
    );
  }

  // ===== AUDIT LOGS =====

  async getAuditLogs(
    groupId: number,
    page: number = 1,
    pageSize: number = 20
  ): Promise<AuditLogsResponse> {
    return this.request<AuditLogsResponse>(
      "GET",
      `/groups/${groupId}/logs?page=${page}&page_size=${pageSize}`
    );
  }

  // ===== MEMBERS =====

  async getMembers(
    groupId: number,
    page: number = 1,
    pageSize: number = 50
  ): Promise<MembersListResponse> {
    return this.request<MembersListResponse>(
      "GET",
      `/groups/${groupId}/members?page=${page}&page_size=${pageSize}`
    );
  }

  // ===== BLACKLIST =====

  async getBlacklist(
    groupId: number,
    page: number = 1,
    pageSize: number = 50
  ): Promise<BlacklistResponse> {
    return this.request<BlacklistResponse>(
      "GET",
      `/groups/${groupId}/blacklist?page=${page}&page_size=${pageSize}`
    );
  }

  // ===== METRICS =====

  async getMetrics(groupId: number): Promise<MetricsResponse> {
    return this.request<MetricsResponse>(
      "GET",
      `/groups/${groupId}/metrics`
    );
  }

  // ===== NEW COMMANDS (Free, ID, Settings, Promote, Demote) =====

  /**
   * Free a user from all restrictions (opposite of /restrict)
   */
  async freeUser(
    groupId: number,
    targetUserId: number,
    targetUsername?: string
  ): Promise<{ ok: boolean; message: string; action_id?: string }> {
    return this.request(
      "POST",
      "/commands/free",
      {
        group_id: groupId,
        target_user_id: targetUserId,
        target_username: targetUsername,
      }
    );
  }

  /**
   * Get user ID and information
   */
  async getUserID(
    groupId: number,
    targetUserId?: number
  ): Promise<{
    ok: boolean;
    user?: {
      user_id: number;
      first_name?: string;
      last_name?: string;
      username?: string;
      is_bot: boolean;
      group_id?: number;
      group_name?: string;
    };
    message: string;
  }> {
    return this.request(
      "POST",
      "/commands/id",
      {
        group_id: groupId,
        target_user_id: targetUserId,
      }
    );
  }

  /**
   * Get group settings and admin list
   */
  async getGroupSettings(groupId: number): Promise<{
    ok: boolean;
    settings?: {
      group_id: number;
      group_name: string;
      group_type: string;
      member_count: number;
      admins: Array<{
        user_id: number;
        username?: string;
        first_name?: string;
        last_name?: string;
        custom_title?: string;
      }>;
      description?: string;
    };
    message: string;
  }> {
    return this.request("GET", `/commands/settings/${groupId}`);
  }

  /**
   * Promote a user to admin with optional custom title
   */
  async promoteUser(
    groupId: number,
    targetUserId: number,
    customTitle?: string,
    targetUsername?: string
  ): Promise<{
    ok: boolean;
    message: string;
    action_id?: string;
    title_set?: boolean;
  }> {
    return this.request(
      "POST",
      "/commands/promote",
      {
        group_id: groupId,
        target_user_id: targetUserId,
        target_username: targetUsername,
        custom_title: customTitle,
      }
    );
  }

  /**
   * Demote an admin back to regular user
   */
  async demoteUser(
    groupId: number,
    targetUserId: number,
    targetUsername?: string
  ): Promise<{ ok: boolean; message: string; action_id?: string }> {
    return this.request(
      "POST",
      "/commands/demote",
      {
        group_id: groupId,
        target_user_id: targetUserId,
        target_username: targetUsername,
      }
    );
  }

  // ===== HEALTH =====

  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request("GET", "/health");
  }
}


// ===== EXPORT DEFAULT INSTANCE =====

export const moderationService = new V3ModerationService();
