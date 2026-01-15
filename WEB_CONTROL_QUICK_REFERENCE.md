# Web Control API - Quick Reference

Quick copy-paste examples for common operations.

---

## 🚀 Quick Examples

### Parse User (Testing)

```bash
curl -X POST http://localhost:8000/api/web/parse-user \
  -H "Content-Type: application/json" \
  -d '{"user_input": "123456789"}'
```

### Ban User

```bash
curl -X POST http://localhost:8000/api/web/actions/ban \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "user_input": "123456789",
    "reason": "Spam",
    "initiated_by": 987654321
  }'
```

### Mute User (60 minutes)

```bash
curl -X POST http://localhost:8000/api/web/actions/mute \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "user_input": "@john_doe",
    "duration_minutes": 60,
    "reason": "Flooding",
    "initiated_by": 987654321
  }'
```

### Warn User

```bash
curl -X POST http://localhost:8000/api/web/actions/warn \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "user_input": "123456789",
    "reason": "Disrespectful",
    "initiated_by": 987654321
  }'
```

### Promote to Admin

```bash
curl -X POST http://localhost:8000/api/web/actions/promote \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "user_input": "123456789",
    "title": "Moderator",
    "initiated_by": 987654321
  }'
```

### Batch Ban 3 Users

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
        "action_type": "ban",
        "group_id": -1001234567890,
        "user_input": "222222",
        "reason": "Toxic",
        "initiated_by": 987654321
      },
      {
        "action_type": "ban",
        "group_id": -1001234567890,
        "user_input": "@user3",
        "reason": "Harassment",
        "initiated_by": 987654321
      }
    ]
  }'
```

### Get User History

```bash
curl "http://localhost:8000/api/web/actions/user-history?group_id=-1001234567890&user_input=123456789&limit=50"
```

### Get Group Stats

```bash
curl "http://localhost:8000/api/web/actions/group-stats?group_id=-1001234567890"
```

### Health Check

```bash
curl http://localhost:8000/api/web/health
```

### API Info

```bash
curl http://localhost:8000/api/web/info
```

---

## 🐍 Python Examples

### Ban User

```python
import requests

url = "http://localhost:8000/api/web/actions/ban"
payload = {
    "group_id": -1001234567890,
    "user_input": "123456789",
    "reason": "Spam",
    "initiated_by": 987654321
}

response = requests.post(url, json=payload)
result = response.json()
print(f"Success: {result['success']}")
print(f"Action ID: {result['action_id']}")
```

### Batch Operations

```python
import requests

url = "http://localhost:8000/api/web/actions/batch"
payload = {
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
}

response = requests.post(url, json=payload)
result = response.json()
print(f"Successful: {result['successful']}/{result['total']}")
```

### Get User History

```python
import requests

url = "http://localhost:8000/api/web/actions/user-history"
params = {
    "group_id": -1001234567890,
    "user_input": "123456789",
    "limit": 50
}

response = requests.get(url, params=params)
history = response.json()
print(f"Total actions: {history['total_actions']}")
for action in history['actions']:
    print(f"  - {action['action_type']}: {action['reason']}")
```

---

## 🟢 JavaScript/Node.js Examples

### Ban User

```javascript
const fetch = require('node-fetch');

async function banUser(groupId, userId, adminId, reason) {
  const response = await fetch('http://localhost:8000/api/web/actions/ban', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      group_id: groupId,
      user_input: String(userId),
      reason: reason,
      initiated_by: adminId,
    }),
  });

  const result = await response.json();
  return result;
}

// Usage
banUser(-1001234567890, 123456789, 987654321, 'Spam').then(result => {
  console.log(`Success: ${result.success}`);
  console.log(`Action ID: ${result.action_id}`);
});
```

### Batch Operations

```javascript
async function batchActions(actions) {
  const response = await fetch('http://localhost:8000/api/web/actions/batch', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ actions }),
  });

  return response.json();
}

// Usage
const actions = [
  {
    action_type: 'ban',
    group_id: -1001234567890,
    user_input: '111111',
    reason: 'Spam',
    initiated_by: 987654321,
  },
  {
    action_type: 'mute',
    group_id: -1001234567890,
    user_input: '222222',
    duration_minutes: 60,
    initiated_by: 987654321,
  },
];

batchActions(actions).then(result => {
  console.log(`${result.successful}/${result.total} successful`);
});
```

---

## 🔗 React Component Example

```jsx
import React, { useState } from 'react';

function BanUserForm() {
  const [groupId, setGroupId] = useState('');
  const [userId, setUserId] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleBan = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/web/actions/ban', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          group_id: parseInt(groupId),
          user_input: userId,
          reason: reason,
          initiated_by: 987654321, // Your admin ID
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        placeholder="Group ID"
        value={groupId}
        onChange={(e) => setGroupId(e.target.value)}
      />
      <input
        placeholder="User ID or @username"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
      />
      <textarea
        placeholder="Reason"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
      />
      <button onClick={handleBan} disabled={loading}>
        {loading ? 'Banning...' : 'Ban User'}
      </button>
      {result && (
        <div>
          {result.success ? (
            <p>✅ User banned! Action ID: {result.action_id}</p>
          ) : (
            <p>❌ Error: {result.error}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default BanUserForm;
```

---

## 📊 Common Response Formats

### Success Response
```json
{
  "success": true,
  "action_id": "507f1f77bcf86cd799439011",
  "user_id": 123456789,
  "username": null,
  "message": "User has been banned"
}
```

### Error Response
```json
{
  "detail": "Invalid user reference"
}
```

### Batch Response
```json
{
  "success": true,
  "total": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "index": 0,
      "success": true,
      "action_id": "507f...",
      "action_type": "ban"
    },
    {
      "index": 1,
      "success": true,
      "action_id": "507f...",
      "action_type": "mute"
    },
    {
      "index": 2,
      "success": true,
      "action_id": "507f...",
      "action_type": "warn"
    }
  ]
}
```

---

## 🔍 Available Actions

| Action | Endpoint | Required Fields |
|--------|----------|-----------------|
| Ban | `/actions/ban` | group_id, user_input, initiated_by |
| Kick | `/actions/kick` | group_id, user_input, initiated_by |
| Mute | `/actions/mute` | group_id, user_input, initiated_by |
| Unmute | `/actions/unmute` | group_id, user_input, initiated_by |
| Restrict | `/actions/restrict` | group_id, user_input, initiated_by |
| Unrestrict | `/actions/unrestrict` | group_id, user_input, initiated_by |
| Warn | `/actions/warn` | group_id, user_input, initiated_by |
| Promote | `/actions/promote` | group_id, user_input, initiated_by |
| Demote | `/actions/demote` | group_id, user_input, initiated_by |
| Unban | `/actions/unban` | group_id, user_input, initiated_by |

---

## 🧪 Testing Commands

### Health Check
```bash
curl http://localhost:8000/api/web/health | jq
```

### API Info
```bash
curl http://localhost:8000/api/web/info | jq
```

### Parse User
```bash
curl -X POST http://localhost:8000/api/web/parse-user \
  -H "Content-Type: application/json" \
  -d '{"user_input": "123456"}' | jq
```

### Ban with jq (pretty print)
```bash
curl -X POST http://localhost:8000/api/web/actions/ban \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "user_input": "123456789",
    "reason": "Test",
    "initiated_by": 987654321
  }' | jq '.success'
```

---

## 🚀 Integration Tips

1. **Always include initiated_by**: Required for audit logging
2. **Use numeric group_id**: Always negative (e.g., -1001234567890)
3. **User input format**: "123456" or "@username" both work
4. **Batch is faster**: Use batch for multiple users
5. **Check /health**: Always verify API is running first
6. **Error handling**: Check response.success before accessing data

---

## 🔐 Production Checklist

- [ ] Add API key authentication
- [ ] Enable rate limiting
- [ ] Use HTTPS only
- [ ] Monitor endpoint usage
- [ ] Log all API calls
- [ ] Set up alerting
- [ ] Regular backups
- [ ] Test error scenarios
- [ ] Document custom extensions

