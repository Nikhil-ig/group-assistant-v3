# Telegram OAuth - Quick Reference Card

## 🎯 What's Working

✅ **Frontend Login Page** with 3 authentication methods:
1. **Telegram OAuth Button** - Click to login with Telegram
2. **Email/Password Form** - Traditional login
3. **Demo Login** - Test account (superadmin role)

✅ **Signup Page** - Create new admin accounts

✅ **Session Management** - JWT tokens, auto-login

✅ **Error Handling** - User-friendly messages

## 📝 Quick Setup (5 minutes)

### Step 1: Create Telegram Bot
```
Open Telegram → Search @BotFather → /newbot
→ Save your BOT_TOKEN and BOT_USERNAME
```

### Step 2: Update Bot Domain
```
In BotFather:
/mybots → Your Bot → Bot Settings → Domain
→ Set to: localhost:5174 (dev) or yourdomain.com (prod)
```

### Step 3: Update Frontend  
Edit `web/frontend/index.html`, find this line:
```html
data-telegram-login="YOUR_BOT_USERNAME"
```
Replace `YOUR_BOT_USERNAME` with your actual bot username.

### Step 4: Implement Backend Endpoint
Copy code from: `telegram_auth_backend_example.py`

Implement endpoint `POST /api/auth/telegram` that:
- Receives Telegram user data
- Verifies hash signature
- Returns JWT token

### Step 5: Test
```bash
Frontend: http://localhost:5174
Click Telegram button → Authenticate → Should redirect to dashboard
```

## 🔗 API Reference

### Telegram Auth Endpoint
```
POST /api/auth/telegram
Content-Type: application/json

Request:
{
  "telegram_id": 123456789,
  "first_name": "John",
  "username": "johndoe",
  "auth_date": 1705329600,
  "hash": "abc123..."
}

Response (200):
{
  "access_token": "eyJ0eXAi...",
  "user": {
    "id": 123456789,
    "username": "johndoe",
    "role": "admin"
  }
}

Error (401):
{"detail": "Invalid authentication hash"}
```

### Email Login Endpoint
```
POST /api/auth/login
{
  "email": "admin@example.com",
  "password": "password123"
}
```

### Signup Endpoint  
```
POST /api/auth/register
{
  "email": "admin@example.com",
  "username": "admin_user",
  "password": "password123",
  "role": "admin"
}
```

## 🛡️ Security: Hash Verification

```python
import hashlib, hmac

def verify_telegram_auth(data, bot_token):
    hash_val = data.pop('hash')
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    data_check = '\n'.join(f'{k}={v}' for k, v in sorted(data.items()))
    computed = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()
    return computed == hash_val
```

## 📁 Key Files

```
web/frontend/
├── src/pages/Login.tsx          ← Telegram OAuth integration
├── src/pages/Signup.tsx         ← New account creation
├── src/App.tsx                  ← Routes setup
└── index.html                   ← Telegram widget (needs update)

Backend:
├── telegram_auth_backend_example.py  ← Copy this
└── centralized_api/app.py            ← Implement here

Docs:
├── TELEGRAM_OAUTH_SETUP.md
├── TELEGRAM_OAUTH_IMPLEMENTATION.md
├── TELEGRAM_OAUTH_CHECKLIST.md
└── telegram_auth_backend_example.py
```

## 🧪 Test Logins

**Telegram OAuth**: Click widget → Select account → Auto-login

**Email/Password**: 
- Email: admin@example.com
- Password: password123

**Demo Account**: Click "Demo Login" → Superadmin access

## ⚙️ Environment Variables

```bash
TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
```

## 🚨 Common Issues

| Problem | Solution |
|---------|----------|
| Widget not showing | Check bot username in index.html |
| "Invalid hash" error | Verify bot token in environment |
| CORS error | Add frontend domain to CORS config |
| Token not working | Check JWT secret key matches |
| Redirect failing | Verify `/dashboard` route exists |

## 📊 Status

- ✅ Frontend: 100% Done
- ⏳ Backend: Needs Implementation
- 🎯 Overall: Ready for Backend Integration

## 🚀 Get Started

1. Create bot with @BotFather (2 min)
2. Update index.html with bot username (1 min)
3. Implement /api/auth/telegram endpoint (15 min)
4. Test end-to-end (5 min)
5. Deploy to production

**Total Time**: ~30 minutes

## 📞 Need Help?

- 📖 Read: TELEGRAM_OAUTH_SETUP.md
- 💻 Copy: telegram_auth_backend_example.py
- 🔍 Check: browser console for errors
- 📚 Reference: https://core.telegram.org/widgets/login

---

**Last Updated**: 2026-01-15  
**Status**: Ready for Backend Implementation
