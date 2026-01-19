import os
import functools
from flask import request, jsonify

# --- Security Configuration ---
# API Key for UIDAI Analytics (Loaded from Environment with hardcoded fallback)
DEFAULT_KEY = "579b464db66ec23bdd000001623c2de44ffb40755360bbc473134c16"
UIDAI_API_KEY = os.environ.get("UIDAI_API_KEY", DEFAULT_KEY)

def require_api_key(f):
    """Decorator to enforce API Key validation on sensitive endpoints."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if not api_key or api_key != UIDAI_API_KEY:
            return jsonify({"error": "Unauthorized: Valid UIDAI API Key required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Config ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
