import os
import json
from api.common import DATA_DIR, validate_api_key, unauthorized_response

def handler(event, context):
    path = event.get('path', '')
    headers = event.get('headers', {})
    
    # 1. Handle Training Trigger
    if 'train' in path:
        if not validate_api_key(headers):
            return unauthorized_response()
            
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "Training Started", 
                "message": "Orchestrating 1.4B records for retraining (Netlify Lambda)."
            })
        }
    
    # 2. Handle Data Serving
    filename = path.split('/')[-1]
    if not filename.endswith('.json'):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Only JSON files allowed"})
        }
    
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(data)
        }
        
    return {
        "statusCode": 404,
        "body": json.dumps({"error": f"File {filename} not found in data directory"})
    }
