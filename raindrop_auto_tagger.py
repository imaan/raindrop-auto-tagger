#!/usr/bin/env python3
"""
Raindrop.io Automatic Bookmark Tagger - Production Version
Securely fetches untagged bookmarks from Raindrop.io and auto-categorizes them using Claude AI

This tool is designed to work as part of a larger ecosystem that includes:
- Raindrop.io for bookmark storage
- Claude AI for intelligent categorization
- MCP server for Claude desktop integration
- GitHub Actions for automated daily processing

Security Features:
- Input sanitization to prevent injection attacks
- Secure error handling that doesn't expose sensitive data
- Rate limiting and retry logic
- Validation of all external data
- Secure logging practices

Author: [Your Name]
License: MIT
Version: 2.0.0
"""

import json
import time
import requests
import os
import sys
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from logging.handlers import RotatingFileHandler
import anthropic
from anthropic import RateLimitError, APIError

# Constants for configuration
class Config:
    """Centralized configuration constants"""
    # API Configuration
    RAINDROP_BASE_URL = "https://api.raindrop.io/rest/v1"
    RAINDROP_TIMEOUT = 15
    CLAUDE_MODEL = "claude-3-haiku-20240307"  # Cost-effective model
    CLAUDE_MAX_TOKENS = 4096

    # Processing Configuration
    BATCH_SIZE = 25  # Bookmarks per Claude API call
    MAX_TAGS_PER_BOOKMARK = 5
    MIN_TAGS_PER_BOOKMARK = 2
    MAX_EXISTING_TAGS_TO_SHOW = 100

    # Rate Limiting Configuration
    RAINDROP_DELAY = 0.5  # Seconds between Raindrop API calls
    CLAUDE_DELAY = 2.0    # Seconds between Claude API calls
    MAX_RETRIES = 3
    RETRY_DELAY = 5.0

    # Security Configuration
    MAX_TITLE_LENGTH = 200
    MAX_EXCERPT_LENGTH = 500
    MAX_URL_LENGTH = 2000
    MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # Validation Patterns
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

class ProcessingStatus(Enum):
    """Status codes for bookmark processing"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RATE_LIMITED = "rate_limited"
    INVALID_DATA = "invalid_data"

@dataclass
class BookmarkData:
    """Sanitized bookmark data structure"""
    id: str
    url: str
    title: str
    excerpt: str
    domain: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "_id": self.id,
            "url": self.url,
            "title": self.title,
            "excerpt": self.excerpt,
            "domain": self.domain
        }

    @classmethod
    def from_raindrop(cls, data: Dict[str, Any]) -> Optional['BookmarkData']:
        """
        Create BookmarkData from Raindrop API response with validation

        Args:
            data: Raw bookmark data from Raindrop API

        Returns:
            Sanitized BookmarkData or None if invalid
        """
        try:
            # Extract and sanitize fields
            bookmark_id = str(data.get('_id', ''))
            url = cls._sanitize_url(data.get('link', ''))
            title = cls._sanitize_text(data.get('title', 'Untitled'), Config.MAX_TITLE_LENGTH)
            excerpt = cls._sanitize_text(data.get('excerpt', ''), Config.MAX_EXCERPT_LENGTH)
            domain = cls._sanitize_text(data.get('domain', ''), 100)

            # Validate required fields
            if not bookmark_id or not url:
                return None

            return cls(
                id=bookmark_id,
                url=url,
                title=title,
                excerpt=excerpt,
                domain=domain
            )
        except Exception:
            return None

    @staticmethod
    def _sanitize_text(text: str, max_length: int) -> str:
        """
        Sanitize text input to prevent injection attacks

        Args:
            text: Raw text input
            max_length: Maximum allowed length

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove control characters and normalize whitespace
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        text = ' '.join(text.split())

        # Truncate to maximum length
        if len(text) > max_length:
            text = text[:max_length-3] + "..."

        # Escape special characters for JSON
        text = text.replace('\\', '\\\\').replace('"', '\\"')

        return text

    @staticmethod
    def _sanitize_url(url: str) -> str:
        """
        Sanitize and validate URL

        Args:
            url: Raw URL input

        Returns:
            Sanitized URL or empty string if invalid
        """
        if not url:
            return ""

        # Truncate if too long
        if len(url) > Config.MAX_URL_LENGTH:
            return ""

        # Basic validation
        if not Config.URL_PATTERN.match(url):
            return ""

        return url

class SecureLogger:
    """
    Secure logging handler that prevents sensitive data exposure
    """

    def __init__(self, log_file: str):
        """Initialize secure logger with rotation"""
        self.logger = logging.getLogger('RaindropTagger')
        self.logger.setLevel(logging.INFO)

        # Create formatters
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=Config.MAX_LOG_FILE_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.sensitive_patterns = [
            (re.compile(r'(Bearer\s+)[^\s]+'), r'\1[REDACTED]'),
            (re.compile(r'(sk-ant-api\d+-)[^\s]+'), r'\1[REDACTED]'),
            (re.compile(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^"\']+)'), r'\1[REDACTED]'),
        ]

    def _sanitize_message(self, message: str) -> str:
        """Remove sensitive data from log messages"""
        for pattern, replacement in self.sensitive_patterns:
            message = pattern.sub(replacement, message)
        return message

    def info(self, message: str):
        """Log info message"""
        self.logger.info(self._sanitize_message(message))

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(self._sanitize_message(message))

    def error(self, message: str):
        """Log error message"""
        self.logger.error(self._sanitize_message(message))

    def success(self, message: str):
        """Log success message with emoji"""
        self.logger.info("✅ " + self._sanitize_message(message))

    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(self._sanitize_message(message))

class RateLimiter:
    """
    Rate limiting handler with exponential backoff
    """

    def __init__(self):
        self.last_call_times = {}
        self.retry_counts = {}

    def wait_if_needed(self, service: str, min_delay: float):
        """
        Enforce rate limiting for a service

        Args:
            service: Name of the service (e.g., 'raindrop', 'claude')
            min_delay: Minimum delay between calls in seconds
        """
        current_time = time.time()

        if service in self.last_call_times:
            elapsed = current_time - self.last_call_times[service]
            if elapsed < min_delay:
                time.sleep(min_delay - elapsed)

        self.last_call_times[service] = time.time()

    def handle_rate_limit(self, service: str, retry_after: Optional[int] = None):
        """
        Handle rate limit response with exponential backoff

        Args:
            service: Name of the service
            retry_after: Optional retry-after header value
        """
        if service not in self.retry_counts:
            self.retry_counts[service] = 0

        self.retry_counts[service] += 1

        if retry_after:
            wait_time = retry_after
        else:
            # Exponential backoff: 5, 10, 20, 40, etc.
            wait_time = Config.RETRY_DELAY * (2 ** self.retry_counts[service])

        # Cap at 5 minutes
        wait_time = min(wait_time, 300)

        return wait_time

    def reset_retry_count(self, service: str):
        """Reset retry count after successful call"""
        if service in self.retry_counts:
            self.retry_counts[service] = 0

class RaindropAutoTagger:
    """
    Main auto-tagger class with security enhancements
    """

    def __init__(self, raindrop_token: str, claude_api_key: str):
        """
        Initialize the auto-tagger with secure configuration

        Args:
            raindrop_token: Raindrop.io API token
            claude_api_key: Anthropic Claude API key
        """
        # Validate tokens
        if not raindrop_token or len(raindrop_token) < 10:
            raise ValueError("Invalid Raindrop token")
        if not claude_api_key or not claude_api_key.startswith('sk-ant-'):
            raise ValueError("Invalid Claude API key format")

        # Initialize API clients
        self.raindrop_headers = {
            "Authorization": f"Bearer {raindrop_token}",
            "Content-Type": "application/json",
            "User-Agent": "RaindropAutoTagger/2.0"
        }

        try:
            self.claude_client = anthropic.Anthropic(api_key=claude_api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Claude client: {str(e)}")

        # Initialize utilities
        self.rate_limiter = RateLimiter()

        # Initialize logging
        log_file = f"raindrop_tagger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = SecureLogger(log_file)

        # Initialize statistics
        self.stats = {
            "fetched": 0,
            "categorized": 0,
            "updated": 0,
            "failed": 0,
            "skipped": 0,
            "rate_limited": 0
        }

    def _make_raindrop_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """
        Make a rate-limited, retryable request to Raindrop API

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Response object or None if failed
        """
        url = f"{Config.RAINDROP_BASE_URL}{endpoint}"

        for attempt in range(Config.MAX_RETRIES):
            try:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed('raindrop', Config.RAINDROP_DELAY)

                # Make request
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.raindrop_headers,
                    timeout=Config.RAINDROP_TIMEOUT,
                    **kwargs
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    wait_time = self.rate_limiter.handle_rate_limit('raindrop', retry_after)
                    self.logger.warning(f"Rate limited by Raindrop. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Success
                if response.status_code in [200, 201, 204]:
                    self.rate_limiter.reset_retry_count('raindrop')
                    return response

                # Client error - don't retry
                if 400 <= response.status_code < 500:
                    self.logger.error(f"Client error from Raindrop: {response.status_code}")
                    return None

                # Server error - retry
                if response.status_code >= 500:
                    self.logger.warning(f"Server error from Raindrop: {response.status_code}. Retrying...")
                    time.sleep(Config.RETRY_DELAY)
                    continue

            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout on attempt {attempt + 1}/{Config.MAX_RETRIES}")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error: {str(e)}")

        return None

    def get_existing_tags(self) -> List[str]:
        """
        Fetch all existing tags from Raindrop with validation

        Returns:
            List of validated tag strings
        """
        self.logger.info("📋 Fetching existing tag taxonomy...")

        response = self._make_raindrop_request('GET', '/tags')

        if not response:
            self.logger.warning("Could not fetch existing tags")
            return []

        try:
            data = response.json()
            tags = []

            for item in data.get('items', []):
                tag = str(item.get('_id', '')).strip()
                # Validate tag format (alphanumeric, spaces, hyphens, underscores)
                if tag and re.match(r'^[\w\s-]+$', tag):
                    tags.append(tag)

            self.logger.success(f"Fetched {len(tags)} existing tags")
            return tags[:Config.MAX_EXISTING_TAGS_TO_SHOW]  # Limit for prompt size

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Error parsing tags response: {str(e)}")
            return []

    def fetch_untagged_bookmarks(self) -> List[BookmarkData]:
        """
        Fetch and validate untagged bookmarks from Unsorted collection

        Returns:
            List of validated BookmarkData objects
        """
        self.logger.info("📥 Fetching untagged bookmarks from Unsorted collection...")

        all_untagged = []
        page = 0
        max_pages = 20  # Safety limit

        while page < max_pages:
            params = {
                "search": "notag:true",
                "perpage": 50,
                "page": page
            }

            response = self._make_raindrop_request('GET', '/raindrops/-1', params=params)

            if not response:
                break

            try:
                data = response.json()
                items = data.get('items', [])

                if not items:
                    break

                # Validate and sanitize each bookmark
                for item in items:
                    bookmark = BookmarkData.from_raindrop(item)
                    if bookmark:
                        all_untagged.append(bookmark)
                    else:
                        self.stats["skipped"] += 1

                # Check if more pages exist
                if len(items) < 50:
                    break

                page += 1
                self.logger.info(f"  📄 Fetched page {page} ({len(all_untagged)} valid bookmarks)")

            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"Error parsing bookmarks: {str(e)}")
                break

        self.stats["fetched"] = len(all_untagged)
        self.logger.success(f"Found {len(all_untagged)} valid untagged bookmarks")

        return all_untagged

    def categorize_bookmarks(self, bookmarks: List[BookmarkData], existing_tags: List[str]) -> List[Dict[str, Any]]:
        """
        Use Claude API to categorize bookmarks with secure prompting

        Args:
            bookmarks: List of BookmarkData objects
            existing_tags: List of existing tags

        Returns:
            List of categorized bookmarks with tags
        """
        if not bookmarks:
            return []

        # Convert bookmarks to dict format for prompt
        bookmark_data = [b.to_dict() for b in bookmarks]

        # Create secure prompt
        prompt = self._create_categorization_prompt(bookmark_data, existing_tags)

        for attempt in range(Config.MAX_RETRIES):
            try:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed('claude', Config.CLAUDE_DELAY)

                # Call Claude API
                message = self.claude_client.messages.create(
                    model=Config.CLAUDE_MODEL,
                    max_tokens=Config.CLAUDE_MAX_TOKENS,
                    temperature=0.3,  # Lower temperature for consistency
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                # Parse response
                response_text = message.content[0].text
                categorized = self._parse_claude_response(response_text)

                if categorized:
                    self.rate_limiter.reset_retry_count('claude')
                    self.stats["categorized"] += len(categorized)
                    return categorized

            except RateLimitError as e:
                wait_time = self.rate_limiter.handle_rate_limit('claude')
                self.logger.warning(f"Rate limited by Claude. Waiting {wait_time}s...")
                self.stats["rate_limited"] += 1
                time.sleep(wait_time)

            except APIError as e:
                self.logger.error(f"Claude API error: {str(e)}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY)

            except Exception as e:
                self.logger.error(f"Unexpected error calling Claude: {str(e)}")
                break

        return []

    def _create_categorization_prompt(self, bookmarks: List[Dict], existing_tags: List[str]) -> str:
        """
        Create a secure categorization prompt

        Args:
            bookmarks: List of bookmark dictionaries
            existing_tags: List of existing tags

        Returns:
            Formatted prompt string
        """
        # Use a subset of tags if too many
        tags_to_show = existing_tags[:Config.MAX_EXISTING_TAGS_TO_SHOW]
        tags_str = ', '.join(tags_to_show)

        # Create prompt with clear instructions
        prompt = f"""You are a bookmark categorization expert. Categorize these bookmarks using the established tag taxonomy.

EXISTING TAGS (use these when possible):
{tags_str}

RULES:
1. Use existing tags when they fit
2. Create new tags only when necessary (lowercase, single words preferred)
3. Assign {Config.MIN_TAGS_PER_BOOKMARK}-{Config.MAX_TAGS_PER_BOOKMARK} tags per bookmark
4. Order tags by relevance: primary category → specific topic → action/type

BOOKMARKS TO CATEGORIZE:
{json.dumps(bookmarks, indent=2, ensure_ascii=False)}

Return ONLY a JSON array with this structure:
[{{"_id": "id", "tags": ["tag1", "tag2", "tag3"]}}]

No explanations, just the JSON array."""

        return prompt

    def _parse_claude_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Safely parse and validate Claude's JSON response

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed and validated categorization data
        """
        try:
            # Extract JSON from potential markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            response_text = response_text.strip()

            # Parse JSON
            categorized = json.loads(response_text)

            # Validate structure
            if not isinstance(categorized, list):
                return []

            validated = []
            for item in categorized:
                if not isinstance(item, dict):
                    continue

                bookmark_id = str(item.get('_id', ''))
                tags = item.get('tags', [])

                # Validate bookmark ID
                if not bookmark_id or not bookmark_id.isalnum():
                    continue

                # Validate and sanitize tags
                valid_tags = []
                for tag in tags[:Config.MAX_TAGS_PER_BOOKMARK]:
                    if isinstance(tag, str):
                        tag = tag.strip().lower()
                        # Basic tag validation
                        if tag and re.match(r'^[\w\s-]+$', tag) and len(tag) < 50:
                            valid_tags.append(tag)

                if valid_tags:
                    validated.append({
                        '_id': bookmark_id,
                        'tags': valid_tags
                    })

            return validated

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Error processing response: {str(e)}")
            return []

    def update_bookmark_tags(self, bookmark_id: str, tags: List[str], title: str) -> bool:
        """
        Update a bookmark's tags in Raindrop with validation

        Args:
            bookmark_id: Raindrop bookmark ID
            tags: List of tags to apply
            title: Bookmark title for logging

        Returns:
            Success status
        """
        # Validate inputs
        if not bookmark_id or not tags:
            return False

        # Sanitize title for logging
        title = title[:60] if title else "Untitled"

        payload = {"tags": tags}

        response = self._make_raindrop_request(
            'PUT',
            f'/raindrop/{bookmark_id}',
            json=payload
        )

        if response and response.status_code == 200:
            self.stats["updated"] += 1
            tags_str = ", ".join(tags[:3]) + ("..." if len(tags) > 3 else "")
            self.logger.success(f"{title}... → [{tags_str}]")
            return True
        else:
            self.stats["failed"] += 1
            self.logger.error(f"Failed to update {title}...")
            return False

    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Main execution function with dry-run support

        Args:
            dry_run: If True, don't actually update bookmarks

        Returns:
            Execution statistics
        """
        self.logger.info("="*70)
        self.logger.info("🏷️  RAINDROP AUTO-TAGGER v2.0")
        self.logger.info("="*70)
        self.logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if dry_run:
            self.logger.info("🔍 DRY RUN MODE - No changes will be made")

        self.logger.info("")

        # Step 1: Get existing tags
        existing_tags = self.get_existing_tags()

        if not existing_tags:
            self.logger.warning("No existing tags found. Will create new taxonomy.")

        # Step 2: Fetch untagged bookmarks
        untagged_bookmarks = self.fetch_untagged_bookmarks()

        if not untagged_bookmarks:
            self.logger.info("✨ No untagged bookmarks found. Nothing to do!")
            return self.stats

        # Step 3: Process bookmarks in batches
        self.logger.info(f"🤖 Categorizing {len(untagged_bookmarks)} bookmarks with Claude AI...")

        all_categorized = []
        total_bookmarks = len(untagged_bookmarks)

        for i in range(0, total_bookmarks, Config.BATCH_SIZE):
            batch = untagged_bookmarks[i:i+Config.BATCH_SIZE]
            batch_num = (i // Config.BATCH_SIZE) + 1
            total_batches = (total_bookmarks + Config.BATCH_SIZE - 1) // Config.BATCH_SIZE

            self.logger.info(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} bookmarks)...")

            categorized_batch = self.categorize_bookmarks(batch, existing_tags)

            if categorized_batch:
                all_categorized.extend(categorized_batch)
                self.logger.success(f"Batch {batch_num} categorized successfully")
            else:
                self.logger.warning(f"Batch {batch_num} failed to categorize")

        if not all_categorized:
            self.logger.error("No bookmarks were successfully categorized.")
            return self.stats

        # Step 4: Apply tags (unless dry run)
        if not dry_run:
            self.logger.info("🏷️  Applying tags to bookmarks...")

            # Create lookup for bookmark titles
            bookmark_lookup = {b.id: b.title for b in untagged_bookmarks}

            for item in all_categorized:
                bookmark_id = item.get('_id')
                tags = item.get('tags', [])
                title = bookmark_lookup.get(bookmark_id, 'Unknown')

                if bookmark_id and tags:
                    self.update_bookmark_tags(bookmark_id, tags, title)
                else:
                    self.stats["skipped"] += 1
        else:
            self.logger.info("🔍 DRY RUN - Skipping tag application")
            self.stats["updated"] = len(all_categorized)

        return self.stats

    def print_summary(self):
        """Print execution summary with statistics"""
        self.logger.info("="*70)
        self.logger.info("📊 EXECUTION SUMMARY")
        self.logger.info("="*70)
        self.logger.info(f"Untagged bookmarks found:  {self.stats['fetched']}")
        self.logger.info(f"Successfully categorized:   {self.stats['categorized']}")
        self.logger.info(f"Tags applied:               {self.stats['updated']} ✅")
        self.logger.info(f"Failed to update:           {self.stats['failed']} ❌")
        self.logger.info(f"Skipped (invalid):          {self.stats['skipped']} ⚠️")
        self.logger.info(f"Rate limit hits:            {self.stats['rate_limited']} 🚦")
        self.logger.info("-" * 70)

        if self.stats['fetched'] > 0:
            success_rate = (self.stats['updated'] / self.stats['fetched'] * 100)
            self.logger.info(f"Success rate: {success_rate:.1f}%")

        self.logger.info(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("="*70)


def main():
    """
    Main entry point with enhanced error handling and validation
    """
    print("\n" + "="*70)
    print("🏷️  RAINDROP AUTO-TAGGER v2.0")
    print("="*70)
    print("\nSecurely categorize your Raindrop.io bookmarks with AI")
    print("\nFeatures:")
    print("  ✅ Secure API handling with rate limiting")
    print("  ✅ Input validation and sanitization")
    print("  ✅ Intelligent retry logic")
    print("  ✅ Privacy-focused logging")
    print("-"*70)

    # Check for dry run mode
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv

    # Get API tokens from environment variables
    raindrop_token = os.environ.get('RAINDROP_TOKEN', '').strip()
    claude_api_key = os.environ.get('CLAUDE_API_KEY', '').strip()

    # Validate environment
    errors = []

    if not raindrop_token:
        errors.append("RAINDROP_TOKEN environment variable not set")
    elif len(raindrop_token) < 10:
        errors.append("RAINDROP_TOKEN appears to be invalid (too short)")

    if not claude_api_key:
        errors.append("CLAUDE_API_KEY environment variable not set")
    elif not claude_api_key.startswith('sk-ant-'):
        errors.append("CLAUDE_API_KEY doesn't match expected format (should start with 'sk-ant-')")

    if errors:
        print("\n❌ Configuration Errors:")
        for error in errors:
            print(f"  • {error}")
        print("\n📖 Setup Instructions:")
        print("  1. Get your Raindrop token from: https://app.raindrop.io/settings/integrations")
        print("  2. Get your Claude API key from: https://console.anthropic.com/")
        print("  3. Set environment variables:")
        print("     export RAINDROP_TOKEN='your_token_here'")
        print("     export CLAUDE_API_KEY='sk-ant-api03-...'")
        print("  4. Run the script:")
        print("     python raindrop_auto_tagger.py [--dry-run]")
        sys.exit(1)

    print("\n✅ Configuration validated")

    if dry_run:
        print("🔍 Running in DRY RUN mode - no changes will be made")

    print("-"*70 + "\n")

    # Initialize and run tagger
    try:
        tagger = RaindropAutoTagger(
            raindrop_token=raindrop_token,
            claude_api_key=claude_api_key
        )

        stats = tagger.run(dry_run=dry_run)
        tagger.print_summary()

        # Exit with appropriate code
        if stats['failed'] > 0:
            sys.exit(1)
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)

    except ValueError as e:
        print(f"\n❌ Configuration error: {str(e)}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()