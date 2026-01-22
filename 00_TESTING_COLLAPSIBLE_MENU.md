# 🧪 Collapsible Menu - Testing Guide

## ✅ Ready to Test

All expand/collapse handlers have been implemented and syntax verified!

---

## 📋 Test Checklist

### Pre-Testing
- [ ] Bot is running
- [ ] Database is connected
- [ ] API server is available at correct endpoint
- [ ] Admin user has proper permissions

---

## 🎯 Test Scenarios

### Test 1: Initial Menu
**Command**: `/free @username` or reply with `/free`

**Expected Result**:
```
✅ Menu appears with:
   - Content Permissions section EXPANDED (▼)
   - Other 3 sections COLLAPSED (▶)
   - 6 content toggle buttons visible
   - 4 section header buttons visible
```

**Success Criteria**:
- [ ] Menu shows cleanly
- [ ] Content Permissions buttons are visible
- [ ] Other sections show only headers
- [ ] No errors in console

---

### Test 2: Expand Behavior Filters
**Action**: Click "▶ 🚨 BEHAVIOR FILTERS" button

**Expected Result**:
```
✅ Menu updates with:
   - Behavior Filters section now EXPANDED (▼)
   - Shows 4 toggle buttons:
     [🌊 Floods ✅] [📨 Spam ❌]
     [✅ Checks ❌] [🌙 Silence ❌]
   - Other sections remain with headers only
   - Message edits in place (no new message)
```

**Success Criteria**:
- [ ] Section expands smoothly
- [ ] Toggle buttons appear
- [ ] API data loads correctly
- [ ] Header changes to ▼ (expanded)

---

### Test 3: Collapse Behavior Filters
**Action**: Click "▼ 🚨 BEHAVIOR FILTERS" button again

**Expected Result**:
```
✅ Menu updates with:
   - Behavior Filters section now COLLAPSED (▶)
   - Only section header shows
   - Toggle buttons disappear
   - Returns to main menu view
```

**Success Criteria**:
- [ ] Section collapses smoothly
- [ ] Header changes back to ▶ (collapsed)
- [ ] Toggle buttons disappear
- [ ] Menu returns to clean view

---

### Test 4: Expand Night Mode
**Action**: Click "▶ 🌙 NIGHT MODE" button

**Expected Result**:
```
✅ Menu updates with:
   - Night Mode section now EXPANDED (▼)
   - Shows night mode status:
     [🌃 Night Mode ⭕ ACTIVE] or [Inactive]
   - Message edits in place
```

**Success Criteria**:
- [ ] Section expands
- [ ] Shows correct night mode status
- [ ] Fetch from API successful
- [ ] Header shows ▼

---

### Test 5: Expand Profile Analysis
**Action**: Click "▶ 🔍 PROFILE ANALYSIS" button

**Expected Result**:
```
✅ Menu updates with:
   - Profile Analysis section now EXPANDED (▼)
   - Shows 2 buttons:
     [🔗 Bio Scan] [⚠️ Risk Check]
   - Ready to run analysis
```

**Success Criteria**:
- [ ] Section expands
- [ ] Bio Scan button appears
- [ ] Risk Check button appears
- [ ] Header shows ▼

---

### Test 6: Toggle Permission While Expanded
**Action**: 
1. Expand Content Permissions (if not already)
2. Click "📝 Text ✅" button

**Expected Result**:
```
✅ Updates with:
   - Toast notification: "📝 Text 🔴 OFF"
   - Menu refreshes showing new state
   - Text button now shows ❌
```

**Success Criteria**:
- [ ] Permission toggles correctly
- [ ] Toast notification appears
- [ ] Menu refreshes automatically
- [ ] Button state updates

---

### Test 7: Toggle Behavior Filter
**Action**:
1. Expand Behavior Filters
2. Click "🌊 Floods ✅" button

**Expected Result**:
```
✅ Updates with:
   - Toast notification: "🌊 Floods 🔴 OFF"
   - Menu refreshes with new state
   - Floods button now shows ❌
```

**Success Criteria**:
- [ ] Setting toggles
- [ ] Toast appears
- [ ] Menu refreshes
- [ ] State updates

---

### Test 8: Switch Between Sections
**Action**:
1. Expand Content Permissions
2. Click "▼ 📋 CONTENT PERMISSIONS" to collapse
3. Click "▶ 🚨 BEHAVIOR FILTERS" to expand
4. Click "▼ 🚨 BEHAVIOR FILTERS" to collapse
5. Click "▶ 🌙 NIGHT MODE" to expand

**Expected Result**:
```
✅ Smooth transitions between sections
   - Only one section expanded at a time
   - Headers always visible
   - Clean visual flow
```

**Success Criteria**:
- [ ] Transitions are smooth
- [ ] No lag or delays
- [ ] Correct buttons shown
- [ ] No errors in logs

---

### Test 9: API Error Handling
**Action**: Disconnect API server, then try to expand a section

**Expected Result**:
```
✅ Error handling works:
   - Toast notification: "Error: Connection timeout"
   - User stays in menu
   - No crash or hang
   - Error logged in console
```

**Success Criteria**:
- [ ] Graceful error message
- [ ] No bot crash
- [ ] Menu still functional
- [ ] Error logged

---

### Test 10: Multiple Rapid Clicks
**Action**: Rapidly click expand/collapse buttons

**Expected Result**:
```
✅ No race conditions:
   - Each click processed in order
   - No duplicate messages
   - No stuck states
   - Menu stays responsive
```

**Success Criteria**:
- [ ] No duplicates
- [ ] Responsive to all clicks
- [ ] No hung states
- [ ] Proper state maintained

---

## 🔍 Debug Checklist

### If Menu Doesn't Appear
- [ ] Check bot is running
- [ ] Verify user is admin
- [ ] Check bot has permission to send messages
- [ ] Look for error in console

### If Expand/Collapse Doesn't Work
- [ ] Check callback data is being sent
- [ ] Verify handler is being triggered (check logs)
- [ ] Check for API connection errors
- [ ] Look for Python exceptions in terminal

### If API Data Doesn't Load
- [ ] Verify API server is running
- [ ] Check API key in config
- [ ] Verify group/user IDs are correct
- [ ] Check API response format

### If Menu Doesn't Update
- [ ] Check message.edit_text() is being called
- [ ] Verify reply_markup is set
- [ ] Check parse_mode is HTML
- [ ] Look for keyboard building errors

---

## 📊 Success Metrics

### Performance
- [ ] Expand takes <200ms
- [ ] Collapse takes <100ms
- [ ] Toggle takes <500ms
- [ ] No noticeable delay

### Reliability
- [ ] 100% success rate on expand/collapse
- [ ] 0 crashes in test session
- [ ] 0 duplicate messages
- [ ] All error cases handled

### UX
- [ ] Menu feels responsive
- [ ] Buttons are easy to click
- [ ] Text is readable
- [ ] Icons display correctly

---

## 🎯 Test Results Template

**Date**: ___________
**Tester**: ___________
**Environment**: Dev/Staging/Production

### Overall Result
- [ ] PASS - All tests successful
- [ ] PARTIAL - Some tests failed
- [ ] FAIL - Critical issues found

### Issues Found
1. _________________________________
2. _________________________________
3. _________________________________

### Notes
_________________________________
_________________________________
_________________________________

---

## 📝 Log Inspection

### What to Look For in Logs

**Successful Expand**:
```
📋 /free callback: free_expand_behavior_<user_id>_<group_id>
(API call info)
(Message edit info)
```

**Successful Toggle**:
```
📋 /free callback: free_toggle_text_<user_id>_<group_id>
📤 Sending toggle request...
📥 Response: 200 - {...}
```

**Error**:
```
❌ Behavior expand error: Connection timeout
Error logged with stack trace
```

---

## 🚀 Ready for Production?

Check all items before deploying:

- [ ] All 8 handlers implemented
- [ ] Syntax verified
- [ ] Error handling in place
- [ ] API integration working
- [ ] All tests passed
- [ ] Documentation complete
- [ ] No console errors
- [ ] Performance acceptable
- [ ] UI/UX satisfactory
- [ ] Admin approved

---

**Version**: 1.0  
**Created**: 2026-01-19  
**Status**: Ready for Testing  

Happy testing! 🧪✨

