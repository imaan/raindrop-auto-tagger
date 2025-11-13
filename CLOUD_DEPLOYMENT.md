# Cloud Deployment Guide for Raindrop Auto-Tagger

This guide shows you how to deploy the Raindrop Auto-Tagger to run automatically in the cloud.

## Option 1: GitHub Actions (Recommended - Free)

GitHub Actions is the easiest and most cost-effective option. It's completely free for public repositories and includes 2000 minutes/month for private repositories.

### Setup Steps:

1. **Create a GitHub Repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   gh repo create raindrop-auto-tagger --private
   git push -u origin main
   ```

2. **Add Your Secrets to GitHub:**
   - Go to your repository on GitHub.com
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret" and add:
     - Name: `RAINDROP_TOKEN`
       Value: Your Raindrop API token
     - Name: `CLAUDE_API_KEY`
       Value: Your Claude API key

3. **GitHub Actions workflow is already set up!**
   The `.github/workflows/daily-auto-tag.yml` file configures:
   - Daily runs at 2 AM UTC
   - Manual trigger capability
   - Log storage for 30 days

4. **Test the Workflow:**
   - Go to Actions tab in your GitHub repository
   - Select "Daily Raindrop Auto-Tagger"
   - Click "Run workflow" → "Run workflow" to test manually

### Customizing Schedule:

Edit `.github/workflows/daily-auto-tag.yml` and modify the cron expression:
```yaml
schedule:
  - cron: '0 2 * * *'  # Current: 2 AM UTC daily
  # Examples:
  # - cron: '0 14 * * *'  # 2 PM UTC daily
  # - cron: '0 */6 * * *'  # Every 6 hours
  # - cron: '0 8 * * 1'   # Every Monday at 8 AM UTC
```

---

## Option 2: Google Cloud Functions (Pay-per-use)

### Setup:

1. **Install Google Cloud CLI:**
   ```bash
   brew install --cask google-cloud-sdk
   gcloud init
   ```

2. **Create `main.py`:**
   ```python
   import os
   from raindrop_auto_tagger import RaindropAutoTagger

   def run_tagger(request):
       tagger = RaindropAutoTagger(
           raindrop_token=os.environ['RAINDROP_TOKEN'],
           claude_api_key=os.environ['CLAUDE_API_KEY']
       )
       tagger.run()
       return 'Tagging completed successfully'
   ```

3. **Deploy:**
   ```bash
   gcloud functions deploy raindrop-tagger \
     --runtime python39 \
     --trigger-http \
     --entry-point run_tagger \
     --set-env-vars RAINDROP_TOKEN=your_token,CLAUDE_API_KEY=your_key \
     --memory 256MB \
     --timeout 540s
   ```

4. **Schedule with Cloud Scheduler:**
   ```bash
   gcloud scheduler jobs create http raindrop-daily \
     --schedule="0 2 * * *" \
     --uri=YOUR_FUNCTION_URL \
     --http-method=GET
   ```

---

## Option 3: Railway.app (Simple, $5/month)

Railway offers easy deployment with cron jobs.

### Setup:

1. **Create account at railway.app**

2. **Deploy from GitHub:**
   - Connect your GitHub repository
   - Railway will auto-detect Python

3. **Add environment variables:**
   - RAINDROP_TOKEN
   - CLAUDE_API_KEY

4. **Add cron job in `railway.toml`:**
   ```toml
   [deploy]
   cronSchedule = "0 2 * * *"
   ```

---

## Option 4: Render.com (Free tier available)

### Setup:

1. **Create a `render.yaml`:**
   ```yaml
   services:
     - type: cron
       name: raindrop-tagger
       env: python
       schedule: "0 2 * * *"
       buildCommand: "pip install -r requirements.txt"
       startCommand: "python raindrop_auto_tagger.py"
       envVars:
         - key: RAINDROP_TOKEN
           sync: false
         - key: CLAUDE_API_KEY
           sync: false
   ```

2. **Deploy on Render.com:**
   - Connect GitHub repository
   - Add environment variables in dashboard
   - Deploy

---

## Option 5: AWS Lambda (Pay-per-use)

### Setup with Serverless Framework:

1. **Install Serverless:**
   ```bash
   npm install -g serverless
   ```

2. **Create `serverless.yml`:**
   ```yaml
   service: raindrop-tagger

   provider:
     name: aws
     runtime: python3.9
     environment:
       RAINDROP_TOKEN: ${env:RAINDROP_TOKEN}
       CLAUDE_API_KEY: ${env:CLAUDE_API_KEY}

   functions:
     tagger:
       handler: handler.run
       timeout: 600
       events:
         - schedule: rate(1 day)
   ```

3. **Create `handler.py`:**
   ```python
   import os
   from raindrop_auto_tagger import RaindropAutoTagger

   def run(event, context):
       tagger = RaindropAutoTagger(
           raindrop_token=os.environ['RAINDROP_TOKEN'],
           claude_api_key=os.environ['CLAUDE_API_KEY']
       )
       tagger.run()
       return {'statusCode': 200, 'body': 'Success'}
   ```

4. **Deploy:**
   ```bash
   serverless deploy
   ```

---

## Monitoring & Logs

### GitHub Actions:
- View logs: Actions tab → Workflow runs
- Download artifacts: Click on workflow run → Artifacts

### Google Cloud:
```bash
gcloud functions logs read raindrop-tagger
```

### AWS Lambda:
```bash
serverless logs -f tagger -t
```

### Railway/Render:
Check logs in their respective dashboards.

---

## Cost Comparison

| Platform | Cost | Pros | Cons |
|----------|------|------|------|
| GitHub Actions | Free (2000 min/mo) | Easy setup, great integration | Limited to GitHub |
| Google Cloud | ~$0.10/month | Scalable, reliable | More complex setup |
| Railway | $5/month | Very simple | Fixed monthly cost |
| Render | Free tier | Good free option | Limited resources on free |
| AWS Lambda | ~$0.05/month | Very scalable | Complex setup |

---

## Security Notes

1. **Never commit credentials to Git**
2. **Always use environment variables or secrets management**
3. **Rotate API keys periodically**
4. **Monitor usage for unusual activity**

---

## Troubleshooting

### Common Issues:

1. **Timeout errors:**
   - Increase timeout limits (10 minutes recommended)
   - Process fewer bookmarks per run

2. **API rate limits:**
   - Add delays between batches
   - Reduce batch size

3. **Memory issues:**
   - Increase allocated memory
   - Process smaller batches

### Support:
- Check workflow logs for detailed error messages
- Ensure API keys are valid and have proper permissions
- Verify network connectivity in cloud environment