# Raindrop Auto-Tagger - Quick Reference

## First Time Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get your tokens
# Raindrop: https://app.raindrop.io/settings/integrations
# Claude: https://console.anthropic.com/settings/keys

# 3. Test run (one-time)
RAINDROP_TOKEN='your_token' CLAUDE_API_KEY='your_key' python raindrop_auto_tagger.py
```

## Daily Automation Setup

### macOS/Linux

```bash
# 1. Edit run_tagger.sh with your tokens
nano run_tagger.sh

# 2. Make executable
chmod +x run_tagger.sh

# 3. Test it
./run_tagger.sh

# 4. Set up daily cron job
crontab -e

# Add this line (runs at 9 AM daily):
0 9 * * * /full/path/to/run_tagger.sh
```

### Windows

```batch
# 1. Create run_tagger.bat with:
@echo off
set RAINDROP_TOKEN=your_token
set CLAUDE_API_KEY=your_key
cd C:\path\to\project
python raindrop_auto_tagger.py
pause

# 2. Open Task Scheduler
# Win + R → taskschd.msc

# 3. Create Basic Task → Daily → Start Program → run_tagger.bat
```

## Common Commands

```bash
# Run once manually
RAINDROP_TOKEN='token' CLAUDE_API_KEY='key' python raindrop_auto_tagger.py

# View latest log
ls -t raindrop_tagger_*.log | head -1 | xargs cat

# View cron logs (macOS)
log show --predicate 'process == "cron"' --last 1h

# View cron logs (Linux)
grep CRON /var/log/syslog | tail -20

# Test tokens are set
echo $RAINDROP_TOKEN
echo $CLAUDE_API_KEY
```

## Cron Schedule Examples

```bash
# Every day at 9 AM
0 9 * * * /path/to/run_tagger.sh

# Every day at midnight
0 0 * * * /path/to/run_tagger.sh

# Twice daily (9 AM and 9 PM)
0 9,21 * * * /path/to/run_tagger.sh

# Every 6 hours
0 */6 * * * /path/to/run_tagger.sh

# Weekdays only at 9 AM
0 9 * * 1-5 /path/to/run_tagger.sh
```

## What It Does

✅ Finds bookmarks in "Unsorted" with no tags
✅ Uses Claude AI to categorize them based on your taxonomy
✅ Automatically applies appropriate tags (3-5 per bookmark)
✅ Creates detailed log files
✅ Respects Raindrop API rate limits

## What It Doesn't Do

❌ Modify bookmarks that already have tags
❌ Move bookmarks between collections
❌ Change titles or URLs
❌ Delete or archive anything

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Token not set error | Export tokens before running script |
| 401 API error | Token expired - generate new one |
| No bookmarks found | Check "Unsorted" collection has untagged items |
| Cron not running | Use absolute paths in crontab |
| Python not found | Use `python3` instead of `python` |

## File Locations

```
project/
├── raindrop_auto_tagger.py    # Main script
├── run_tagger.sh               # Wrapper script (edit with your tokens)
├── requirements.txt            # Python dependencies
├── SETUP_GUIDE.md             # Detailed setup guide
├── QUICK_REFERENCE.md         # This file
└── logs/                      # Created by wrapper script
    └── cron_run_*.log
```

## Security Tips

🔒 **Never commit tokens to git:**
```bash
echo "run_tagger.sh" >> .gitignore
echo ".env" >> .gitignore
echo "*.log" >> .gitignore
```

🔒 **Use environment files:**
```bash
# Create .env file
echo "RAINDROP_TOKEN=your_token" > .env
echo "CLAUDE_API_KEY=your_key" >> .env

# Source it in wrapper script
source .env
python3 raindrop_auto_tagger.py
```

🔒 **macOS Keychain (most secure):**
```bash
# Store securely
security add-generic-password -a $(whoami) -s raindrop_token -w 'token'
security add-generic-password -a $(whoami) -s claude_key -w 'key'

# Retrieve in script
export RAINDROP_TOKEN=$(security find-generic-password -a $(whoami) -s raindrop_token -w)
export CLAUDE_API_KEY=$(security find-generic-password -a $(whoami) -s claude_key -w)
```

## Cost

**Claude API (Sonnet 4):**
- ~$0.01-0.05 per run (for typical 10-50 bookmarks)
- ~$0.30-1.50 per month for daily runs
- $5 free credits for new accounts

**Raindrop.io:**
- Free tier: Unlimited bookmarks & tags
- API access included in free tier

## Support

📖 Full guide: `SETUP_GUIDE.md`
🐛 Issues: Check log files first
✉️  Contact: Your logs will help diagnose issues

## Quick Test

```bash
# 1. Set tokens
export RAINDROP_TOKEN='your_token_here'
export CLAUDE_API_KEY='your_key_here'

# 2. Add a test bookmark manually to Raindrop
# Go to https://app.raindrop.io
# Add any URL to "Unsorted" without tags

# 3. Run the tagger
python raindrop_auto_tagger.py

# 4. Check if it got tagged!
# Refresh Raindrop and look for your bookmark
```

Success! 🎉 Your bookmark should now have relevant tags.
