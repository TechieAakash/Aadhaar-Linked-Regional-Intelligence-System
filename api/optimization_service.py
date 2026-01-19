from flask import Flask, jsonify, request
import os
from api.common import require_api_key
from backend.budget_optimizer import maximize_inclusion

app = Flask(__name__)

@app.route('/api/budget/optimize', methods=['POST'])
@require_api_key
def optimize_budget():
    """Triggers the budget optimization logic."""
    try:
        data = request.json
        budget = data.get('budget', 100000000) # Default 10Cr
        
        result = maximize_inclusion(budget)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
