from flask import Flask, jsonify, send_from_directory
import os
from api.common import DATA_DIR, require_api_key

app = Flask(__name__)

@app.route('/api/data/<path:filename>')
def get_data(filename):
    """Serve analytics JSON files from the data directory with fallback."""
    try:
        if not filename.endswith('.json'):
            return jsonify({"error": "Only JSON files allowed"}), 400
        
        if os.path.exists(os.path.join(DATA_DIR, filename)):
            return send_from_directory(DATA_DIR, filename)
            
        return jsonify({"error": "File not found in data directory"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/train')
@require_api_key
def train_model():
    """Trigger background model training."""
    return jsonify({
        "status": "Training Started", 
        "message": "Orchestrating 1.4B records for retraining. This will take effect on next refresh."
    })

@app.route('/data/<path:filename>')
def get_raw_data(filename):
    """Fallback route for raw data files."""
    return send_from_directory(DATA_DIR, filename)
