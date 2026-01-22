# 🔓 /FREE Command - Quick Reference

## 📌 At a Glance

The **`/free`** command is your all-in-one **content restriction & behavior management tool**.

---

## ⚡ Quick Start

```bash
/free @username          # Manage user permissions
/free 123456789         # By user ID  
Reply + /free           # Target message author
```

---

## 📋 Content Permissions (Auto-Delete)

| Button | Blocks | Auto-Delete |
|--------|--------|-------------|
| 📝 Text | Text messages | ✅ Yes |
| 🎨 Stickers | Sticker images | ✅ Yes |
| 🎬 GIFs | Animated GIFs | ✅ Yes |
| 📸 Media | Photos, videos, docs, audio | ✅ Yes |
| 🎤 Voice | Voice messages, video notes | ✅ Yes |
| 🔗 Links | URLs and web previews | ✅ Yes |

---

## 🚨 Behavior Filters (Group-Level)

| Filter | What It Does | Threshold |
|--------|--------------|-----------|
| 🌊 Floods | Delete spam floods | >4 msgs/5s |
| 📨 Spam | Delete link/mention spam | 3+ links |
| ✅ Checks | Require verification | All new users |
| 🌙 Silence | Night mode enforcement | Scheduled hours |

---

## 🎛️ Actions

| Button | Effect |
|--------|--------|
| ↻ Reset All | Restore ALL permissions to allowed |
| ❌ Close | Close the menu |
| 🌃 Night Mode | Toggle user's night mode exemption |

---

## 📊 Status Indicators

| Icon | Meaning |
|------|---------|
| ✅ | ALLOWED / ENABLED |
| ❌ | BLOCKED / DISABLED |
| 🌙 ACTIVE | Night mode is running |
| 🎖️ Exempt by role | User's role exempts from night mode |
| ⭐ Personally exempt | User individually exempted |

---

## 💥 Examples in 10 Seconds

### Stop Media Spam
```
/free @spammer
Click: 📸 Media ❌
→ All photos/videos auto-deleted
```

### Enable Flood Protection
```
/free
Click: 🌊 Floods ✅
→ Spam floods auto-deleted
```

### Night Mode
```
/free @user
Click: 🌙 Silence ✅
Click: 🌃 Night Mode
→ During night hours: User's media auto-deleted
```

### Verify Members
```
/free
Click: ✅ Checks ✅
→ New members must pass CAPTCHA
```

---

## 🔑 Key Features

✨ **Real-Time Auto-Delete**: Messages deleted instantly
✨ **Silent Operation**: No notifications or explanations
✨ **Group-Wide Controls**: Floods, spam, verification
✨ **Night Mode**: Time-based automatic restrictions
✨ **Exemptions**: Exempt trusted users from night mode
✨ **Audit Trail**: All actions logged

---

## ⚙️ Database Persistence

- ✅ All settings saved to database
- ✅ Survives bot restart
- ✅ Per-user, per-group configuration
- ✅ Real-time updates

---

## 🔐 Requirements

- Admin status required
- Bot needs delete message permission
- Bot needs restrict/unrestrict permission
- API running on port 8002

---

## 🚀 Advanced

### Content Restriction Cascade
Block "Media" → Blocks ALL:
- 📷 Photos
- 🎥 Videos
- 📄 Documents
- 🎵 Audio

### Night Mode Integration
- Works with `/nightmode` command
- Respects configured night hours
- Auto-exempts by role
- Can manually exempt users

### Spam Detection
- **Floods**: >4 messages in 5 seconds
- **Spam**: 3+ links in one message or multiple @mentions

---

## 📞 Troubleshooting

| Problem | Solution |
|---------|----------|
| Media not deleted | Check: Is media button showing ❌? |
| Settings disappear | Restart bot & API |
| Can't access menu | Need admin role |
| Permission denied | Check bot permissions in group |

---

## 🎯 Common Use Cases

| Use Case | Steps |
|----------|-------|
| **Mute User** | `/free @user` → Click `📝 Text ❌` |
| **Stop GIFs** | `/free @user` → Click `🎬 GIFs ❌` |
| **Block All Media** | `/free @user` → Click `📸 Media ❌` |
| **Spam Protection** | `/free` → Click `🌊 Floods ✅` `📨 Spam ✅` |
| **Night Quiet Hours** | `/free @user` → Click `🌙 Silence ✅` |
| **Verify New Members** | `/free` → Click `✅ Checks ✅` |

---

## 🔄 Related Commands

- `/restrict` - Old permission system (deprecated)
- `/unrestrict` - Old unrestrict (use `/free` instead)
- `/nightmode` - Configure night mode schedule
- `/ban` - Ban user
- `/kick` - Kick user
- `/mute` - Simple mute

---

**Pro Tip**: Use the `/free` menu interface for all permission management - it's faster and shows live status! 🚀
