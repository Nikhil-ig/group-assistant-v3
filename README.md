# V3 - Microservices Architecture

This is a **production-ready microservices architecture** where each module can be deployed independently on different servers while communicating through the **api_v2**.

## 🏗️ Architecture Overview

```
v3/
├── api_v2/          # Core API service (shared backend)
│   ├── app.py               # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   ├── db/                  # Database layer
│   ├── requirements.txt      # Dependencies
│   └── README.md            # Setup guide
│
├── bot/                      # Telegram bot service (independent deployment)
│   ├── main.py              # Bot entry point
│   ├── handlers/            # Command handlers
│   ├── middleware/          # Bot middleware
│   ├── client.py            # api_v2 client
│   ├── requirements.txt      # Dependencies
│   └── README.md            # Setup guide
│
├── web/                      # Web API service (independent deployment)
│   ├── app.py               # FastAPI application
│   ├── endpoints/           # API endpoints
│   ├── client.py            # api_v2 client
│   ├── dashboard/           # Web dashboard (future)
│   ├── requirements.txt      # Dependencies
│   └── README.md            # Setup guide
│
├── docker-compose.yml        # Local development setup
├── README.md                 # This file
└── ARCHITECTURE.md           # Detailed architecture docs
```

## 🎯 Key Principles

### 1. **Independence**
Each service can:
- Be deployed on different servers
- Be scaled independently
- Have its own database if needed
- Be developed and tested separately

### 2. **Centralized API**
The `api_v2` provides:
- Core business logic (RBAC, permissions, audit)
- Database connections
- Shared models and utilities
- Reusable services

### 3. **Communication**
Services communicate via:
- REST API calls to `api_v2`
- Async HTTP client (httpx)
- Event-driven pub/sub (optional, Redis)

## 📦 Service Descriptions

### api_v2 (Port 8000)
**Purpose:** Core backend with all business logic

**Responsibilities:**
- RBAC and permission management
- User and group management
- Audit logging
- Data persistence (MongoDB)
- Shared utilities and models

**Endpoints:**
- `/api/rbac/*` - RBAC operations
- `/api/users/*` - User management
- `/api/groups/*` - Group management
- `/api/audit/*` - Audit logging

**Can be deployed on:**
- Dedicated server
- Cloud (AWS, GCP, Azure)
- Docker container
- Kubernetes pod

---

### bot (Port 8001)
**Purpose:** Telegram bot with command handlers

**Responsibilities:**
- Handle Telegram updates
- Parse and execute bot commands
- Validate permissions via api_v2
- Forward moderation actions to api_v2
- Stream user interactions

**Key Files:**
- `main.py` - Bot initialization and polling
- `handlers/` - Command handlers
- `client.py` - HTTP client for api_v2 calls
- `middleware/` - Permission checking middleware

**Dependencies:**
- aiogram==3.0b7 (Telegram bot framework)
- httpx (async HTTP client)
- pydantic (data validation)

**Can be deployed on:**
- Dedicated server
- Different machine than api_v2
- Docker container
- Kubernetes pod

---

### web (Port 8002)
**Purpose:** Web API and future dashboard

**Responsibilities:**
- REST API for web clients
- Web dashboard (future)
- Real-time updates via WebSocket
- Admin panel for group management
- Statistics and analytics

**Key Files:**
- `app.py` - FastAPI application
- `endpoints/` - API route definitions
- `client.py` - HTTP client for api_v2 calls
- `dashboard/` - Frontend assets (future)

**Can be deployed on:**
- Dedicated server
- Different machine than api_v2
- Docker container
- Kubernetes pod

## 🚀 Deployment Scenarios

### Scenario 1: Single Machine (Development)
```
localhost:8002 - api_v2
localhost:8002 - bot
localhost:8002 - web
```

All services on same machine, communicate via localhost

### Scenario 2: Multiple Machines (Production)
```
Server 1: api_v2 (8000)
  ├── MongoDB
  └── Redis (optional)

Server 2: bot (8001)
  └── Connects to Server 1:8002

Server 3: web (8002)
  └── Connects to Server 1:8002

Server 4: nginx (load balancer)
  └── Routes requests to services
```

### Scenario 3: Kubernetes (Enterprise)
```
kubernetes/
├── api-v2-deployment.yaml
├── bot-deployment.yaml
├── web-deployment.yaml
├── services.yaml
└── configmap.yaml
```

Each service in its own pod(s), can be scaled independently

## 🔧 Quick Start (Development)

### 1. Start All Services with Docker Compose

```bash
cd v3
docker-compose up
```

This will start:
- api_v2 on port 8000
- bot on port 8001
- web on port 8002
- MongoDB
- Redis

### 2. Or Start Manually

```bash
# Terminal 1: api_v2
cd v3/api_v2
pip install -r requirements.txt
python app.py

# Terminal 2: bot
cd v3/bot
pip install -r requirements.txt
python main.py

# Terminal 3: web
cd v3/web
pip install -r requirements.txt
python app.py
```

### 3. Test the System

```bash
# Test api_v2
curl http://localhost:8002/api/health

# Test bot status
curl http://localhost:8002/status

# Test web API
curl http://localhost:8002/api/health
```

## 📡 Communication Flow

```
User Command
    ↓
Bot (port 8001)
    ├─ Parse command
    ├─ Validate input
    ├─ HTTP POST to api_v2 (8000)
    │   └─ Check permissions
    │   └─ Execute action
    │   └─ Log to audit
    │   └─ Return result
    └─ Send response to user

Web Dashboard
    ↓
Web API (port 8002)
    ├─ Receive HTTP request
    ├─ HTTP call to api_v2 (8000)
    │   └─ Fetch data
    │   └─ Check permissions
    │   └─ Return result
    └─ Send JSON response to client
```

## 🔐 Security

### Environment Variables
Each service has its own `.env` file:

```
# api_v2/.env
MONGODB_URL=mongodb://mongo:27017
DATABASE_NAME=bot_rbac
SECRET_KEY=your-secret-key
JWT_EXPIRATION=3600

# bot/.env
TELEGRAM_BOT_TOKEN=your-bot-token
API_V2_URL=http://api-v2:8002
API_V2_KEY=shared-api-key

# web/.env
API_V2_URL=http://api-v2:8002
API_V2_KEY=shared-api-key
JWT_SECRET=your-secret-key
```

### API Authentication
Services authenticate to api_v2 using:
- API keys (for bot and web)
- JWT tokens (for end users)
- Role-based access control (RBAC)

## 📊 Service Dependencies

```
bot (port 8001)
    └─ depends on → api_v2 (8000)
                      └─ MongoDB
                      └─ Redis (optional)

web (port 8002)
    └─ depends on → api_v2 (8000)
                      └─ MongoDB
                      └─ Redis (optional)

api_v2 (8000)
    └─ depends on → MongoDB
    └─ depends on → Redis (optional)
```

## 🎓 What Comes Next

### Phase 1 (Current)
✅ Microservices architecture
✅ api_v2 core
✅ bot service with RBAC
✅ web service basics

### Phase 2 (Next)
🔜 Beautiful web dashboard
   - React/Vue frontend
   - Real-time updates
   - Admin panel
   - Analytics

🔜 Enhanced bot
   - More commands
   - Auto-moderation
   - ML-based filtering

🔜 Monitoring & Logging
   - Prometheus metrics
   - ELK stack logging
   - Grafana dashboards

### Phase 3 (Future)
🔜 Horizontal scaling
🔜 Multi-region deployment
🔜 Advanced features (ML, webhooks)
🔜 Mobile app

## 📚 Documentation

- **README.md** (this file) - Overview
- **ARCHITECTURE.md** - Detailed architecture
- **api_v2/README.md** - API setup
- **bot/README.md** - Bot setup
- **web/README.md** - Web setup
- **DEPLOYMENT.md** - Production deployment

## 🧪 Testing

Each service has its own test suite:

```bash
# Test api_v2
cd v3/api_v2
pytest tests/

# Test bot
cd v3/bot
pytest tests/

# Test web
cd v3/web
pytest tests/

# Integration tests
cd v3
pytest tests/integration/
```

## ✨ Status

✅ **Architecture Ready**
- Microservices structure
- Independent deployments
- Centralized core
- Scalable design

🔜 **In Progress**
- Service implementations
- Docker configuration
- Testing framework

🔜 **Coming Soon**
- Beautiful web dashboard
- Advanced monitoring
- Production deployment

---

**Version:** 3.0.0 | **Status:** Architecture Phase | **Last Updated:** 2024
# new-test
