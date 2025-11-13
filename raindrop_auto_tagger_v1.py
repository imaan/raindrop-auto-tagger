#!/usr/bin/env python3
"""
Raindrop.io Automatic Bookmark Tagger
Fetches untagged bookmarks from Unsorted collection and auto-categorizes them using Claude API
"""

import json
import time
import requests
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import anthropic

class RaindropAutoTagger:
    def __init__(self, raindrop_token: str, claude_api_key: str):
        """
        Initialize the auto-tagger
        
        Args:
            raindrop_token: Raindrop.io API token
            claude_api_key: Anthropic Claude API key
        """
        self.raindrop_token = raindrop_token
        self.claude_api_key = claude_api_key
        self.raindrop_base_url = "https://api.raindrop.io/rest/v1"
        self.raindrop_headers = {
            "Authorization": f"Bearer {raindrop_token}",
            "Content-Type": "application/json"
        }
        self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
        
        self.stats = {
            "fetched": 0,
            "categorized": 0,
            "updated": 0,
            "failed": 0,
            "skipped": 0
        }
        
        self.log_file = f"raindrop_tagger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message: str):
        """Log message to both console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def get_existing_tags(self) -> List[str]:
        """Fetch all existing tags from Raindrop to understand current taxonomy"""
        try:
            response = requests.get(
                f"{self.raindrop_base_url}/tags",
                headers=self.raindrop_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tags = [item['_id'] for item in data.get('items', [])]
                self.log(f"📋 Fetched {len(tags)} existing tags from your collection")
                return tags
            else:
                self.log(f"⚠️  Could not fetch existing tags (status {response.status_code})")
                return []
                
        except Exception as e:
            self.log(f"⚠️  Error fetching tags: {e}")
            return []
    
    def fetch_untagged_bookmarks(self) -> List[Dict[str, Any]]:
        """Fetch bookmarks from Unsorted collection that have no tags"""
        try:
            all_untagged = []
            page = 0

            while True:
                # Use search API with notag:true to find untagged bookmarks in Unsorted collection
                params = {
                    "search": "notag:true",
                    "perpage": 50,  # Raindrop API max per page
                    "page": page
                }

                # Collection ID -1 is the Unsorted collection
                response = requests.get(
                    f"{self.raindrop_base_url}/raindrops/-1",
                    headers=self.raindrop_headers,
                    params=params,
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])

                    if not items:
                        # No more pages to fetch
                        break

                    all_untagged.extend(items)

                    # Check if there are more pages
                    if len(items) < 50:
                        # Less than full page, we've reached the end
                        break

                    page += 1
                    self.log(f"  📄 Fetched page {page} ({len(all_untagged)} bookmarks so far...)")

                    # Small delay to avoid rate limiting
                    time.sleep(0.5)

                else:
                    self.log(f"❌ Failed to fetch bookmarks: {response.status_code}")
                    self.log(f"Response: {response.text}")
                    break

            self.stats["fetched"] = len(all_untagged)
            self.log(f"📥 Found {len(all_untagged)} untagged bookmarks in Unsorted collection")

            return all_untagged

        except Exception as e:
            self.log(f"❌ Error fetching bookmarks: {e}")
            return []
    
    def categorize_bookmarks(self, bookmarks: List[Dict[str, Any]], existing_tags: List[str]) -> List[Dict[str, Any]]:
        """
        Use Claude API to categorize bookmarks
        
        Args:
            bookmarks: List of untagged bookmark objects from Raindrop
            existing_tags: List of existing tags in the collection
            
        Returns:
            List of bookmarks with suggested tags
        """
        if not bookmarks:
            return []

        # Don't log for every batch, that's handled by the caller

        # Prepare bookmark data for Claude
        bookmark_data = []
        for b in bookmarks:
            bookmark_data.append({
                "url": b.get('link', ''),
                "title": b.get('title', ''),
                "excerpt": b.get('excerpt', ''),
                "domain": b.get('domain', ''),
                "_id": b.get('_id')  # Keep the Raindrop ID for updating later
            })
        
        # Create the prompt for Claude
        prompt = f"""You are a bookmark categorization expert. I need you to categorize these bookmarks according to my established tag taxonomy.

EXISTING TAGS IN MY COLLECTION:
{', '.join(existing_tags[:100])}  # Showing top 100 tags

KEY TAGGING RULES:
1. Use ONLY tags from my existing collection above (be strict about this)
2. Maximum 4-5 tags per bookmark
3. Order: Primary category → Domain → Action → Specific
4. Most common primary tags: tool, design, learn, resource, product, dev, marketing, content, service
5. Add domain-specific tags: ai, blockchain, fitness, fashion, food, music, etc.
6. Add action tags when relevant: learn, resource, growth, automation

BOOKMARKS TO CATEGORIZE:
{json.dumps(bookmark_data, indent=2)}

Return a JSON array with this EXACT structure (and ONLY this JSON, no other text):
[
  {{
    "_id": "raindrop_id_here",
    "url": "url_here",
    "title": "title_here",
    "tags": ["tag1", "tag2", "tag3"]
  }}
]

Requirements:
- Return ONLY valid JSON (no markdown, no explanations)
- Include ALL bookmarks from the input
- Use only tags that exist in my collection
- 3-5 tags per bookmark (prioritize quality over quantity)
"""

        try:
            # Call Claude API (using Haiku model - faster and more cost-effective)
            message = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # Extract JSON from response (handle markdown code blocks if present)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON response
            categorized = json.loads(response_text)

            # Update stats with the count from this batch
            self.stats["categorized"] += len(categorized)

            return categorized

        except json.JSONDecodeError as e:
            self.log(f"  ⚠️  Failed to parse JSON response: {e}")
            # Try to salvage partial results if possible
            try:
                # Attempt to fix common JSON errors
                if response_text.strip().endswith(','):
                    response_text = response_text.strip()[:-1] + ']'
                elif not response_text.strip().endswith(']'):
                    response_text = response_text.strip() + ']'

                categorized = json.loads(response_text)
                self.stats["categorized"] += len(categorized)
                return categorized
            except:
                self.log(f"  ❌ Could not recover from JSON error")
                return []
        except Exception as e:
            self.log(f"❌ Error calling Claude API: {e}")
            return []
    
    def update_bookmark_tags(self, bookmark_id: str, tags: List[str], title: str) -> bool:
        """
        Update a bookmark's tags in Raindrop
        
        Args:
            bookmark_id: Raindrop bookmark ID
            tags: List of tags to apply
            title: Bookmark title (for logging)
            
        Returns:
            Success status
        """
        try:
            payload = {
                "tags": tags
            }
            
            response = requests.put(
                f"{self.raindrop_base_url}/raindrop/{bookmark_id}",
                headers=self.raindrop_headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.stats["updated"] += 1
                tags_str = ", ".join(tags)
                self.log(f"  ✅ {title[:60]}... → [{tags_str}]")
                return True
            else:
                self.stats["failed"] += 1
                self.log(f"  ❌ Failed to update {title[:60]}... (status {response.status_code})")
                return False
                
        except Exception as e:
            self.stats["failed"] += 1
            self.log(f"  ❌ Error updating {title[:60]}...: {e}")
            return False
    
    def run(self):
        """Main execution function"""
        self.log("="*70)
        self.log("🏷️  RAINDROP AUTO-TAGGER")
        self.log("="*70)
        self.log(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("")

        # Step 1: Get existing tags
        self.log("📋 Step 1: Fetching your existing tag taxonomy...")
        existing_tags = self.get_existing_tags()

        if not existing_tags:
            self.log("⚠️  Warning: Could not fetch existing tags. Will proceed with default taxonomy.")

        self.log("")

        # Step 2: Fetch untagged bookmarks
        self.log("📥 Step 2: Fetching untagged bookmarks from Unsorted collection...")
        untagged_bookmarks = self.fetch_untagged_bookmarks()

        if not untagged_bookmarks:
            self.log("✨ No untagged bookmarks found. Nothing to do!")
            self.print_summary()
            return

        self.log("")

        # Step 3: Process bookmarks in batches
        self.log("🤖 Step 3: Categorizing bookmarks with Claude AI...")

        BATCH_SIZE = 25  # Process 25 bookmarks at a time
        total_bookmarks = len(untagged_bookmarks)
        all_categorized = []

        for i in range(0, total_bookmarks, BATCH_SIZE):
            batch = untagged_bookmarks[i:i+BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (total_bookmarks + BATCH_SIZE - 1) // BATCH_SIZE

            self.log(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} bookmarks)...")

            # Categorize this batch
            categorized_batch = self.categorize_bookmarks(batch, existing_tags)

            if categorized_batch:
                all_categorized.extend(categorized_batch)
                self.log(f"  ✅ Batch {batch_num} categorized successfully")
            else:
                self.log(f"  ⚠️  Batch {batch_num} failed to categorize")

            # Small delay between batches
            if i + BATCH_SIZE < total_bookmarks:
                time.sleep(2)

        if not all_categorized:
            self.log("❌ No bookmarks were successfully categorized. Exiting.")
            self.print_summary()
            return

        self.log("")

        # Step 4: Apply tags
        self.log("🏷️  Step 4: Applying tags to bookmarks...")
        self.log("-" * 70)

        for bookmark in all_categorized:
            bookmark_id = bookmark.get('_id')
            tags = bookmark.get('tags', [])
            title = bookmark.get('title', 'Untitled')

            if not bookmark_id or not tags:
                self.stats["skipped"] += 1
                self.log(f"  ⚠️  Skipped {title[:60]}... (missing ID or tags)")
                continue

            # Apply tags
            self.update_bookmark_tags(bookmark_id, tags, title)

            # Rate limiting to avoid API throttling
            time.sleep(0.5)

        self.log("")
        self.print_summary()
    
    def print_summary(self):
        """Print execution summary"""
        self.log("="*70)
        self.log("📊 EXECUTION SUMMARY")
        self.log("="*70)
        self.log(f"Untagged bookmarks found:  {self.stats['fetched']}")
        self.log(f"Successfully categorized:   {self.stats['categorized']}")
        self.log(f"Tags applied:               {self.stats['updated']} ✅")
        self.log(f"Failed to update:           {self.stats['failed']} ❌")
        self.log(f"Skipped:                    {self.stats['skipped']} ⚠️")
        self.log("-" * 70)
        
        if self.stats['fetched'] > 0:
            success_rate = (self.stats['updated'] / self.stats['fetched'] * 100)
            self.log(f"Success rate: {success_rate:.1f}%")
        
        self.log(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Log saved to: {self.log_file}")
        self.log("="*70)


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("🏷️  RAINDROP AUTO-TAGGER")
    print("="*70)
    print("\nThis script will:")
    print("  1. Fetch untagged bookmarks from your Unsorted collection")
    print("  2. Categorize them using Claude AI")
    print("  3. Automatically apply appropriate tags")
    print("\n" + "-"*70)
    
    # Get API tokens from environment variables
    raindrop_token = os.environ.get('RAINDROP_TOKEN')
    claude_api_key = os.environ.get('CLAUDE_API_KEY')

    # Validate tokens
    if not raindrop_token:
        print("\n❌ Error: RAINDROP_TOKEN environment variable not set")
        print("\nUsage:")
        print("  export RAINDROP_TOKEN='your_token_here'")
        print("  export CLAUDE_API_KEY='your_api_key_here'")
        print("  python raindrop_auto_tagger.py")
        print("\nOr run in one line:")
        print("  RAINDROP_TOKEN='your_token' CLAUDE_API_KEY='your_key' python raindrop_auto_tagger.py")
        sys.exit(1)
    
    if not claude_api_key:
        print("\n❌ Error: CLAUDE_API_KEY environment variable not set")
        print("\nUsage:")
        print("  export RAINDROP_TOKEN='your_token_here'")
        print("  export CLAUDE_API_KEY='your_api_key_here'")
        print("  python raindrop_auto_tagger.py")
        print("\nOr run in one line:")
        print("  RAINDROP_TOKEN='your_token' CLAUDE_API_KEY='your_key' python raindrop_auto_tagger.py")
        sys.exit(1)
    
    print("\n✅ Tokens loaded successfully")
    print("-"*70 + "\n")
    
    # Create tagger and run
    tagger = RaindropAutoTagger(
        raindrop_token=raindrop_token,
        claude_api_key=claude_api_key
    )
    
    try:
        tagger.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        tagger.print_summary()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        tagger.print_summary()
        raise


if __name__ == "__main__":
    main()
