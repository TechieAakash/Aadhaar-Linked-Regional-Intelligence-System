# ALRIS Anvil Deployment Guide

This project is fully optimized for deployment on the **Anvil** platform using **Anvil Uplink**.

## 🚀 Pre-Deployment Checklist

1. **Anvil App Setup**:
   - Create a new app on [Anvil.works](https://anvil.works).
   - Enable **Uplink** in your Anvil App settings.
   - Copy your **Server Uplink Key**.

2. **Environment Configuration**:
   - Ensure the `ANVIL_UPLINK_KEY` environment variable is set on your hosting provider (e.g., PythonAnywhere, AWS, Azure, or locally).
   - Set `UIDAI_API_KEY` to your official government production key.

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🛠️ How to Connect

1. **Start the ALRIS Server**:
   ```bash
   python server.py
   ```
   *The server will print `[ALRIS] ✅ Anvil Uplink Connected Successfully.` once live.*

2. **Call Backend Functions from Anvil**:
   In your Anvil frontend code (Python), you can now call the ALRIS analytical engine directly:
   ```python
   # Example: Triggering Model Training from an Anvil Button
   result = anvil.server.call('train_trigger')
   print(result['message'])
   
   # Example: Fetching Social Risk Data
   risk_data = anvil.server.call('get_social_risk')
   ```

## 🛡️ Stability Features
- **Data Cleaning**: The backend automatically removes `NaN` and `Inf` values that cause browser crashes in Anvil.
- **Context Awareness**: The server intelligently detects if a call is coming from a web browser (Flask) or an Anvil Server callable, adjusting security and response formats automatically.
- **Mock Fallback**: If `anvil-uplink` is not installed, the server automatically enters "Safe Mode" and runs as a standard Flask dashboard without crashing.
