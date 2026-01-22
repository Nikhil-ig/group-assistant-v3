# 📨 /send Command - Quick Reference

## ✨ What's New

The `/send` command now supports **media forwarding** with captions!

## 🎬 Media Support

| Media Type | How to Use | Caption Support |
|-----------|-----------|-----------------|
| 📷 Photo | Reply to photo + `/send` | ✅ Preserved |
| 🎥 Video | Reply to video + `/send` | ✅ Preserved |
| 📄 Document | Reply to doc + `/send` | ✅ Preserved |
| 🎵 Audio | Reply to audio + `/send` | ✅ Preserved |
| 🎤 Voice | Reply to voice + `/send` | ✅ Preserved |
| 🎬 Animation | Reply to GIF + `/send` | ✅ Preserved |

## 📝 Text Mode (Still Works!)

```
/send <text>           → Send text message
/send pin <text>       → Send and pin
/send edit <id> <text> → Edit message
... and more!
```

## 🚀 Quick Start

### Send a Photo
```
1. Share a photo in the group
2. Reply to the photo
3. Type: /send
4. ✅ Photo sent with original caption!
```

### Send a Video
```
1. Share a video with caption
2. Reply to the video
3. Type: /send
4. ✅ Video + caption forwarded!
```

### Send a Document
```
1. Share a document (PDF, ZIP, etc.)
2. Reply to the document
3. Type: /send
4. ✅ Document sent!
```

## 🔐 Requirements

- ✅ Must be **admin** in the group
- ✅ Must **reply** to the media message
- ✅ Media must be in the same chat

## ❌ What Doesn't Work

- ❌ Forward media without replying
- ❌ Non-admins cannot use `/send`
- ❌ Multiple media in one reply (send separately)

## ✅ Error Handling

| Error | Solution |
|-------|----------|
| "❌ Admin permissions required" | You need admin rights |
| "❌ Please provide text or reply" | Reply to a message first |
| "❌ Error sending media" | Media might be corrupted |

## 📊 Status

```
Command:      /send
Status:       ✅ ACTIVE
Media:        ✅ SUPPORTED
Captions:     ✅ PRESERVED
Admin Only:   ✅ YES
Errors Fixed: ❌ NoneType error
```

---

**Last Updated:** 2026-01-20
**Version:** 3.1
