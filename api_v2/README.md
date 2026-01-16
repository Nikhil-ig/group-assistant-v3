"""
API V2 - Professional & Scalable Data Management System
Usage Guide & Quick Start
"""

# 📚 API V2 DOCUMENTATION

## 🚀 Overview

API V2 is a **professional-grade, high-performance data management system** designed for enterprise-scale Telegram bot operations.

### Key Features:
- ✅ **Multi-Group Support** - Handle unlimited groups with isolated settings
- ✅ **Role Management** - Create custom roles with fine-grained permissions
- ✅ **Advanced Rules** - Define group rules with automatic penalties
- ✅ **Flexible Settings** - Per-group configuration and customization
- ✅ **Performance Optimized** - Redis caching, connection pooling, aggregation pipelines
- ✅ **Type Safe** - Full Pydantic validation on all endpoints
- ✅ **Scalable** - Designed for multi-server deployments

---

## 📁 Project Structure

```
api_v2/
├── core/                    # Core infrastructure
│   ├── database.py         # Advanced MongoDB manager
│   └── __init__.py
├── models/                 # Data models
│   ├── schemas.py          # Pydantic schemas
│   └── __init__.py
├── services/               # Business logic
│   ├── business_logic.py   # All services (groups, roles, rules, settings, actions)
│   └── __init__.py
├── routes/                 # API endpoints
│   ├── api_v2.py          # All routes
│   └── __init__.py
├── cache/                  # Caching layer
│   ├── manager.py         # Redis + in-memory cache
│   └── __init__.py
├── telegram/              # Telegram integration
│   ├── api.py            # Telegram API wrapper
│   └── __init__.py
├── utils/                 # Utilities
│   └── __init__.py
├── __init__.py
└── README.md
```

---

## 🔌 Integration with Existing Code

### Step 1: Update requirements.txt

```bash
# Add these dependencies
motor>=3.1.1              # Async MongoDB driver
redis>=4.5.0              # Redis client
pydantic>=2.0             # Data validation
aioredis>=2.0             # Async Redis
```

### Step 2: Initialize API V2 in your FastAPI app

```python
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from api_v2.core.database import init_db_manager
from api_v2.cache import init_cache_manager
from api_v2.routes.api_v2 import router as api_v2_router

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Initialize database
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["bot_manager"]
    await init_db_manager(db)
    
    # Initialize cache
    await init_cache_manager("redis://localhost:6379")
    
    # Include router
    app.include_router(api_v2_router)

@app.on_event("shutdown")
async def shutdown():
    from api_v2.core.database import close_db_manager
    from api_v2.cache import close_cache_manager
    
    await close_db_manager()
    await close_cache_manager()
```

---

## 📡 API Endpoints

### Health Check
```bash
GET /api/v2/health
```

### Groups
```bash
# Create group
POST /api/v2/groups
{
    "group_id": -1001234567890,
    "name": "My Group",
    "member_count": 100
}

# Get group
GET /api/v2/groups/{group_id}

# Update group
PUT /api/v2/groups/{group_id}
{
    "member_count": 105
}

# Get group statistics
GET /api/v2/groups/{group_id}/stats
```

### Roles
```bash
# Create role
POST /api/v2/groups/{group_id}/roles
{
    "name": "Moderator",
    "priority": 10,
    "permissions": ["ban", "mute", "warn"]
}

# Get all roles
GET /api/v2/groups/{group_id}/roles

# Get specific role
GET /api/v2/groups/{group_id}/roles/{role_name}
```

### Rules
```bash
# Create rule
POST /api/v2/groups/{group_id}/rules
{
    "rule_name": "No Spam",
    "description": "Spam is not allowed",
    "penalty": "warn"
}

# Get all rules
GET /api/v2/groups/{group_id}/rules?active_only=true
```

### Settings
```bash
# Get settings
GET /api/v2/groups/{group_id}/settings

# Update settings
PUT /api/v2/groups/{group_id}/settings
{
    "welcome_message_enabled": true,
    "welcome_message": "Welcome to the group!",
    "logging_enabled": true
}
```

### Actions
```bash
# Log action
POST /api/v2/groups/{group_id}/actions
{
    "user_id": 123456,
    "action_type": "warn",
    "reason": "Spam"
}

# Get actions
GET /api/v2/groups/{group_id}/actions?page=1&per_page=50

# Get user statistics
GET /api/v2/groups/{group_id}/users/{user_id}/stats
```

---

## 🔧 Usage Examples

### Python
```python
import httpx
import asyncio

async def example():
    async with httpx.AsyncClient() as client:
        # Create group
        response = await client.post(
            "http://localhost:8000/api/v2/groups",
            json={
                "group_id": -1001234567890,
                "name": "My Group",
                "member_count": 100
            }
        )
        print(response.json())
        
        # Create role
        response = await client.post(
            "http://localhost:8000/api/v2/groups/-1001234567890/roles",
            json={
                "name": "Moderator",
                "priority": 10,
                "permissions": ["ban", "mute"]
            }
        )
        print(response.json())

asyncio.run(example())
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function example() {
    // Create group
    const groupResponse = await axios.post(
        'http://localhost:8000/api/v2/groups',
        {
            group_id: -1001234567890,
            name: 'My Group',
            member_count: 100
        }
    );
    console.log(groupResponse.data);
    
    // Create role
    const roleResponse = await axios.post(
        'http://localhost:8000/api/v2/groups/-1001234567890/roles',
        {
            name: 'Moderator',
            priority: 10,
            permissions: ['ban', 'mute']
        }
    );
    console.log(roleResponse.data);
}

example();
```

### cURL
```bash
# Create group
curl -X POST http://localhost:8000/api/v2/groups \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "name": "My Group",
    "member_count": 100
  }'

# Create role
curl -X POST http://localhost:8000/api/v2/groups/-1001234567890/roles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Moderator",
    "priority": 10,
    "permissions": ["ban", "mute"]
  }'
```

---

## ⚡ Performance Optimizations

### Connection Pooling
- Max pool size: 50 connections
- Min pool size: 10 connections
- Timeout: 5 seconds

### Caching Strategy
- **Group data**: 1 hour TTL
- **User data**: 30 minutes TTL
- **Settings**: 1 hour TTL
- **Roles**: 1 hour TTL

### Database Indexes
Optimized indexes on all frequently queried fields:
- `groups`: group_id (unique), active status, timestamps
- `users`: group_id + user_id (unique), role, active status
- `roles`: group_id + name (unique), permissions
- `rules`: group_id + rule_name (unique), active status
- `actions`: group_id + timestamp, user_id + timestamp
- `logs`: TTL index (30 days auto-delete)

---

## 🔐 Security Features

- ✅ Input validation with Pydantic
- ✅ Type checking on all endpoints
- ✅ Error handling and logging
- ✅ Database connection pooling
- ✅ Transaction support for critical operations

---

## 📊 Scaling Considerations

### Database
- Use MongoDB replica sets for high availability
- Enable sharding for multi-group deployments
- Monitor index performance

### Cache
- Use Redis cluster for distributed caching
- Monitor cache hit rates
- Implement cache warming strategies

### Application
- Use async/await throughout
- Deploy multiple instances behind load balancer
- Monitor performance metrics

---

## 🚀 Deployment

### Local Development
```bash
# Start MongoDB
mongod --port 27017 --dbpath ./data/mongodb

# Start Redis
redis-server --port 6379

# Install dependencies
pip install -r requirements.txt

# Run API
python -m uvicorn api_v2.app:app --reload --port 8000
```

### Production
```bash
# Use Gunicorn + Uvicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_v2.app:app

# Or use Docker
docker build -t api-v2 .
docker run -p 8000:8000 api-v2
```

---

## 📞 Support & Documentation

- API Docs: http://localhost:8000/docs
- Swagger UI: http://localhost:8000/swagger
- Health Check: http://localhost:8000/api/v2/health
