╔════════════════════════════════════════════════════════════════════════════╗
║             WHITELIST & BLACKLIST - QUICK REFERENCE & CHEATSHEET            ║
╚════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHITELIST COMMANDS CHEATSHEET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BASIC USAGE:
    /whitelist                                  Help menu
    /whitelist add @user exemption              Exempt from restrictions
    /whitelist add @user moderator              Default moderator (mute,unmute,warn,kick,restrict,unrestrict)
    /whitelist add @user moderator mute,warn    Custom powers
    /whitelist remove @user                     Remove from whitelist
    /whitelist list                             Show all whitelisted users
    /whitelist check @user                      Check user's whitelist status

EXAMPLES:
    /whitelist add @john exemption              → John bypasses message restrictions
    /whitelist add @mod moderator               → Mod can mute/unmute/warn
    /whitelist add @helper moderator warn       → Helper can only warn
    /whitelist remove @john                     → Remove John's exemption
    /whitelist list                             → See all exemptions & moderators


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BLACKLIST COMMANDS CHEATSHEET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BASIC USAGE:
    /blacklist                                  Help menu
    /blacklist add sticker <id>                 Block sticker
    /blacklist add gif <id>                     Block GIF
    /blacklist add user <id|@user>              Block user
    /blacklist add link <https://url>           Block specific link
    /blacklist add domain <example.com>         Block entire domain
    /blacklist list                             Show all blacklist items
    /blacklist list sticker                     Show blocked stickers only
    /blacklist check sticker <id>               Check if sticker blocked
    /blacklist remove <id>                      Remove from blacklist

EXAMPLES:
    /blacklist add sticker ABC123               → Block this sticker
    /blacklist add domain facebook.com          → Block all facebook links
    /blacklist add user 123456789               → Block this user
    /blacklist add link https://phishing.com    → Block this specific link
    /blacklist list                             → See all blocked items
    /blacklist check domain facebook.com        → Check if domain is blocked


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODERATOR POWERS AVAILABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Currently Active:
    mute              /mute @user
    unmute            /unmute @user
    warn              /warn @user [reason]
    restrict          /restrict @user
    unrestrict        /unrestrict @user
    kick              (Ready for implementation)
    send_link         (Bypass link filters)
    manage_stickers   (Manage sticker blacklist)
    manage_links      (Manage link blacklist)

Syntax to Grant Specific Powers:
    /whitelist add @user moderator power1,power2,power3

Example - Grant Only Warn & Mute:
    /whitelist add @helper moderator mute,warn


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERMISSION CHECKING - HOW IT WORKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When User Executes /mute:

    Is user TELEGRAM ADMIN?
        YES → Execute immediately ✅
        NO  → Go to next check ↓

    Is user MODERATOR with "mute" power in whitelist?
        YES → Execute immediately ✅
        NO  → ❌ Permission denied

Summary: Admin OR whitelisted moderator with power → Allowed


When Message is Restricted:

    Is sender EXEMPT (in whitelist exemption)?
        YES → Allow message ✅
        NO  → Go to next check ↓

    Is sender RESTRICTED (permission state)?
        YES → Delete message ❌
        NO  → Allow message ✅

Summary: Exempt users bypass restrictions


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRACTICAL SCENARIOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENARIO 1: Create a Help Team
──────────────────────────────
Goal: Non-admin team that helps moderate

    /whitelist add @help1 moderator mute,unmute,warn
    /whitelist add @help2 moderator mute,unmute,warn
    /whitelist add @help3 moderator warn

Result:
    • @help1 & @help2 can mute/unmute/warn
    • @help3 can only warn
    • None are Telegram admins
    • Can easily add/remove powers


SCENARIO 2: Protect Important Users
────────────────────────────────────
Goal: Trusted members' messages are never restricted

    /whitelist add @founder exemption
    /whitelist add @vip1 exemption
    /whitelist add @vip2 exemption

Later: /restrict @spammer (even if @vip1 gets restricted, they bypass it)

Result:
    • VIPs can always send messages
    • Restriction rules don't affect them


SCENARIO 3: Block Harmful Content
──────────────────────────────────
Goal: Auto-delete spam stickers, phishing links, bad domains

    /blacklist add domain facebook.com
    /blacklist add domain discord.gg
    /blacklist add sticker SPAM1ID
    /blacklist add user 999999999

Result:
    • All facebook/discord links auto-deleted
    • Spam sticker auto-deleted
    • User 999999999's messages auto-deleted


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMMON COMMANDS COMBINATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Setup Complete Moderation Team:
    /whitelist add @mod1 moderator mute,unmute,warn,kick
    /whitelist add @mod2 moderator warn,restrict,unrestrict
    /whitelist add @mod3 moderator mute,unmute

Setup VIP Protection:
    /whitelist add @boss exemption
    /whitelist add @vip exemption
    /whitelist add @trusted exemption

Block All Social Media:
    /blacklist add domain facebook.com
    /blacklist add domain instagram.com
    /blacklist add domain twitter.com
    /blacklist add domain tiktok.com
    /blacklist add domain linkedin.com
    /blacklist add domain youtube.com

Block Spam Sticker Pack:
    /blacklist add sticker STICKER1
    /blacklist add sticker STICKER2
    /blacklist add sticker STICKER3

View Everything:
    /whitelist list                 See all moderators & exemptions
    /blacklist list                 See all blocked items


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q: User not able to use /mute command
   A1: Is user an admin? (Check in group)
   A2: /whitelist check @user → Check if they're a moderator with "mute" power
   A3: If not whitelisted: /whitelist add @user moderator mute

Q: Whitelisted user's message still gets deleted
   A1: Check if user is restricted: /restrict → See current restrictions
   A2: Add to exemption: /whitelist add @user exemption
   A3: Or unrestrict: /unrestrict @user

Q: Domain block not working
   A1: Check exact format: /blacklist check domain example.com
   A2: Recheck domain name (case doesn't matter but spelling does)
   A3: Try parent domain if subdomain was blocked

Q: How to see who's moderator?
   A1: /whitelist list
   A2: /whitelist check @username

Q: Need to update moderator powers?
   A1: /whitelist remove @user
   A2: /whitelist add @user moderator [new,powers]


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT NOTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Only admins can manage whitelist/blacklist
• Whitelist/blacklist is PER-GROUP
• Moderators don't need Telegram admin status
• Multiple powers can be given/removed at once
• Blacklist auto-deletes messages by default
• Can manually remove items with IDs from /blacklist list
• Exempt users still follow group rules except restrictions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For detailed documentation, see: WHITELIST_BLACKLIST_SYSTEM.md

