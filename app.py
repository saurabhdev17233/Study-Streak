# app.py
from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ------------------ DATABASE SETUP ------------------
def init_db():
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS study_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        task_name TEXT NOT NULL,
                        duration INTEGER NOT NULL,
                        date TEXT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
        conn.commit()

init_db()

# ------------------ EMAIL FUNCTION ------------------
def send_confirmation_email(receiver_email, username):
    msg = EmailMessage()
    msg['Subject'] = 'StudyStreak | Registration Successful'
    msg['From'] = 'your_email@gmail.com'
    msg['To'] = receiver_email
    msg.set_content(f"Hello {username},\n\nWelcome to StudyStreak! You're all set to start tracking your study habits.\n\nHappy studying!")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('your_email@gmail.com', 'your_app_password')
            smtp.send_message(msg)
    except Exception as e:
        print("Email failed to send:", e)

# ------------------ ROUTES ------------------
@app.route('/')
def home():
    return redirect('/login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                          (username, email, password))
                conn.commit()
                send_confirmation_email(email, username)
                flash('Registration successful! Please log in.', 'success')
                return redirect('/login')
            except sqlite3.IntegrityError:
                flash('Email already registered. Please use another.', 'danger')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute("SELECT id, username, password FROM users WHERE email = ?", (email,))
            user = c.fetchone()

            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                return redirect('/dashboard')
            else:
                flash('Invalid credentials', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT task_name, duration, date FROM study_sessions WHERE user_id = ? ORDER BY date DESC LIMIT 5", (session['user_id'],))
        sessions = c.fetchall()

        # Calculate streak: consecutive days with study sessions
        c.execute("SELECT DISTINCT date FROM study_sessions WHERE user_id = ? ORDER BY date DESC", (session['user_id'],))
        dates = [datetime.strptime(row[0].split()[0], '%Y-%m-%d').date() for row in c.fetchall()]

        streak = 0
        today = date.today()
        for i, d in enumerate(dates):
            if d == today or (i > 0 and (dates[i-1] - d).days == 1):
                streak += 1
                today = d
            else:
                break

    return render_template('dashboard.html', sessions=sessions, username=session['username'], streak=streak)

@app.route('/timer', methods=['GET', 'POST'])
def timer():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        task_name = request.form['task']
        duration = int(request.form['duration'])
        date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO study_sessions (user_id, task_name, duration, date) VALUES (?, ?, ?, ?)",
                      (session['user_id'], task_name, duration, date_now))
            conn.commit()
        flash('Study session logged!', 'success')
        return redirect('/dashboard')

    return render_template('timer.html')

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect('/login')

    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT task_name, duration, date FROM study_sessions WHERE user_id = ? ORDER BY date DESC", (session['user_id'],))
        sessions = c.fetchall()
    return render_template('history.html', sessions=sessions)

if __name__ == '__main__':
    app.run(debug=True)
