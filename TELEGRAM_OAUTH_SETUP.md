# Telegram OAuth Integration Guide

## Setup Instructions

### Step 1: Create a Telegram Bot (if you don't have one)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the prompts to create a new bot
4. You'll receive a **Bot Token** (e.g., `123456789:ABCDefGhijKlmnOpqRsTuvWxyz...`)
5. Get your **Bot Username** (e.g., `my_admin_bot`)

### Step 2: Set Login Redirect

In BotFather:
1. Send `/mybots`
2. Select your bot
3. Go to **Bot Settings** → **Domain**
4. Set domain to your deployment URL (e.g., `localhost:5174` for dev, `yourdomain.com` for production)

### Step 3: Update Frontend

In `/web/frontend/index.html`, add the Telegram widget script:

```html
<script
    async
    src="https://telegram.org/js/telegram-widget.js?22"
    data-telegram-login="YOUR_BOT_USERNAME"
    data-size="large"
    data-userpic="true"
    data-onauth="onTelegramAuth(user)"
    data-request-access="write"
></script>

<script>
    function onTelegramAuth(user) {
        window.onTelegramAuth(user);
    }
</script>
```

Replace `YOUR_BOT_USERNAME` with your actual bot username.

### Step 4: Backend Endpoints

You need to implement these endpoints in your backend:

#### POST `/api/auth/telegram`

**Request:**
```json
{
  "telegram_id": 123456789,
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "photo_url": "https://t.me/...",
  "auth_date": 1705329600,
  "hash": "abc123..."
}
```

**Security Note**: Verify the hash signature to prevent spoofing:

```python
import hashlib
import hmac

def verify_telegram_auth(data: dict, bot_token: str) -> bool:
    """Verify Telegram authentication hash"""
    hash_value = data.pop('hash')
    data_check_string = '\n'.join(
        f'{k}={v}' for k, v in sorted(data.items())
    )
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    return computed_hash == hash_value
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "user": {
    "id": 123456789,
    "username": "johndoe",
    "email": "john@example.com",
    "role": "admin",
    "permissions": [...]
  }
}
```

#### Error Response:
```json
{
  "detail": "Invalid authentication hash"
}
```

### Step 5: Environment Variables

Add to your backend `.env`:
```
TELEGRAM_BOT_TOKEN=123456789:ABCDefGhijKlmnOpqRsTuvWxyz...
TELEGRAM_BOT_USERNAME=my_admin_bot
```

### Step 6: Frontend Login Flows

The login page now supports:

1. **Telegram OAuth** (top) - Click the widget to authenticate with Telegram
2. **Email/Password** (middle) - Traditional login
3. **Demo Login** (bottom) - Quick test account

## Testing

### Local Development
- URL: `http://localhost:5174`
- Make sure to set the Telegram bot domain to `localhost:5174`

### Production
- Replace `localhost:5174` with your actual domain
- Update bot domain in BotFather accordingly

## Frontend Code

The `Login.tsx` component includes:
- `handleTelegramAuth(user)` - Processes Telegram authentication
- `handleLogin()` - Email/password authentication
- `handleDemoLogin()` - Demo account for testing

All three methods set the auth token and redirect to dashboard.

## Troubleshooting

**"Telegram widget not showing?"**
- Check bot username is correct
- Verify bot domain matches current URL
- Clear browser cache

**"Login failed after clicking?"**
- Check backend `/api/auth/telegram` endpoint exists
- Verify JWT token is being returned
- Check browser console for errors

**"Hash verification failed?"**
- Ensure `TELEGRAM_BOT_TOKEN` env variable is set correctly
- Verify hash calculation matches Telegram's algorithm
- Check timestamp is recent (not too old)

## References

- [Telegram Widgets](https://core.telegram.org/widgets/login)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [BotFather](https://t.me/botfather)
