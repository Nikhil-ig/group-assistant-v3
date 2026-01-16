# Website Development - Components & Pages Guide

## 🎨 UI Component Structure

### Base Components (`/components/Common`)
```
Common/
├── NotificationsContainer.tsx     - Toast/notification display
├── LoadingSpinner.tsx              - Loading indicator
├── EmptyState.tsx                  - Empty data state
├── Pagination.tsx                  - Pagination control
├── SearchBar.tsx                   - Search input
├── FilterPanel.tsx                 - Advanced filters
├── DataTable.tsx                   - Reusable table component
├── Badge.tsx                       - Status badges
├── Avatar.tsx                      - User avatars
└── Modal.tsx                       - Modal dialog
```

### Layout Components (`/components/Layout`)
```
Layout/
├── MainLayout.tsx                  - Main wrapper with header/sidebar
├── Header.tsx                      - Top navigation bar
├── Sidebar.tsx                     - Left navigation
├── Breadcrumbs.tsx                 - Breadcrumb navigation
└── Footer.tsx                      - Footer section
```

### Dashboard Components (`/components/Dashboard`)
```
Dashboard/
├── StatsCards.tsx                  - KPI cards
├── RecentActions.tsx               - Recent actions widget
├── Charts/
│   ├── ActionChart.tsx            - Actions line chart
│   ├── TypeDistribution.tsx        - Action types pie
│   ├── TrendChart.tsx              - Trend analysis
│   └── HeatMap.tsx                 - Activity heatmap
├── QuickActions.tsx                - Quick action buttons
└── Widgets.tsx                     - Widget system
```

### Groups Components (`/components/Groups`)
```
Groups/
├── GroupsTable.tsx                 - Groups list table
├── GroupCard.tsx                   - Group card view
├── GroupDetails.tsx                - Group details modal
├── GroupFilters.tsx                - Group filtering
├── GroupForm.tsx                   - Create/edit group
├── GroupStats.tsx                  - Group statistics
└── MembersList.tsx                 - Members in group
```

### Members Components (`/components/Members`)
```
Members/
├── MembersTable.tsx                - Members list table
├── MemberCard.tsx                  - Member card
├── MemberDetails.tsx               - Member profile modal
├── MemberFilters.tsx               - Member filtering
├── MemberActions.tsx               - Action buttons (ban, kick, etc)
├── MemberHistory.tsx               - Action history for member
└── RestrictionDisplay.tsx          - Show restrictions
```

### Actions Components (`/components/Actions`)
```
Actions/
├── ActionModal.tsx                 - Generic action modal
├── BanForm.tsx                     - Ban user form
├── KickForm.tsx                    - Kick user form
├── MuteForm.tsx                    - Mute user form with duration
├── PromoteForm.tsx                 - Promote to admin
├── WarnForm.tsx                    - Issue warning
├── BulkActionForm.tsx              - Batch operations
├── ActionPreview.tsx               - Preview before execute
├── ActionHistory.tsx               - View action history
└── ActionStats.tsx                 - Action statistics
```

### Analytics Components (`/components/Analytics`)
```
Analytics/
├── MetricsOverview.tsx             - Overview cards
├── ActionTrends.tsx                - Trends chart
├── TopPerformers.tsx               - Top users/admins
├── GroupComparison.tsx             - Compare groups
├── ExportButton.tsx                - Export functionality
├── DateRangePicker.tsx             - Date range selector
└── Report.tsx                      - Report generator
```

## 📄 Page Structure

### Login Page (`/pages/login/index.tsx`)
- [ ] Telegram OAuth button
- [ ] Username/ID input
- [ ] Login form validation
- [ ] Remember me checkbox
- [ ] Error handling
- [ ] Loading state
- [ ] Responsive design

### Dashboard Page (`/pages/dashboard/index.tsx`)

**SuperAdmin Dashboard**
```
1. Global Stats (Total Groups, Users, Actions)
2. System Health
3. Recent Actions (All groups)
4. Top Groups by Activity
5. Top Admins by Actions
6. System Alerts/Warnings
7. Quick Actions (Ban user, Promote admin)
```

**Admin Dashboard**
```
1. My Groups Stats
2. Total Members Managed
3. Recent Actions (My groups only)
4. Member Activity
5. Warnings & Restrictions
6. Quick Actions (for my group)
```

**Member Dashboard**
```
1. My Groups (List)
2. My Status (Warnings, Restrictions)
3. My Permissions
4. My Action History
5. Group Policies
```

### Groups Page (`/pages/dashboard/groups/index.tsx`)
- [ ] Groups table with pagination
- [ ] Search/filter groups
- [ ] Create group button
- [ ] Group details modal
- [ ] Edit group form
- [ ] Delete group confirmation
- [ ] Group statistics
- [ ] Export groups

### Members Page (`/pages/dashboard/members/index.tsx`)
- [ ] Members table (paginated)
- [ ] Search members
- [ ] Filter by status
- [ ] Member details modal
- [ ] Execute actions dropdown
- [ ] Bulk action selection
- [ ] Member history
- [ ] Export members

### Analytics Page (`/pages/dashboard/analytics/index.tsx`)
- [ ] Date range picker
- [ ] KPI cards
- [ ] Action trends chart
- [ ] Action type distribution
- [ ] Top users/admins
- [ ] Group comparison
- [ ] Export reports
- [ ] Custom date ranges

### Profile Page (`/pages/dashboard/profile/index.tsx`)
- [ ] User profile info
- [ ] Managed groups list (for admins)
- [ ] Joined groups list (for members)
- [ ] Restrictions & Warnings
- [ ] Action history
- [ ] Settings/preferences
- [ ] Change theme
- [ ] Logout button

## 🎯 Page-Role Matrix

| Feature | SuperAdmin | Admin | Member |
|---------|-----------|-------|--------|
| Dashboard | System Overview | Group Overview | Personal |
| View All Groups | ✅ | ✅ (Own) | ❌ |
| Manage Groups | ✅ | ❌ | ❌ |
| View All Members | ✅ | ✅ (Group) | ❌ |
| Ban Users | ✅ | ✅ (Group) | ❌ |
| Promote Admins | ✅ | ✅ (Group) | ❌ |
| View Analytics | ✅ (Global) | ✅ (Group) | ❌ |
| View Own Profile | ✅ | ✅ | ✅ |
| View Restrictions | ✅ | ✅ | ✅ (Own) |
| Export Data | ✅ | ✅ | ❌ |

## 🔌 API Integration Points

### Pages That Need API Calls

**Dashboard**
- `useSystemAnalytics()` - Superadmin only
- `useGroupAnalytics()` - Admin, their groups
- `useActionTrends()`
- `useTopUsers()`

**Groups**
- `useGroups()` - List all groups
- `useGroup()` - Get group details
- `useGroupStats()` - Get group statistics

**Members**
- `useGroupMembers()` - List members in group
- `useMember()` - Get member details
- `useMemberHistory()` - Action history

**Actions**
- `useBanUser()` - Ban user
- `useKickUser()` - Kick user
- `useMuteUser()` - Mute user
- `usePromoteUser()` - Promote to admin
- `useActionHistory()` - Get action history

**Analytics**
- `useActionTrends()` - Trends data
- `useTopUsers()` - Top performers
- `useGroupAnalytics()` - Group stats

## 🎨 Styling Strategy

### Tailwind CSS Setup
```
- Primary Color: Indigo (600-900)
- Secondary Color: Blue (400-700)
- Success: Emerald
- Warning: Amber
- Error: Red
- Neutral: Slate
```

### Component Variants
```
Button: primary, secondary, outline, ghost, danger
Input: default, error, disabled, focus
Card: default, elevated, outlined
Badge: success, warning, error, info, neutral
```

### Responsive Breakpoints
```
sm: 640px  - Mobile
md: 768px  - Tablet
lg: 1024px - Desktop
xl: 1280px - Large Desktop
```

## 📦 Export Order for Building

1. **Common Components** (Foundation)
   - Buttons, inputs, cards, badges

2. **Layout Components** (Structure)
   - Header, sidebar, main layout

3. **Dashboard Components** (Views)
   - Stats, charts, widgets

4. **Specific Components** (Features)
   - Groups, members, actions

5. **Pages** (Containers)
   - Login, dashboard, groups, members, analytics

6. **Context & Hooks** (Logic)
   - Already created ✅

7. **App.tsx** (Entry point)
   - Already created ✅

## 🚀 Quick Implementation Priority

### TIER 1 (MVP - Hours 1-3)
- [ ] Login page
- [ ] Basic dashboard
- [ ] Groups list
- [ ] Members list
- [ ] Action modals

### TIER 2 (Core Features - Hours 4-6)
- [ ] Analytics page
- [ ] Advanced filtering
- [ ] Bulk actions
- [ ] Action history

### TIER 3 (Polish - Hours 7-8)
- [ ] Charts & visualizations
- [ ] Export functionality
- [ ] Real-time updates
- [ ] Mobile responsive

### TIER 4 (Advanced - Hours 9+)
- [ ] Dark mode
- [ ] Dashboard customization
- [ ] Saved filters
- [ ] Accessibility

## ✅ Implementation Checklist

- [x] Types defined
- [x] API client created
- [x] Auth context
- [x] Notification context
- [x] Settings context
- [x] API hooks
- [x] App.tsx routing
- [ ] Common components
- [ ] Layout components
- [ ] Dashboard components
- [ ] Groups components
- [ ] Members components
- [ ] Actions components
- [ ] Analytics components
- [ ] Login page
- [ ] All dashboard pages
- [ ] Testing
- [ ] Deployment

---

**Status**: Ready for component implementation
**Next**: Start with Common components, then Layout, then Pages
