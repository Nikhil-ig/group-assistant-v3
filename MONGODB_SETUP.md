# MongoDB Setup & Configuration Guide

## Quick Fix for Your System ✅

Your MongoDB is running but on **port 27018** (not the default 27017).

### Update Your .env File

```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
cp .env.example .env
nano .env
```

**Change this line:**
```
MONGODB_URI=mongodb://localhost:27017
```

**To this:**
```
MONGODB_URI=mongodb://localhost:27018
```

Then add your Telegram configuration:
```
TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE
SUPERADMIN_ID=YOUR_ID_HERE
SUPERADMIN_USERNAME=your_username
```

---

## MongoDB Port Configuration

### Current Setup (macOS Homebrew)
```
Configuration: /usr/local/etc/mongod.conf
Port: 27018 (custom, not default)
Data: /usr/local/var/mongodb/
Logs: /usr/local/var/log/mongodb/
```

### Option 1: Use Current Port (27018) - Easiest ✅

Just update `.env`:
```
MONGODB_URI=mongodb://localhost:27018
```

Then run the bot:
```bash
python -m v3.main
```

---

### Option 2: Change MongoDB Back to Default Port (27017)

Edit MongoDB configuration:
```bash
sudo nano /usr/local/etc/mongod.conf
```

Find the `net:` section and change:
```yaml
net:
  bindIp: 127.0.0.1, ::1
  port: 27017      # Change from 27018 to 27017
```

Save and restart MongoDB:
```bash
brew services restart mongodb-community
```

Then use default in .env:
```
MONGODB_URI=mongodb://localhost:27017
```

---

### Option 3: Use MongoDB Atlas (Cloud) - Recommended for Production

1. Visit https://cloud.mongodb.com
2. Create free account
3. Create cluster
4. Get connection string like:
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

5. Update .env:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

---

## Verify MongoDB is Working

### Check Service Status
```bash
brew services list | grep mongodb
```

Should show:
```
mongodb-community started
```

### Check MongoDB is Listening

For port 27018:
```bash
lsof -i :27018
```

For port 27017:
```bash
lsof -i :27017
```

### Test Connection

Using mongosh (MongoDB shell):
```bash
mongosh --port 27018
```

Or for default port:
```bash
mongosh --port 27017
```

Should show:
```
test>
```

Then exit:
```bash
exit
```

---

## Troubleshooting MongoDB Issues

### MongoDB Not Starting

Check logs:
```bash
tail -50 /usr/local/var/log/mongodb/mongo.log
```

If logs show errors, try:
```bash
brew services restart mongodb-community
```

Or start in foreground to see errors:
```bash
mongod --config /usr/local/etc/mongod.conf
```

### Connection Refused Error

**Most common cause:** Wrong port in .env

Check which port MongoDB is using:
```bash
cat /usr/local/etc/mongod.conf | grep port
```

Update .env to match that port.

### Port Already in Use

If port 27018 is in use, change in mongod.conf:
```bash
sudo nano /usr/local/etc/mongod.conf
```

Change port to something free (e.g., 27019):
```yaml
net:
  port: 27019
```

Restart:
```bash
brew services restart mongodb-community
```

Then update .env:
```
MONGODB_URI=mongodb://localhost:27019
```

---

## Your Current Configuration

```
📍 MongoDB Status: RUNNING ✅
📍 Port: 27018
📍 Data Directory: /usr/local/var/mongodb/
📍 Config: /usr/local/etc/mongod.conf
📍 Logs: /usr/local/var/log/mongodb/mongo.log
```

### What You Need to Do Now

1. **Update .env** with correct port:
   ```bash
   MONGODB_URI=mongodb://localhost:27018
   ```

2. **Add Telegram Configuration**:
   ```bash
   TELEGRAM_BOT_TOKEN=YOUR_TOKEN
   SUPERADMIN_ID=YOUR_ID
   SUPERADMIN_USERNAME=your_username
   ```

3. **Run the bot**:
   ```bash
   cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2"
   python -m v3.main
   ```

---

## Database Initialization

When your bot connects to MongoDB for the first time, it will:

1. ✅ Create database: `telegram_bot_v3`
2. ✅ Create collections:
   - `groups` - Store group info
   - `admins` - Store admin permissions
   - `audit_logs` - Store all actions
   - `metrics` - Store statistics
3. ✅ Create indexes for performance

All automatic - no manual setup needed!

---

## MongoDB Data Location

Your data is stored here:
```
/usr/local/var/mongodb/
```

### Backup MongoDB Data

```bash
# Create backup
mongodump --port 27018 --out ~/backup/mongodb_backup

# Restore from backup
mongorestore --port 27018 ~/backup/mongodb_backup
```

### Export Data to JSON

```bash
# Export audit logs
mongoexport --port 27018 -d telegram_bot_v3 -c audit_logs -o audit_logs.json
```

---

## MongoDB Commands

### Connect to Database

```bash
mongosh --port 27018
```

### View Databases

```bash
show databases
```

### Use Your Bot Database

```bash
use telegram_bot_v3
```

### View Collections

```bash
show collections
```

### View Sample Data

```bash
# Recent audit logs
db.audit_logs.find().limit(5)

# All groups
db.groups.find()

# All admins
db.admins.find()

# Group metrics
db.metrics.find()
```

### Exit MongoDB

```bash
exit
```

---

## Performance Optimization

MongoDB has automatic indexes created for your collections. They're optimized for:

- Fast user lookups
- Fast group queries
- Quick audit log searches
- Efficient metrics aggregation

No manual optimization needed!

---

## Production Considerations

### Before Going Live

1. **Use MongoDB Atlas** instead of local
2. **Enable authentication** in mongod.conf
3. **Configure backup** strategy
4. **Monitor** performance
5. **Scale** as needed

### Security

For local development:
- Current setup is fine

For production:
- Use MongoDB Atlas with auth
- Use VPN/private network
- Enable SSL/TLS
- Regular backups

---

## Get Help

Check MongoDB logs:
```bash
tail -100 /usr/local/var/log/mongodb/mongo.log | grep -i error
```

Check bot connection logs:
```bash
# Look for MongoDB connection messages in bot output
```

---

## Summary

✅ **Your MongoDB is running on port 27018**

Just update `.env` and you're ready to go:

```bash
# In .env file:
MONGODB_URI=mongodb://localhost:27018
TELEGRAM_BOT_TOKEN=YOUR_TOKEN
SUPERADMIN_ID=YOUR_ID
SUPERADMIN_USERNAME=your_username
```

Then run:
```bash
python -m v3.main
```

That's it! 🚀

---

**Last Updated:** December 30, 2025
**Platform:** macOS with Homebrew
