import os
import json

# --- Security Configuration ---
DEFAULT_KEY = "579b464db66ec23bdd000001623c2de44ffb40755360bbc473134c16"
UIDAI_API_KEY = os.environ.get("UIDAI_API_KEY", DEFAULT_KEY)

def validate_api_key(headers):
    """Helper to validate API Key from event headers."""
    api_key = headers.get('x-api-key') or headers.get('X-Api-Key')
    if not api_key or api_key != UIDAI_API_KEY:
        return False
    return True

def unauthorized_response():
    return {
        "statusCode": 401,
        "body": json.dumps({"error": "Unauthorized: Valid UIDAI API Key required"})
    }

# --- Config ---
# Netlify function root is usually the current working directory
if os.path.exists(os.path.join(os.getcwd(), 'data')):
    DATA_DIR = os.path.join(os.getcwd(), 'data')
else:
    # Fallback to absolute path relative to this file
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
