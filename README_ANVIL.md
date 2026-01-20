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

## 🧭 Quick Troubleshoot Checklist (Frontend Fixes)

If you encounter errors like `Cannot read properties of undefined (reading 'editable')` in the Anvil IDE, follow this checklist:

- [ ] **Confirm component existence**: Ensure the component you are trying to access actually exists in your Form design.
- [ ] **Check `.editable` support**: Verify that the component you are accessing supports the `.editable` property (standard inputs do, but some custom components might not).
- [ ] **Execution Order**: Ensure your logic runs **after** `self.init_components()` in your Form's `__init__` method.
- [ ] **No Flask on Client**: Ensure you are not importing Flask in your Anvil Form code (Anvil Uses its own client-side Python).
- [ ] **Spelling & Casing**: Double-check the spelling and casing of your component names in the Anvil properties panel vs your code.

---
*ALRIS | Aadhaar Intelligence & Governance System Deployment Documentation*
