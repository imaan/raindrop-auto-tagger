# Raindrop Auto-Tagger

Automatically categorizes your Raindrop.io bookmarks using Claude AI. Runs daily via GitHub Actions to tag unorganized bookmarks based on your existing tag taxonomy.

## Quick Setup

### 1. Fork this repository

Click the "Fork" button at the top of this page.

### 2. Get API credentials

**Raindrop.io token:**
- Go to [app.raindrop.io/settings/integrations](https://app.raindrop.io/settings/integrations)
- Click "Create new app"
- Copy the test token

**Claude API key:**
- Go to [console.anthropic.com](https://console.anthropic.com/)
- Navigate to API Keys
- Create a new key
- Copy it (starts with `sk-ant-api03-`)

### 3. Add secrets to your fork

In your forked repository:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `RAINDROP_TOKEN` with your Raindrop token
4. Add `CLAUDE_API_KEY` with your Claude key

### 4. Enable GitHub Actions

1. Go to the Actions tab
2. Click "I understand my workflows, go ahead and enable them"
3. The workflow runs daily at 2 AM UTC

### 5. Test it

1. Go to Actions tab
2. Select "Daily Raindrop Auto-Tagger"
3. Click "Run workflow" → "Run workflow"

## How It Works

The tool fetches untagged bookmarks from your Raindrop "Unsorted" collection, analyzes them with Claude AI using your existing tag taxonomy, and applies 3-5 relevant tags per bookmark. It preserves your existing tags and only suggests new ones when appropriate.

**What it does:**
- Processes untagged bookmarks in "Unsorted"
- Uses your existing tags as the categorization system
- Applies tags automatically

**What it doesn't do:**
- Modify bookmarks that already have tags
- Change titles, URLs, or collections
- Delete or archive anything

## Configuration

### Change the schedule

Edit `.github/workflows/daily-auto-tag.yml`:

```yaml
schedule:
  - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

Use [crontab.guru](https://crontab.guru/) to customize.

### Run locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export RAINDROP_TOKEN='your_token'
export CLAUDE_API_KEY='your_key'

# Run
python raindrop_auto_tagger.py

# Dry run (no changes)
python raindrop_auto_tagger.py --dry-run
```

### Adjust processing

Edit the `Config` class in `raindrop_auto_tagger.py`:

```python
class Config:
    BATCH_SIZE = 25              # Bookmarks per API call
    MAX_TAGS_PER_BOOKMARK = 5    # Maximum tags per bookmark
    CLAUDE_MODEL = "claude-3-haiku-20240307"
```

## Cost

- Claude API: ~$0.01-0.05 per run (using Haiku)
- Monthly: ~$0.30-1.50 for daily automation
- Raindrop.io: Free tier works fine
- GitHub Actions: Free (2000 minutes/month)

## Troubleshooting

**"Failed to fetch bookmarks: 401"**
- Your Raindrop token is invalid or expired

**"Error calling Claude API"**
- Check your Claude API key is valid
- Verify you have API credits remaining

**Workflow not running**
- Make sure GitHub Actions is enabled
- Check that secrets are set correctly
- View workflow logs in Actions tab for details

**No bookmarks found**
- Ensure you have untagged bookmarks in "Unsorted"
- The tool only processes bookmarks with zero tags

## License

MIT License - see LICENSE file for details.
