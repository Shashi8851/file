# app.py
from flask import Flask, request, send_file, render_template, jsonify
from datetime import datetime
import os
import json
import qrcode
import base64
from io import BytesIO

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure database
DB_FILE = 'database.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {'files': [], 'history': []}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

@app.route('/')
def index():
    db = load_db()
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=files, history=db['history'])

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        
        # Update database
        db = load_db()
        history_entry = {
            'filename': file.filename,
            'action': 'upload',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'size': os.path.getsize(filename)
        }
        db['history'].insert(0, history_entry)  # Add to beginning of history
        save_db(db)
        
        return 'File uploaded successfully'

@app.route('/download/<filename>')
def download_file(filename):
    try:
        # Update database with download history
        db = load_db()
        history_entry = {
            'filename': filename,
            'action': 'download',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'size': os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        }
        db['history'].insert(0, history_entry)
        save_db(db)
        
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)
    except:
        return 'File not found', 404

@app.route('/generate_qr/<filename>')
def generate_qr(filename):
    # Generate download URL
    download_url = f"{request.host_url}download/{filename}"
    
    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(download_url)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffered = BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return jsonify({'qr_code': img_str})

@app.route('/history')
def get_history():
    db = load_db()
    return jsonify(db['history'])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
