from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')

@app.route('/api/index')
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/policy-simulator')
def policy_simulator():
    return render_template('policy_simulator.html')

@app.route('/lifecycle')
def lifecycle():
    return render_template('lifecycle.html')

@app.route('/planning')
def planning():
    return render_template('resource_planning.html')

@app.route('/forecasting')
def forecasting():
    return render_template('forecasting.html')

@app.route('/anomalies')
def anomalies():
    return render_template('anomalies.html')

@app.route('/decisions')
def decisions():
    return render_template('decisions.html')

@app.route('/execution-plan')
def execution_plan():
    return render_template('execution_plan.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/equity')
def equity():
    return render_template('equity_index.html')

@app.route('/equity/insights')
def equity_insights():
    return render_template('equity_insights.html')

@app.route('/social_risk')
def social_risk():
    return render_template('social_risk.html')

@app.route('/benchmarking')
def benchmarking():
    return render_template('benchmarking.html')

# --- Static Asset Fallbacks for Local Testing ---
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(os.getcwd(), 'static', 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(os.getcwd(), 'static', 'js'), filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(os.getcwd(), 'static', 'assets'), filename)
