import os
import json
from api.common import validate_api_key, unauthorized_response
from backend.budget_optimizer import maximize_inclusion

def handler(event, context):
    headers = event.get('headers', {})
    
    if not validate_api_key(headers):
        return unauthorized_response()
    
    if event.get('httpMethod') != 'POST':
        return {"statusCode": 405, "body": json.dumps({"error": "Method not allowed"})}
    
    try:
        data = json.loads(event.get('body', '{}'))
        budget = data.get('budget', 100000000) # Default 10Cr
        
        result = maximize_inclusion(budget)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result)
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
