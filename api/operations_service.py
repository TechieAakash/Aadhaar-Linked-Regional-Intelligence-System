import os
import json
import csv
import base64
from datetime import datetime
from api.common import DATA_DIR, validate_api_key, unauthorized_response

def handler(event, context):
    path = event.get('path', '')
    headers = event.get('headers', {})
    
    if not validate_api_key(headers):
        return unauthorized_response()
    
    try:
        data_path = os.path.join(DATA_DIR, 'integrated_service_risk.csv')
        if not os.path.exists(data_path):
            return {"statusCode": 404, "body": json.dumps({"error": "Risk data not found"})}

        # --- CSV Export ---
        if 'export/csv' in path:
            with open(data_path, 'rb') as f:
                content = f.read()
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "text/csv",
                    "Content-Disposition": f"attachment; filename=Regional_Analysis_{datetime.now().strftime('%Y%m%d')}.csv"
                },
                "body": base64.b64encode(content).decode('utf-8'),
                "isBase64Encoded": True
            }

        # --- PDF Export ---
        if 'export/pdf' in path:
            from fpdf import FPDF
            
            data = []
            states_seen = set()
            with open(data_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    state = row.get('state')
                    if state and state not in states_seen:
                        data.append(row)
                        states_seen.add(state)
            
            def get_risk(x):
                try: return float(x.get('integrated_risk_score', 0))
                except: return 0.0
            data.sort(key=get_risk, reverse=True)
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'UIDAI - Regional Classification Analysis Report', 0, 1, 'C')
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}', 0, 1, 'C')
            pdf.ln(5)
            
            col_widths = [60, 35, 30, 45, 20]
            headers_text = ['State / UT', 'Vuln. Score', 'Coverage %', 'Risk Category', 'Rank']
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(0, 61, 98) 
            pdf.set_text_color(255, 255, 255)
            for i, h in enumerate(headers_text):
                pdf.cell(col_widths[i], 8, h, 1, 0, 'C', True)
            pdf.ln()
            
            pdf.set_font('Arial', '', 8)
            pdf.set_text_color(0, 0, 0)
            for idx, row in enumerate(data):
                if idx % 2 == 0: pdf.set_fill_color(245, 245, 245)
                else: pdf.set_fill_color(255, 255, 255)
                
                pdf.cell(col_widths[0], 7, str(row['state'])[:30], 1, 0, 'L', True)
                try: r_v = float(row['integrated_risk_score'])
                except: r_v = 0.0
                pdf.cell(col_widths[1], 7, f"{r_v:.1f}", 1, 0, 'C', True)
                try: cov = float(row.get('biometric_update_ratio', 0)) * 100
                except: cov = 0.0
                pdf.cell(col_widths[2], 7, f"{cov:.1f}%", 1, 0, 'C', True)
                pdf.cell(col_widths[3], 7, str(row['service_risk_category'])[:20], 1, 0, 'C', True)
                pdf.cell(col_widths[4], 7, f"#{idx+1}", 1, 0, 'C', True)
                pdf.ln()
            
            pdf_bytes = pdf.output(dest='S') # Output as string/bytes if supported, or save and read
            # FPDF2 output('S') returns bytes
            
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/pdf",
                    "Content-Disposition": f"attachment; filename=Regional_Analysis_{datetime.now().strftime('%Y%m%d')}.pdf"
                },
                "body": base64.b64encode(pdf_bytes).decode('utf-8'),
                "isBase64Encoded": True
            }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    return {"statusCode": 404, "body": json.dumps({"error": "Operations endpoint not found"})}
