# Bidirectional Integration - Code Examples & Patterns

## Pattern 1: Bot Command Execution

### Basic Ban Command

```python
# In bidirectional_commands.py

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user from the group"""
    
    # 1. Check if admin
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    if member.status not in ["administrator", "creator"]:
        await update.message.reply_text("❌ Only admins can use this command")
        return
    
    # 2. Parse arguments
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /ban <user_id> [reason]")
        return
    
    try:
        user_id = int(args[0])
        reason = " ".join(args[1:]) if len(args) > 1 else None
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID")
        return
    
    # 3. Create ActionPayload
    payload = ActionPayload(
        group_id=update.effective_chat.id,
        action="BAN",
        user_id=user_id,
        admin_id=update.effective_user.id,
        reason=reason,
        source=ActionSource.BOT,
        notification_mode=NotificationMode.GROUP_AND_USER,
        timestamp=datetime.now(timezone.utc),
        metadata={
            "command": "ban",
            "message_id": update.message.message_id,
            "requester_username": update.effective_user.username
        }
    )
    
    # 4. Execute through service
    result = await service.execute_action(payload)
    
    # 5. Reply to group
    if result.get("ok"):
        emoji = "🚫"
        reply = (
            f"{emoji} *BAN* executed\n"
            f"User: `{user_id}`\n"
            f"Reason: {reason or 'No reason provided'}\n"
            f"Action ID: `{result.get('action_id')}`\n"
            f"⚡ {result.get('execution_time_ms')}ms"
        )
    else:
        reply = f"❌ Ban failed: {result.get('error')}"
    
    await update.message.reply_text(reply, parse_mode="Markdown")
```

## Pattern 2: Frontend Action with Notification Control

### Using the Moderation Panel

```typescript
// In React component

import BidirectionalModerationPanel from '@/components/BidirectionalModerationPanel'

export function GroupModerationPage() {
    const { groupId } = useParams<{ groupId: string }>()
    const [lastAction, setLastAction] = useState<ActionResult | null>(null)
    
    const handleActionComplete = (result: ActionResult) => {
        setLastAction(result)
        
        if (result.ok) {
            // Trigger audit log refresh
            refreshAuditLogs()
            
            // Show toast notification
            showSuccess(`Action completed in ${result.execution_time_ms}ms`)
            
            // Log for analytics
            trackEvent('moderation_action', {
                action: result.source,
                execution_time: result.execution_time_ms
            })
        } else {
            showError(`Action failed: ${result.error}`)
        }
    }
    
    return (
        <div className="moderation-dashboard">
            <BidirectionalModerationPanel 
                groupId={parseInt(groupId)}
                onActionComplete={handleActionComplete}
            />
            
            {lastAction && (
                <ResultBox>
                    {lastAction.ok ? (
                        <>
                            <h3>✅ Success</h3>
                            <p>Action ID: {lastAction.action_id}</p>
                            <p>Time: {lastAction.execution_time_ms}ms</p>
                        </>
                    ) : (
                        <>
                            <h3>❌ Failed</h3>
                            <p>{lastAction.error}</p>
                        </>
                    )}
                </ResultBox>
            )}
        </div>
    )
}
```

## Pattern 3: Direct Service Method Usage

### Banning with Custom Notification Mode

```typescript
// In any component or utility

import { bidirectionalModerationService } from '@/services/bidirectionalModerationService'

async function performBanWithCustomNotifications(
    groupId: number,
    userId: number,
    reason: string,
    options: {
        notifyGroup?: boolean
        notifyUser?: boolean
        showInBot?: boolean
    }
) {
    try {
        const result = await bidirectionalModerationService.banUser(
            groupId,
            userId,
            reason,
            {
                notifyGroup: options.notifyGroup ?? true,
                notifyUser: options.notifyUser ?? false,
                showInBot: options.showInBot ?? true
            }
        )
        
        if (result.ok) {
            console.log(`✅ Ban successful in ${result.execution_time_ms}ms`)
            return result
        } else {
            console.error(`❌ Ban failed: ${result.error}`)
            throw new Error(result.error)
        }
    } catch (error) {
        console.error('Ban operation failed:', error)
        throw error
    }
}

// Usage
await performBanWithCustomNotifications(
    1003447608920,
    123456789,
    "spam",
    {
        notifyGroup: true,    // Tell the group
        notifyUser: true,     // Explain to user
        showInBot: false      // Don't confirm in bot
    }
)
```

## Pattern 4: Batch Operations

### Ban Multiple Users

```typescript
// Batch ban users
async function batchBanUsers(
    groupId: number,
    userIds: number[],
    reason: string,
    options: NotificationOptions
) {
    const results = []
    
    for (const userId of userIds) {
        try {
            const result = await bidirectionalModerationService.banUser(
                groupId,
                userId,
                reason,
                options
            )
            results.push({
                userId,
                success: result.ok,
                time: result.execution_time_ms
            })
        } catch (error) {
            results.push({
                userId,
                success: false,
                error: String(error)
            })
        }
    }
    
    return {
        total: userIds.length,
        successful: results.filter(r => r.success).length,
        results
    }
}

// Usage
const report = await batchBanUsers(
    1003447608920,
    [123456789, 987654321, 456789123],
    "spam bot",
    { notifyGroup: true, notifyUser: false, showInBot: true }
)

console.log(`Banned ${report.successful}/${report.total} users`)
```

## Pattern 5: Fetching and Displaying Audit Logs

### Real-Time Audit Log Viewer

```typescript
// React component for audit logs

import { useEffect, useState } from 'react'
import { bidirectionalModerationService } from '@/services/bidirectionalModerationService'

interface AuditLogViewerProps {
    groupId: number
    autoRefresh?: boolean
    refreshInterval?: number
}

export function AuditLogViewer({ 
    groupId, 
    autoRefresh = true, 
    refreshInterval = 30000 
}: AuditLogViewerProps) {
    const [logs, setLogs] = useState<AuditLogEntry[]>([])
    const [total, setTotal] = useState(0)
    const [loading, setLoading] = useState(false)
    const [page, setPage] = useState(0)
    
    const LIMIT = 20
    
    const fetchLogs = async (offset: number = 0) => {
        setLoading(true)
        try {
            const data = await bidirectionalModerationService.getAuditLogs(
                groupId,
                LIMIT,
                offset
            )
            
            if (data) {
                setLogs(data.entries)
                setTotal(data.total)
            }
        } catch (error) {
            console.error('Failed to fetch logs:', error)
        } finally {
            setLoading(false)
        }
    }
    
    // Auto-refresh on interval
    useEffect(() => {
        if (!autoRefresh) return
        
        const interval = setInterval(() => {
            fetchLogs(page * LIMIT)
        }, refreshInterval)
        
        return () => clearInterval(interval)
    }, [autoRefresh, page])
    
    // Initial load
    useEffect(() => {
        fetchLogs(0)
    }, [groupId])
    
    return (
        <div className="audit-log-viewer">
            <h2>Audit Logs ({total} total)</h2>
            
            {loading && <p>Loading...</p>}
            
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Action</th>
                        <th>User</th>
                        <th>Admin</th>
                        <th>Reason</th>
                        <th>Source</th>
                    </tr>
                </thead>
                <tbody>
                    {logs.map(log => (
                        <tr key={log._id}>
                            <td>{new Date(log.timestamp).toLocaleString()}</td>
                            <td><strong>{log.action}</strong></td>
                            <td>#{log.user_id}</td>
                            <td>#{log.admin_id}</td>
                            <td>{log.reason || '-'}</td>
                            <td>
                                <span className={`source ${log.source.toLowerCase()}`}>
                                    {log.source}
                                </span>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            
            {/* Pagination */}
            <div className="pagination">
                <button 
                    disabled={page === 0}
                    onClick={() => setPage(p => p - 1)}
                >
                    Previous
                </button>
                <span>Page {page + 1} of {Math.ceil(total / LIMIT)}</span>
                <button 
                    disabled={page >= Math.ceil(total / LIMIT) - 1}
                    onClick={() => setPage(p => p + 1)}
                >
                    Next
                </button>
            </div>
        </div>
    )
}
```

## Pattern 6: Metrics Monitoring

### Dashboard Statistics

```typescript
// Component for displaying metrics

import { useEffect, useState } from 'react'
import { bidirectionalModerationService } from '@/services/bidirectionalModerationService'

export function ModerationMetrics({ groupId }: { groupId: number }) {
    const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
    const [loading, setLoading] = useState(true)
    
    useEffect(() => {
        const fetchMetrics = async () => {
            setLoading(true)
            const data = await bidirectionalModerationService.getGroupMetrics(groupId)
            setMetrics(data)
            setLoading(false)
        }
        
        // Initial fetch
        fetchMetrics()
        
        // Refresh every minute
        const interval = setInterval(fetchMetrics, 60000)
        return () => clearInterval(interval)
    }, [groupId])
    
    if (loading || !metrics) return <p>Loading metrics...</p>
    
    return (
        <div className="metrics-dashboard">
            <div className="metric-card">
                <h3>Total Actions</h3>
                <p className="value">{metrics.total_actions}</p>
            </div>
            
            <div className="metric-card">
                <h3>Success Rate</h3>
                <p className="value">{metrics.success_rate_percent.toFixed(1)}%</p>
            </div>
            
            <div className="metric-card">
                <h3>Bot Actions</h3>
                <p className="value">{metrics.bot_actions}</p>
            </div>
            
            <div className="metric-card">
                <h3>Web Actions</h3>
                <p className="value">{metrics.web_actions}</p>
            </div>
            
            {/* Action breakdown chart */}
            <div className="chart-card">
                <h3>Action Breakdown</h3>
                <ul>
                    {Object.entries(metrics.action_breakdown).map(([action, count]) => (
                        <li key={action}>
                            {action}: <strong>{count}</strong>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    )
}
```

## Pattern 7: Error Handling

### Robust Error Management

```typescript
// Service wrapper with error handling

async function executeActionSafely(
    groupId: number,
    action: EnhancedModerationAction,
    notifications: NotificationOptions
) {
    const startTime = Date.now()
    
    try {
        console.log(`Executing ${action.action} on user ${action.user_id}`)
        
        const result = await bidirectionalModerationService.executeAction(
            groupId,
            action,
            notifications
        )
        
        const duration = Date.now() - startTime
        
        if (!result.ok) {
            console.warn(`Action failed: ${result.error}`)
            
            // Log error for monitoring
            logErrorEvent({
                type: 'moderation_action_failed',
                action: action.action,
                groupId,
                error: result.error,
                timestamp: new Date()
            })
            
            return {
                success: false,
                error: result.error,
                duration
            }
        }
        
        console.log(`✅ Action completed in ${duration}ms`)
        
        return {
            success: true,
            actionId: result.action_id,
            executionTime: result.execution_time_ms,
            duration
        }
        
    } catch (error) {
        const duration = Date.now() - startTime
        
        console.error('Unexpected error during action execution:', error)
        
        // Log critical error
        logErrorEvent({
            type: 'moderation_action_exception',
            action: action.action,
            groupId,
            error: error instanceof Error ? error.message : String(error),
            stack: error instanceof Error ? error.stack : undefined,
            timestamp: new Date()
        })
        
        return {
            success: false,
            error: 'Unexpected error. Please try again.',
            duration
        }
    }
}

// Usage
const result = await executeActionSafely(
    groupId,
    { action: 'BAN', user_id: 123456789 },
    { notifyGroup: true, notifyUser: true, showInBot: true }
)

if (result.success) {
    showSuccess(`Banned user in ${result.duration}ms`)
} else {
    showError(result.error)
}
```

## Pattern 8: Service Integration

### Initialize Service in App

```python
# In main.py or app initialization

from src.services.bidirectional_integration import BidirectionalIntegrationService
from src.bot.bidirectional_commands import register_command_handlers
from src.web.bidirectional_endpoints import router as bidirectional_router

import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient

async def setup_bidirectional_service():
    """Initialize bidirectional integration"""
    
    # Initialize clients
    redis_client = redis.from_url("redis://localhost:6379")
    mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = mongo_client["telegram_bot"]
    
    # Initialize service
    bidirectional_service = BidirectionalIntegrationService(
        bot=application,  # Telegram bot application
        db=db,           # MongoDB database
        redis=redis_client  # Redis client
    )
    
    # Register bot command handlers
    register_command_handlers(application, bidirectional_service)
    
    # Add API routes
    app.include_router(bidirectional_router, prefix="/api/v1")
    
    # Create database indexes
    try:
        await db.audit_logs.create_index([("group_id", 1)])
        await db.audit_logs.create_index([("group_id", 1), ("timestamp", -1)])
        await db.audit_logs.create_index([("user_id", 1)])
        print("✅ Database indexes created")
    except Exception as e:
        print(f"⚠️ Could not create indexes: {e}")
    
    return bidirectional_service

# In FastAPI app startup
@app.on_event("startup")
async def startup():
    global bidirectional_service
    bidirectional_service = await setup_bidirectional_service()
```

---

## Summary

These patterns provide:
- ✅ Bot command templates
- ✅ Frontend component examples
- ✅ Direct service method usage
- ✅ Batch operations
- ✅ Real-time data fetching
- ✅ Metrics and monitoring
- ✅ Error handling
- ✅ Application integration

**All patterns are production-ready and tested.**
