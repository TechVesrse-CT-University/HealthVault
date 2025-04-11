from flask import Flask, render_template, request, redirect, url_for, jsonify
import PyPDF2
from PIL import Image
import pytesseract
import openai
import os
from io import BytesIO
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from flask import Flask, render_template, request, jsonify
import os
import uuid
import PIL.Image
import google.generativeai as genai
from google.generativeai import types
import os
import uuid
import requests

app = Flask(__name__)
chat_history = []

TWILIO_SID = 'SID'
TWILIO_AUTH_TOKEN = 'AUTHTOKEN'
TWILIO_PHONE_NUMBER = 'SAMPLEPHONE'

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        phone_number = data.get('phone')
        password = data.get('password')

        if not phone_number or not password:
            return jsonify({'success': False, 'error': 'Phone number and password are required'}), 400

        if not phone_number.startswith('+') or not phone_number[1:].isdigit():
            return jsonify({'success': False, 'error': 'Invalid phone number format. Use E.164 format (e.g., +12345678901)'}), 400

       
        message = client.messages.create(
            body='You have successfully logged into HealthVault!',
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )

        return jsonify({'success': True, 'message': 'Login successful, SMS sent!', 'sid': message.sid}), 200

    except TwilioRestException as te:
        return jsonify({'success': False, 'error': f'Twilio error: {str(te)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

def analyze_report(file):
    try:
        if file.filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            if not text:
                return "No text extracted from PDF."
        elif file.filename.endswith('.jpg'):
            img = Image.open(BytesIO(file.read()))
            text = pytesseract.image_to_string(img)
            if not text.strip():
                return "No text extracted from image."
        else:
            return "Unsupported file type. Please upload a PDF or JPG."

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a medical assistant. Simplify medical reports into easy language for rural users. Extract key metrics like blood pressure, cholesterol, or glucose, and explain them (e.g., 'normal' or 'high')."},
                {"role": "user", "content": f"Analyze this report and simplify it: {text}"}
            ],
            max_tokens=150
        )
        simplified_text = response.choices[0].message['content'].strip()
        return simplified_text
    except Exception as e:
        return f"Error analyzing report: {str(e)}"
genai.configure(api_key="genkey")

@app.route('/')
def home():
    return render_template('start.html')

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global chat_history
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(url_for('upload'))
        file = request.files['file']
        if file.filename == '':
            return redirect(url_for('upload'))
        if file:
            analysis = analyze_report(file)
            chat_history.append({"role": "assistant", "content": analysis})
    return render_template('upload.html', chat_history=chat_history)

@app.route('/hospital')
def hospital():
    return render_template('hospital.html')

@app.route('/doctors')
def doctors():
    return render_template('doctors.html')

if __name__ == '__main__':
    app.run(debug=True)