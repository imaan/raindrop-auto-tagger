#!/usr/bin/env python3
"""
Web wrapper for Raindrop Auto-Tagger
This enables deployment to cloud platforms that require HTTP endpoints
like Google Cloud Run, Heroku, or similar services.
"""

import os
import json
from flask import Flask, jsonify, request
from raindrop_auto_tagger import RaindropAutoTagger
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "service": "Raindrop Auto-Tagger",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/run', methods=['GET', 'POST'])
def run_tagger():
    """
    Run the auto-tagger
    Can be triggered by GET or POST request
    Useful for webhooks, schedulers, or manual triggers
    """
    try:
        # Get credentials from environment
        raindrop_token = os.environ.get('RAINDROP_TOKEN')
        claude_api_key = os.environ.get('CLAUDE_API_KEY')

        if not raindrop_token or not claude_api_key:
            return jsonify({
                "error": "Missing API credentials",
                "message": "RAINDROP_TOKEN and CLAUDE_API_KEY must be set"
            }), 500

        # Optional: Check for authorization token if you want to secure the endpoint
        auth_token = os.environ.get('AUTH_TOKEN')
        if auth_token:
            provided_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if provided_token != auth_token:
                return jsonify({"error": "Unauthorized"}), 401

        # Run the tagger
        tagger = RaindropAutoTagger(
            raindrop_token=raindrop_token,
            claude_api_key=claude_api_key
        )

        # Run the tagging process
        tagger.run()

        # Return results
        return jsonify({
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "fetched": tagger.stats.get("fetched", 0),
                "categorized": tagger.stats.get("categorized", 0),
                "updated": tagger.stats.get("updated", 0),
                "failed": tagger.stats.get("failed", 0),
                "skipped": tagger.stats.get("skipped", 0)
            },
            "log_file": tagger.log_file
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics without running the tagger"""
    try:
        # This would need to read from a persistent store in production
        # For now, just return a placeholder
        return jsonify({
            "message": "Stats endpoint - implement persistent storage for production",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # For local testing
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)