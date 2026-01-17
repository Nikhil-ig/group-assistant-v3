# Web Control API - Integration Guide

Quick setup guide to integrate the web control API into your centralized API.

---

## 📋 Integration Steps

### Step 1: Import the Web Router

In `centralized_api/app.py`, add the import:

```python
from centralized_api.api.web_control import web_router, set_database
```

### Step 2: Register the Router

In your FastAPI app initialization:

```python
app = FastAPI()

# ... other setup ...

# Register web control router
app.include_router(web_router)
```

### Step 3: Initialize Web Control Module

In app startup event:

```python
@app.on_event("startup")
async def startup_event():
    # ... existing startup code ...
    
    # Initialize web control API
    from centralized_api.db import ActionDatabase
    db = ActionDatabase()
    set_database(db)
```

### Step 4: Verify Integration

Test the integration:

```bash
# Health check
curl http://localhost:8000/api/web/health

# API info
curl http://localhost:8000/api/web/info

# Parse user endpoint
curl -X POST http://localhost:8000/api/web/parse-user \
  -H "Content-Type: application/json" \
  -d '{"user_input": "123456"}'
```

---

## 📁 File Structure

```
centralized_api/
├── api/
│   ├── __init__.py
│   ├── routes.py              (existing)
│   ├── web_control.py         (NEW)
│   ├── advanced_rbac_routes.py
│   └── simple_actions.py
├── models/
│   ├── __init__.py
│   ├── action_types.py
│   └── advanced_rbac.py
├── services/
│   ├── __init__.py
│   └── executor.py
├── db/
│   ├── __init__.py
│   └── mongodb.py
├── app.py                      (UPDATE)
└── config.py
```

---

## 🔌 API Endpoints Available

### Utility
- `POST /api/web/parse-user` - Parse user reference

### Actions (All POST)
- `/api/web/actions/ban` - Ban user
- `/api/web/actions/kick` - Kick user
- `/api/web/actions/mute` - Mute user
- `/api/web/actions/unmute` - Unmute user
- `/api/web/actions/restrict` - Restrict permissions
- `/api/web/actions/unrestrict` - Restore permissions
- `/api/web/actions/warn` - Warn user
- `/api/web/actions/promote` - Promote to admin
- `/api/web/actions/demote` - Demote from admin
- `/api/web/actions/unban` - Unban user
- `/api/web/actions/batch` - Batch execute

### Queries (All GET)
- `/api/web/actions/user-history` - User action history
- `/api/web/actions/group-stats` - Group statistics
- `/api/web/actions/status/{action_id}` - Action status
- `/api/web/groups/list` - List all groups

### System
- `GET /api/web/health` - Health check
- `GET /api/web/info` - API documentation

---

## 🧪 Test Cases

### 1. Health Check
```bash
curl http://localhost:8000/api/web/health
```
Expected: `200 OK` with healthy status

### 2. Parse User (Numeric)
```bash
curl -X POST http://localhost:8000/api/web/parse-user \
  -H "Content-Type: application/json" \
  -d '{"user_input": "123456789"}'
```
Expected: `type: "numeric"`, `user_id: 123456789`

### 3. Parse User (Username)
```bash
curl -X POST http://localhost:8000/api/web/parse-user \
  -H "Content-Type: application/json" \
  -d '{"user_input": "@john_doe"}'
```
Expected: `type: "username"`, `username: "@john_doe"`

### 4. Ban User
```bash
curl -X POST http://localhost:8000/api/web/actions/ban \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "user_input": "123456789",
    "reason": "Test ban",
    "initiated_by": 987654321
  }'
```
Expected: `200 OK` with success: true, action_id

### 5. Batch Actions
```bash
curl -X POST http://localhost:8000/api/web/actions/batch \
  -H "Content-Type: application/json" \
  -d '{
    "actions": [
      {
        "action_type": "ban",
        "group_id": -1001234567890,
        "user_input": "111111",
        "reason": "Spam",
        "initiated_by": 987654321
      },
      {
        "action_type": "mute",
        "group_id": -1001234567890,
        "user_input": "222222",
        "duration_minutes": 60,
        "initiated_by": 987654321
      }
    ]
  }'
```
Expected: `200 OK` with results array

---

## 🔐 Security Recommendations

### For Production:
1. Add API key authentication
2. Implement rate limiting
3. Add CORS configuration
4. Use HTTPS only
5. Add request validation
6. Log all API calls
7. Implement request signing

### Example Authentication:

```python
from fastapi import Depends, HTTPException, Header

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("WEB_API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

# Use in endpoints:
@web_router.post("/actions/ban")
async def web_ban(
    request_data: dict = Body(...),
    api_key: str = Depends(verify_api_key)
):
    # ... endpoint code ...
```

---

## 📊 Monitoring & Logging

### View API Logs
```bash
# Docker
docker logs -f centralized_api

# Or with grep to filter
docker logs centralized_api | grep "web_control"
```

### Enable Debug Logging
In `centralized_api/config.py`:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

---

## 🚀 Deployment

### Docker Compose Example

```yaml
version: '3.8'

services:
  centralized_api:
    build: ./centralized_api
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017
      - MONGODB_DATABASE=bot_actions
      - LOG_LEVEL=INFO
    depends_on:
      - mongo
    volumes:
      - ./centralized_api:/app
    command: uvicorn centralized_api.app:app --host 0.0.0.0 --port 8000 --reload

  mongo:
    image: mongo:5.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

---

## 🐛 Troubleshooting

### Issue: `Module not found: web_control`

**Solution:**
1. Verify file exists: `centralized_api/api/web_control.py`
2. Check `__init__.py` imports
3. Restart Python process

### Issue: Database not initialized

**Solution:**
```python
# In startup event, ensure:
from centralized_api.db import ActionDatabase
db = ActionDatabase()
set_database(db)
```

### Issue: Parse user returns invalid

**Solution:**
- Check user_input format
- Valid: "123456", "@username", "username"
- Invalid: "", " ", "user@example.com"

### Issue: Action returns 500 error

**Solution:**
1. Check MongoDB connection: `mongosh mongodb://localhost:27017`
2. Verify database and collections exist
3. Check logs: `docker logs centralized_api`

---

## 📖 Additional Resources

- **Main Documentation:** `WEB_CONTROL_API.md`
- **API Architecture:** `ARCHITECTURE.md`
- **Permission Checking:** `PERMISSION_CHECKING_IN_API.md`
- **Duplicate Prevention:** `API_DUPLICATE_PREVENTION.md`

---

## ✅ Integration Checklist

- [ ] Web control module created (`web_control.py`)
- [ ] Router imported in `app.py`
- [ ] Router registered in FastAPI
- [ ] Database initialized in startup
- [ ] Health check working
- [ ] Parse user endpoint working
- [ ] Ban endpoint tested
- [ ] Batch endpoint tested
- [ ] Query endpoints tested
- [ ] Error handling verified
- [ ] Logging configured
- [ ] Docker compose updated (if needed)
- [ ] Documentation reviewed
- [ ] Ready for deployment

---

## 🎯 Next Steps

1. **Test all endpoints** using provided curl commands
2. **Integrate with frontend** web dashboard
3. **Add authentication** for production
4. **Set up monitoring** and alerting
5. **Deploy to VPS** using provided scripts
6. **Monitor logs** for issues

---

## 📞 Support

For issues:
1. Check `/api/web/health` endpoint
2. Review MongoDB logs
3. Check application logs
4. Verify all imports and registrations
5. Test individual endpoints with curl

