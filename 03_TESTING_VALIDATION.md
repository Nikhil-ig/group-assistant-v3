# 🧪 TESTING & VALIDATION GUIDE

**Status:** ✅ **READY TO TEST**  
**Testing Strategy:** Progressive validation of all new modes  

---

## 🔍 DELETE MODE TESTS

### Test 1: Regex Delete
```bash
# Test command in bot
/del regex "^Error"

# Test via API
curl -X POST http://localhost:8002/api/v2/groups/12345/messages/delete-regex \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "^Error",
    "admin_id": 123,
    "scan_limit": 100,
    "case_sensitive": false
  }'

# Expected response:
# {"success": true, "deleted_count": N, "pattern": "^Error"}
```

### Test 2: Duplicate Delete
```bash
# Test command
/del duplicates

# Test via API
curl -X POST http://localhost:8002/api/v2/groups/12345/messages/delete-duplicates \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "admin_id": 123,
    "user_id": null,
    "scan_limit": 200
  }'
```

### Test 3: Inactive User Delete
```bash
# Test command (delete messages from users inactive 30+ days)
/del inactive 30

# Test via API
curl -X POST http://localhost:8002/api/v2/groups/12345/messages/delete-inactive-users \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "admin_id": 123,
    "days": 30
  }'
```

### Test 4: Profanity Delete
```bash
# Test command (severity: low/medium/high)
/del profanity high

# Test via API
curl -X POST http://localhost:8002/api/v2/groups/12345/messages/delete-profanity \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "admin_id": 123,
    "severity": "high",
    "custom_words": []
  }'
```

### Test 5: Emoji Spam Delete
```bash
# Test command
/del emoji-spam

# Test via API (min_emoji_count default: 3)
curl -X POST http://localhost:8002/api/v2/groups/12345/messages/delete-emoji-spam \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "admin_id": 123,
    "min_emoji_count": 3
  }'
```

### Test 6: Long Message Delete
```bash
# Test command (delete messages >500 chars)
/del long 500

# Test via API
curl -X POST http://localhost:8002/api/v2/groups/12345/messages/delete-long \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "admin_id": 123,
    "char_limit": 500
  }'
```

---

## 📊 ANALYTICS TESTS

### Test 1: Message Velocity
```bash
# Get message velocity (messages per 5-minute interval)
curl -X GET "http://localhost:8002/api/v2/groups/12345/analytics/message-velocity?interval_minutes=5" \
  -H "Authorization: Bearer YOUR_API_TOKEN"

# Expected response:
# {
#   "success": true,
#   "group_id": 12345,
#   "average_per_interval": 4.2,
#   "peak": 10,
#   "low": 0,
#   "intervals": {...}
# }
```

### Test 2: User Activity
```bash
# Get top 10 most active users
curl -X GET "http://localhost:8002/api/v2/groups/12345/analytics/user-activity?limit=10" \
  -H "Authorization: Bearer YOUR_API_TOKEN"

# Expected response:
# {
#   "success": true,
#   "group_id": 12345,
#   "top_users": [
#     {"user_id": 123, "messages": 45},
#     {"user_id": 456, "messages": 32}
#   ],
#   "total_messages": 200,
#   "unique_users": 15,
#   "average_per_user": 13.3
# }
```

---

## ✅ VERIFICATION CHECKLIST

### Phase 1: Endpoint Existence
- [ ] Regex delete endpoint responds (200)
- [ ] Duplicate delete endpoint responds (200)
- [ ] Inactive user delete endpoint responds (200)
- [ ] Profanity delete endpoint responds (200)
- [ ] Emoji spam delete endpoint responds (200)
- [ ] Long message delete endpoint responds (200)
- [ ] Message velocity analytics endpoint responds (200)
- [ ] User activity analytics endpoint responds (200)

### Phase 2: Data Validation
- [ ] Regex endpoint accepts valid regex patterns
- [ ] Inactive user endpoint validates day range (1-365)
- [ ] Profanity endpoint accepts severity levels
- [ ] Emoji spam endpoint counts correctly
- [ ] Long message endpoint filters by character count
- [ ] Analytics endpoints return proper data structures

### Phase 3: Error Handling
- [ ] Invalid regex pattern returns 400 error
- [ ] Missing admin_id returns 400 error
- [ ] Database errors return 500 error
- [ ] Malformed JSON returns 400 error

### Phase 4: Integration
- [ ] Bot command `/del regex` triggers API call
- [ ] Bot command `/del duplicates` triggers API call
- [ ] Bot command `/del inactive` triggers API call
- [ ] Bot command `/del profanity` triggers API call
- [ ] Bot command `/del emoji-spam` triggers API call
- [ ] Bot command `/del long` triggers API call

### Phase 5: MongoDB Logging
- [ ] Deleted messages logged to `deleted_messages` collection
- [ ] Actions logged to `action_history` collection
- [ ] Timestamps recorded correctly
- [ ] Admin IDs recorded correctly

---

## 🐛 DEBUG COMMANDS

### Check API health
```bash
curl http://localhost:8002/health
```

### List all delete operations
```bash
curl http://localhost:8002/api/v2/groups/12345/messages/deleted \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

### Check MongoDB connection
```python
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client.telegram_bot
print(db.deleted_messages.find().count())
```

### View logs
```bash
tail -f logs/bot.log
tail -f logs/api_v2.log
```

---

## 🚨 TROUBLESHOOTING

### Issue: "Endpoint not found" (404)
- **Solution:** Verify code was pasted correctly
- Check indentation matches existing code
- Restart API: `pkill -f uvicorn && cd api_v2 && uvicorn app:app --port 8002 &`

### Issue: "Authentication failed"
- **Solution:** Verify API token in headers
- Check `API_V2_TOKEN` environment variable
- Compare with token in `.env` file

### Issue: "Empty results"
- **Solution:** Ensure test group has message history
- Send test messages first: `/test 10` (send 10 messages)
- Check MongoDB has data: `db.action_history.find()`

### Issue: "Regex pattern invalid"
- **Solution:** Use raw strings in curl: `"pattern": "^Error"`
- Test regex in Python first:
  ```python
  import re
  pattern = "^Error"
  re.compile(pattern)  # Should not raise
  ```

---

## 📈 PERFORMANCE BENCHMARKS

**Expected Performance (on normal hardware):**

| Operation | Time | Notes |
|-----------|------|-------|
| Regex delete (100 scans) | 250ms | Depends on pattern complexity |
| Duplicate delete (200 scans) | 150ms | Fast hashing |
| Inactive delete (all messages) | 500ms | Full scan required |
| Profanity delete (200 scans) | 200ms | Word list matching |
| Emoji spam delete (100 scans) | 100ms | Regex matching |
| Long message delete (200 scans) | 50ms | Simple length check |
| Message velocity | 1000ms | 24 interval lookups |
| User activity | 500ms | Aggregation required |

---

## 🎯 NEXT STEPS

1. **Complete Implementation** (Use 02_IMPLEMENTATION_GUIDE.md)
2. **Run Phase 1 Tests** (Endpoint existence checks)
3. **Run Phase 2 Tests** (Data validation)
4. **Run Phase 3 Tests** (Error handling)
5. **Run Phase 4 Tests** (Integration with bot)
6. **Run Phase 5 Tests** (Database logging)
7. **Performance Profiling** (Benchmark operations)
8. **Deploy to Production** (When all tests pass)

