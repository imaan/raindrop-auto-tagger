# Raindrop Auto-Tagger Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Your API Tokens

#### Raindrop.io Token:
1. Go to https://app.raindrop.io/settings/integrations
2. Click "Create new app"
3. Copy the "Test token" (for personal use)

#### Anthropic Claude API Key:
1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy and save it securely

### 3. Run the Script

**One-time run:**
```bash
RAINDROP_TOKEN='your_raindrop_token' CLAUDE_API_KEY='your_claude_key' python raindrop_auto_tagger.py
```

**Or set as environment variables:**
```bash
export RAINDROP_TOKEN='your_raindrop_token'
export CLAUDE_API_KEY='your_claude_key'
python raindrop_auto_tagger.py
```

## Setting Up Daily Automation

### Option A: macOS/Linux - Cron Job

1. **Create a wrapper script** (`run_tagger.sh`):
```bash
#!/bin/bash

# Set your API tokens
export RAINDROP_TOKEN='your_raindrop_token_here'
export CLAUDE_API_KEY='your_claude_api_key_here'

# Navigate to script directory
cd /path/to/your/raindrop/project

# Run the tagger
python3 raindrop_auto_tagger.py

# Optional: Send notification when complete (macOS)
# osascript -e 'display notification "Raindrop bookmarks tagged!" with title "Auto-Tagger Complete"'
```

2. **Make it executable:**
```bash
chmod +x run_tagger.sh
```

3. **Test it works:**
```bash
./run_tagger.sh
```

4. **Add to crontab:**
```bash
crontab -e
```

Add this line (runs daily at 9 AM):
```
0 9 * * * /path/to/your/run_tagger.sh >> /path/to/tagger_cron.log 2>&1
```

Or for midnight:
```
0 0 * * * /path/to/your/run_tagger.sh >> /path/to/tagger_cron.log 2>&1
```

### Option B: Windows - Task Scheduler

1. **Create a batch file** (`run_tagger.bat`):
```batch
@echo off
set RAINDROP_TOKEN=your_raindrop_token_here
set CLAUDE_API_KEY=your_claude_api_key_here

cd C:\path\to\your\raindrop\project
python raindrop_auto_tagger.py

pause
```

2. **Open Task Scheduler:**
   - Press Win + R, type `taskschd.msc`
   - Click "Create Basic Task"
   - Name: "Raindrop Auto-Tagger"
   - Trigger: Daily at your preferred time
   - Action: Start a program
   - Program: `C:\path\to\run_tagger.bat`

### Option C: Cloud Server (Always-On)

If you have a cloud server (AWS, DigitalOcean, etc.):

1. **Upload script to server**
2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up cron job as above**

## Security Best Practices

### Storing API Keys Securely

**Instead of hardcoding tokens in scripts, use:**

#### Option 1: Environment file (recommended)
Create a `.env` file:
```
RAINDROP_TOKEN=your_token_here
CLAUDE_API_KEY=your_key_here
```

Add to `.gitignore`:
```
.env
```

Modify wrapper script:
```bash
#!/bin/bash
cd /path/to/project
source .env
python3 raindrop_auto_tagger.py
```

#### Option 2: macOS Keychain
```bash
# Store tokens
security add-generic-password -a $(whoami) -s raindrop_token -w 'your_token'
security add-generic-password -a $(whoami) -s claude_key -w 'your_key'

# Retrieve in script
export RAINDROP_TOKEN=$(security find-generic-password -a $(whoami) -s raindrop_token -w)
export CLAUDE_API_KEY=$(security find-generic-password -a $(whoami) -s claude_key -w)
```

## Monitoring & Logs

### Log Files
Each run creates a timestamped log file:
- Format: `raindrop_tagger_YYYYMMDD_HHMMSS.log`
- Contains: All operations, successes, failures, and summary

### Check Recent Logs
```bash
# View latest log
ls -t raindrop_tagger_*.log | head -1 | xargs cat

# View all logs from today
grep -l "$(date +%Y%m%d)" raindrop_tagger_*.log | xargs cat

# Count successful operations
grep "Tags applied:" raindrop_tagger_*.log | tail -1
```

### Email Notifications (Optional)

Add to your wrapper script:
```bash
# Run tagger and capture output
OUTPUT=$(python3 raindrop_auto_tagger.py 2>&1)

# Send email summary (requires mail/sendmail configured)
echo "$OUTPUT" | mail -s "Raindrop Auto-Tagger Report" your@email.com
```

## Troubleshooting

### Issue: "RAINDROP_TOKEN environment variable not set"
**Solution:** Make sure you're exporting variables before running the script

### Issue: "Failed to fetch bookmarks: 401"
**Solution:** Your Raindrop token is invalid or expired. Generate a new one.

### Issue: "Error calling Claude API"
**Solution:** 
- Check your Claude API key is valid
- Verify you have API credits remaining
- Check your internet connection

### Issue: Cron job not running
**Solution:**
- Check cron logs: `grep CRON /var/log/syslog` (Linux) or `log show --predicate 'process == "cron"'` (macOS)
- Verify full paths in crontab (use absolute paths)
- Test wrapper script manually first

### Issue: Too many bookmarks at once
**Solution:** The script handles up to 50 bookmarks per run (Raindrop API limit). Run multiple times if needed, or modify the script's `perpage` parameter.

## Script Behavior

### What it does:
1. ✅ Fetches your existing tag taxonomy
2. ✅ Finds bookmarks in "Unsorted" with no tags
3. ✅ Sends them to Claude for categorization
4. ✅ Automatically applies the suggested tags
5. ✅ Creates a detailed log file

### What it doesn't do:
- ❌ Modify bookmarks that already have tags
- ❌ Move bookmarks to different collections
- ❌ Delete or archive bookmarks
- ❌ Change titles or URLs

### Rate Limiting
- 0.5 second delay between tag updates (to respect Raindrop API)
- Processes up to 50 bookmarks per run
- Safe for daily automation

## Cost Considerations

### Claude API Costs:
- Model: Claude Sonnet 4 (claude-sonnet-4-20250514)
- Typical cost per run: ~$0.01-0.05 (depending on number of bookmarks)
- Daily automation: ~$0.30-1.50/month

### Free Tier:
- Anthropic offers $5 free credits for new accounts
- Should cover several months of daily runs

## Example Output

```
======================================================================
🏷️  RAINDROP AUTO-TAGGER
======================================================================
Started at: 2025-01-15 09:00:00

📋 Step 1: Fetching your existing tag taxonomy...
📋 Fetched 156 existing tags from your collection

📥 Step 2: Fetching untagged bookmarks from Unsorted collection...
📥 Found 12 untagged bookmarks in Unsorted collection

🤖 Step 3: Categorizing bookmarks with Claude AI...
🤖 Sending 12 bookmarks to Claude for categorization...
✅ Claude categorized 12 bookmarks

🏷️  Step 4: Applying tags to bookmarks...
----------------------------------------------------------------------
  ✅ OpenAI GPT-4 API Documentation... → [ai, dev, api, resource]
  ✅ Nike Air Max 2024 Release... → [fashion, product, sneakers]
  ✅ Fitness Tracker Comparison Guide... → [fitness, resource, health]
  ...

======================================================================
📊 EXECUTION SUMMARY
======================================================================
Untagged bookmarks found:  12
Successfully categorized:   12
Tags applied:               12 ✅
Failed to update:           0 ❌
Skipped:                    0 ⚠️
----------------------------------------------------------------------
Success rate: 100.0%
Completed at: 2025-01-15 09:01:23
Log saved to: raindrop_tagger_20250115_090000.log
======================================================================
```

## Advanced Configuration

### Change Collection
To categorize bookmarks from a different collection:

Edit line 61 in `raindrop_auto_tagger.py`:
```python
# Change -1 to your collection ID
response = requests.get(
    f"{self.raindrop_base_url}/raindrops/12345",  # Your collection ID
    ...
)
```

Find collection IDs at: https://app.raindrop.io/

### Adjust Batch Size
To process more bookmarks per run:

Edit line 63:
```python
params = {
    "perpage": 50,  # Change to 25, 50, or 100
    ...
}
```

### Customize Tag Limits
To change max tags per bookmark:

Edit the prompt in line 152 to adjust "Maximum 4-5 tags per bookmark"

## Support

For issues or questions:
1. Check the log files first
2. Review this guide's troubleshooting section
3. Test with a small number of bookmarks first
4. Verify API tokens are valid and have proper permissions

## Changelog

- **v1.0** (2025-01-15): Initial release
  - Auto-fetch untagged bookmarks
  - Claude AI categorization
  - Automatic tag application
  - Detailed logging
