from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "porter_catering_ais_2026_secure"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB total

# Email settings for testing (Gmail)
EMAIL_FROM = "aerodromefleet@gmail.com"
EMAIL_TO = "report@security-ais.com"
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "lsqugmsfjrthfzeu")

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app = Flask(__name__)
app.secret_key = "porter_catering_ais_2026_secure"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB total

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB = 'porter.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        name TEXT,
        license_number TEXT,
        password TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS flights (
        id INTEGER PRIMARY KEY,
        flight_number TEXT,
        date TEXT,
        time TEXT,
        guard_name TEXT,
        license_number TEXT,
        notes TEXT,
        created_at TEXT,
        created_by TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS photos (
        id INTEGER PRIMARY KEY,
        flight_id INTEGER,
        filename TEXT,
        uploaded_at TEXT,
        FOREIGN KEY(flight_id) REFERENCES flights(id)
    )''')
    # Create Gagan
    c.execute("INSERT OR IGNORE INTO users (username, name, license_number, password) VALUES (?, ?, ?, ?)",
              ("gagan", "Gagan", "", "Aisxx2026"))
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                            (username, password)).fetchone()
        conn.close()
        if user:
            session['user'] = user['username']
            session['name'] = user['name']
            session['license'] = user['license_number'] or ''
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    flights = conn.execute("SELECT * FROM flights ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('dashboard.html', flights=flights, name=session.get('name'))

@app.route('/new', methods=['GET', 'POST'])
def new_flight():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        flight_number = request.form.get('flight_number', '').strip()
        date = request.form.get('date')
        time = request.form.get('time')
        guard_name = request.form.get('guard_name', session.get('name'))
        license_number = request.form.get('license_number', session.get('license', ''))
        notes = request.form.get('notes', '')

        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO flights 
                     (flight_number, date, time, guard_name, license_number, notes, created_at, created_by)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (flight_number, date, time, guard_name, license_number, notes,
                   datetime.now().isoformat(), session['user']))
        flight_id = c.lastrowid

        # Handle multiple photos
        photos = request.files.getlist('photos')
        for photo in photos:
            if photo and photo.filename:
                filename = secure_filename(
                    f"porter_{flight_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{photo.filename}"
                )
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(path)
                c.execute("INSERT INTO photos (flight_id, filename, uploaded_at) VALUES (?, ?, ?)",
                          (flight_id, filename, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        # Send email notification
        send_flight_email(flight_id, flight_number, date, time, guard_name, license_number, notes, len([p for p in photos if p.filename]))

        flash(f'Flight {flight_number} saved with {len([p for p in photos if p.filename])} photos and emailed')
        return redirect(url_for('flight_detail', flight_id=flight_id))

    return render_template('new_flight.html', 
                           name=session.get('name'),
                           license=session.get('license', ''))

def send_flight_email(flight_id, flight_number, date, time, guard_name, license_number, notes, photo_count):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = f"Porter Catering Report - {flight_number} - {date}"

        body = f"""
Porter Catering Flight Report

Flight Number: {flight_number}
Date: {date}
Time: {time}
Guard: {guard_name}
Security License: {license_number or 'Not provided'}
Notes: {notes or 'None'}

Photos uploaded: {photo_count}

Flight ID: {flight_id}
(This is a test notification. Photos are stored on the server.)
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Email failed: {e}")

@app.route('/flight/<int:flight_id>')
def flight_detail(flight_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    flight = conn.execute("SELECT * FROM flights WHERE id = ?", (flight_id,)).fetchone()
    photos = conn.execute("SELECT * FROM photos WHERE flight_id = ? ORDER BY uploaded_at", (flight_id,)).fetchall()
    conn.close()
    if not flight:
        return "Flight not found", 404
    return render_template('flight_detail.html', flight=flight, photos=photos)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
