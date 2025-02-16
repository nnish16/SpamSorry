from flask import Flask, request, jsonify, render_template
import pandas as pd
import re
import smtplib
import os
from werkzeug.utils import secure_filename
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to extract emails from text
def extract_emails(text):
    return re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)

# Function to extract emails from files
def extract_emails_from_file(filepath):
    emails = []
    if filepath.endswith('.csv') or filepath.endswith('.xlsx'):
        df = pd.read_csv(filepath) if filepath.endswith('.csv') else pd.read_excel(filepath)
        for col in df.columns:
            emails.extend(extract_emails(' '.join(df[col].astype(str))))
    return list(set(emails))

# Endpoint to upload file and extract emails
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    emails = extract_emails_from_file(filepath)
    return jsonify({'emails': emails})

# Endpoint to send bulk email
@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.json
    email_list = data.get('emails', [])
    subject = data.get('subject', 'No Subject')
    message = data.get('message', 'No Content')
    sender_email = os.getenv('EMAIL_SENDER')
    sender_password = os.getenv('EMAIL_PASSWORD')
    
    if not sender_email or not sender_password:
        return jsonify({'error': 'Missing email credentials'}), 400

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    
    for email in email_list:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        server.sendmail(sender_email, email, msg.as_string())
    
    server.quit()
    return jsonify({'message': 'Emails sent successfully'})

if __name__ == '__main__':
    app.run(debug=True)