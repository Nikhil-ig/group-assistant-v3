# 🔧 Negative Group ID Parsing Fix

## Problem
Telegram groups can have negative IDs (e.g., `-123456789`). The bot was using `.split("_")` which broke when parsing callback data containing negative group IDs.

Example: `free_mute_123_-456` would split into:
- `["free", "mute", "123", "", "456"]` ❌ (extra empty string)

## Solution
Use `parts[-2]` and `parts[-1]` to get the last two parts (user_id and group_id) instead of relying on fixed index positions.

This ensures:
- Works with negative group IDs: `-456` stays as one part
- Works with positive group IDs: `456` works as expected
- More robust to future callback data format changes

## Files Fixed

### `/bot/main.py`

#### 1. **free_mute** callbacks (line ~5757)
```python
# Before (BROKEN with negative group IDs):
user_id = int(parts[3])
group_id = int(parts[4])

# After (WORKS with negative group IDs):
user_id = int(parts[-2])
group_id = int(parts[-1])
```

#### 2. **free_ban** callbacks (line ~5797)
- Same fix applied

#### 3. **free_warn** callbacks (line ~5837)
- Same fix applied

#### 4. **free_mute_all** callbacks (line ~5877)
- Same fix applied

#### 5. **free_toggle_nightmode** callbacks (line ~5917)
```python
# Before:
parts = data.replace("free_toggle_nightmode_", "").split("_")
user_id = int(parts[0])
group_id = int(parts[1])

# After:
remainder = data.replace("free_toggle_nightmode_", "")
last_underscore = remainder.rfind("_")
user_id = int(remainder[:last_underscore])
group_id = int(remainder[last_underscore+1:])
```

#### 6. **free_reset_all** callbacks (line ~5927)
- Same fix as free_toggle_nightmode

#### 7. **handle_permission_toggle_callback** (line ~5310)
```python
# For callback data: toggle_perm_{type}_{user_id}_{group_id}
# Handles types with underscores (e.g., "text_stickers")
perm_type = "_".join(parts[2:-2]) if len(parts) > 4 else parts[2]
user_id = int(parts[-2])
group_id = int(parts[-1])
```

#### 8. **handle_advanced_toggle** (line ~5501)
```python
# For callback data: adv_toggle_{action}_{user_id}_{group_id}
action = parts[1]
user_id = int(parts[-2])
group_id = int(parts[-1])
```

#### 9. **handle_advanced_refresh** (line ~5568)
```python
# For callback data: adv_refresh_{user_id}_{group_id}
user_id = int(parts[-2])
group_id = int(parts[-1])
```

## Testing
All parsers tested with negative group IDs:
- ✅ `toggle_perm_text_123_-456` → type=text, user_id=123, group_id=-456
- ✅ `free_mute_789_-654` → user_id=789, group_id=-654
- ✅ `adv_toggle_mute_321_-987` → action=mute, user_id=321, group_id=-987
- ✅ Compound types: `toggle_perm_text_stickers_456_-789` → type=text_stickers, user_id=456, group_id=-789

## Impact
- ✅ All permission callbacks now work with negative group IDs
- ✅ All advanced admin panel callbacks work with negative group IDs
- ✅ Backward compatible with positive group IDs
- ✅ More robust parsing method for future changes
