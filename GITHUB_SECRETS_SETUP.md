# GitHub Secrets Setup Guide

For the CI/CD pipeline to work, configure these secrets in your GitHub repository.

## Required Secrets

Go to: **Settings → Secrets and variables → Actions**

Click **"New repository secret"** and add each:

### Essential Secrets (Required)

1. **TELEGRAM_TOKEN**
   - Get from: @BotFather on Telegram
   - Format: `8366781443:AAHIXgGD1UXvPWw9EIDBlMk5Ktuhj2qQ8WU`
   - Purpose: Bot authentication

2. **MONGODB_URL**
   - Format: `mongodb://admin:password@host:27017/telegram_bot?authSource=admin`
   - For local/Docker: `mongodb://admin:changeme@mongodb:27017/telegram_bot?authSource=admin`
   - For production: Your actual MongoDB connection string
   - Purpose: Database connection

3. **JWT_SECRET**
   - Generate: `openssl rand -hex 32`
   - Example: `5a3c9f8e2b1d4a6f7c9e1b3a5d7f9e1b3a5c7d9e1f3a5b7c9d1e3f5a7b9c1`
   - Purpose: API token signing

4. **SERVER_HOST**
   - Your server IP or domain: `123.45.67.89` or `your-domain.com`
   - Purpose: SSH deployment target

5. **SERVER_USER**
   - SSH username: Usually `ubuntu`, `root`, or custom user
   - Purpose: SSH login

6. **SERVER_SSH_KEY**
   - Generate on server: `ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -N ""`
   - Then: `cat ~/.ssh/deploy_key` (copy entire output)
   - **Important**: Include `-----BEGIN` and `-----END` lines
   - Purpose: SSH authentication key

7. **SERVER_PORT**
   - SSH port: Usually `22`
   - Purpose: SSH connection port

### Optional Secrets

8. **SLACK_WEBHOOK_URL** (Optional - for deployment notifications)
   - Get from: Slack workspace → Apps → Incoming Webhooks
   - Format: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
   - Purpose: Send deployment status to Slack

## Verification Checklist

- [ ] TELEGRAM_TOKEN is set and not empty
- [ ] MONGODB_URL has proper connection string
- [ ] JWT_SECRET is 64+ characters (hex string)
- [ ] SERVER_HOST is IP or domain
- [ ] SERVER_USER exists on the server
- [ ] SERVER_SSH_KEY includes BEGIN/END lines
- [ ] SERVER_PORT is correct (usually 22)
- [ ] SLACK_WEBHOOK_URL is valid (optional)

## Test SSH Connection

Before deploying, verify SSH key works:

```bash
# On your local machine, test SSH to server
ssh -i ~/.ssh/deploy_key <SERVER_USER>@<SERVER_HOST> -p <SERVER_PORT> echo "Connected!"
```

Expected output: `Connected!`

## GitHub Actions Testing

After adding secrets:

1. Push code to `main` branch
2. Go to **Actions** tab
3. Watch workflow run through: test → lint → security → build
4. Verify all pass (deploy only runs on `production` branch)

## Troubleshooting

### Deployment fails with "SSH permission denied"
- Verify SERVER_SSH_KEY includes all lines (-----BEGIN to -----END)
- Check server public key: `cat ~/.ssh/authorized_keys`

### Database connection fails
- Test locally: `docker-compose up` with correct .env values
- Verify MONGODB_URL is reachable from deployment server

### Slack notifications not working
- SLACK_WEBHOOK_URL is optional (deployment won't fail without it)
- If you want notifications, generate a webhook in Slack first

## Production Security Notes

✅ All secrets are encrypted by GitHub  
✅ Secrets never appear in logs  
✅ Secrets only accessible to Actions jobs  
✅ Use unique secrets per environment if needed  
✅ Rotate TELEGRAM_TOKEN if compromised  

---

**Status**: Ready for deployment once all 7 required secrets are set
