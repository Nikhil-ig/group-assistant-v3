# Telegram OAuth Implementation Checklist

## Frontend Setup (✅ DONE)

- [x] Install dependencies
- [x] Create Login.tsx with Telegram OAuth widget
- [x] Create Signup.tsx for new admin accounts
- [x] Update App.tsx routing
- [x] Add ErrorBoundary component
- [x] Fix Tailwind CSS issues
- [x] Implement session management (JWT)
- [x] Add authentication context (AuthContext)
- [x] Create multiple login methods:
  - [x] Telegram OAuth button
  - [x] Email/Password form
  - [x] Demo login button

## Backend Setup (⏳ TODO - Use Example File)

### Create `/api/auth/telegram` Endpoint

```python
# In centralized_api/app.py or auth module

@app.post("/api/auth/telegram")
async def telegram_auth(auth_data: TelegramAuthRequest):
    """Authenticate via Telegram OAuth"""
    # 1. Verify hash signature
    # 2. Create/update user in database
    # 3. Generate JWT token
    # 4. Return token + user data
```

**Reference**: `telegram_auth_backend_example.py`

### Create `/api/auth/register` Endpoint

```python
@app.post("/api/auth/register")
async def register(user_data: RegisterRequest):
    """Register new admin account"""
    # 1. Validate input
    # 2. Check email doesn't exist
    # 3. Hash password
    # 4. Create user in database
    # 5. Return success + redirect to login
```

### Environment Variables

Add to your `.env`:
```bash
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
```

## Configuration

### Telegram Bot Setup

- [ ] Create bot with @BotFather (`/newbot`)
- [ ] Get bot token
- [ ] Get bot username
- [ ] Set bot domain in BotFather settings
  - Dev: `localhost:5174`
  - Prod: `yourdomain.com`

### Update Frontend Files

**File**: `web/frontend/index.html`
- [ ] Replace `YOUR_BOT_USERNAME` with actual username

**File**: `web/frontend/src/pages/Login.tsx`
- [x] Already configured (uses placeholder)

## Testing Checklist

### Local Testing

- [ ] Start frontend: `npm run dev` (from web/frontend)
- [ ] Start backend: Run your API server
- [ ] Open http://localhost:5174
- [ ] Test Telegram button (click and authenticate)
- [ ] Verify backend receives user data
- [ ] Verify JWT token is returned
- [ ] Verify localStorage has token
- [ ] Test redirect to dashboard
- [ ] Test Demo Login button
- [ ] Test Email/Password login
- [ ] Test Signup flow

### Error Scenarios

- [ ] Test invalid hash (should fail auth)
- [ ] Test old timestamp (should fail auth)
- [ ] Test network error handling
- [ ] Test missing backend endpoint
- [ ] Test CORS issues

## Database Schema (Suggested)

```sql
-- Users table
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    username VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    photo_url TEXT,
    password_hash VARCHAR(255),  -- For email/password auth
    role VARCHAR(50),  -- admin, superadmin, member
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Permissions table
CREATE TABLE permissions (
    id INT PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    action VARCHAR(100),
    scope VARCHAR(50),  -- self, group, system
    allowed BOOLEAN,
    UNIQUE(user_id, action, scope)
);
```

## Code Organization

```
centralized_api/
├── app.py
├── routes/
│   ├── auth.py          ← Add Telegram auth here
│   └── telegram.py      ← Or create separate module
└── utils/
    ├── jwt.py
    ├── telegram_verify.py  ← Hash verification
    └── password.py
```

## Security Checklist

- [ ] HTTPS enabled in production
- [ ] CORS properly configured
- [ ] JWT secret key stored securely
- [ ] Telegram bot token in environment variables
- [ ] Hash verification implemented
- [ ] Timestamp validation (max 10 mins)
- [ ] Rate limiting on auth endpoints
- [ ] Password hashing (for email auth)
- [ ] SQL injection prevention
- [ ] CSRF protection

## Deployment Checklist

- [ ] Frontend built (`npm run build`)
- [ ] Backend running with correct environment
- [ ] Database migrations applied
- [ ] Bot domain updated in BotFather
- [ ] HTTPS certificates configured
- [ ] JWT secret key configured
- [ ] Error logging enabled
- [ ] Monitoring/alerting set up

## Documentation

- [x] TELEGRAM_OAUTH_SETUP.md (Setup guide)
- [x] TELEGRAM_OAUTH_IMPLEMENTATION.md (Overview)
- [x] telegram_auth_backend_example.py (Code example)
- [ ] API documentation (create with your backend)
- [ ] Architecture diagram (optional)

## Support Resources

**Telegram Official Docs**:
- https://core.telegram.org/widgets/login
- https://core.telegram.org/bots/api

**Code Examples**:
- See `telegram_auth_backend_example.py`
- See `Login.tsx` in frontend

**Getting Help**:
1. Check browser console for errors
2. Check backend logs
3. Review Telegram widget docs
4. Verify bot domain is set

---

## Progress Tracking

**Frontend**: ✅ 100% Complete
- Login page with all methods
- Signup page
- Auth context
- Error handling
- Session management

**Backend**: ⏳ 0% - Awaiting Implementation
- Telegram auth endpoint
- User registration endpoint  
- Database setup
- JWT validation

**Overall**: ~50% Complete (Frontend done, Backend needed)

## Next Immediate Steps

1. Copy code from `telegram_auth_backend_example.py`
2. Implement in your backend
3. Set up environment variables
4. Update database schema
5. Create Telegram bot
6. Test end-to-end flow

Once backend is ready:
- [x] Frontend ready to use
- [x] All frontend features implemented
- ⏳ Backend integration pending
