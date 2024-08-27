import os
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.rest import Client
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_number = os.getenv('TWILIO_NUMBER')
client = Client(account_sid, auth_token)

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['password'])
    return None

def send_sms(to, message):
    try:
        message = client.messages.create(
            body=message,
            from_=twilio_number,
            to=to
        )
        print(f"Message sent with SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return False

def get_student_info(student_id):
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        cursor.execute("SELECT name, parent_contact FROM students WHERE student_id=%s", (student_id,))
        student = cursor.fetchone()
        conn.close()
        if student:
            return {"name": student['name'], "parent_contact": student['parent_contact']}
        else:
            return None
    except Exception as e:
        print(f"Failed to fetch student info: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['password'])
            login_user(user_obj)
            return redirect(url_for('marks'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='sha256')
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        conn.close()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/marks', methods=['GET', 'POST'])
@login_required
def marks():
    if request.method == 'POST':
        try:
            student_id = request.form['student_id']
            subject = request.form['subject']
            mark = int(request.form['mark'])
            
            student = get_student_info(student_id)
            if not student:
                flash('Student not found. Please check the student ID.', 'danger')
                return redirect(url_for('marks'))

            if mark < 40:
                message = f"Alert: Your child {student['name']} scored {mark} in {subject}."
                if send_sms(student['parent_contact'], message):
                    flash('Alert SMS sent successfully!', 'success')
                else:
                    flash('Failed to send alert SMS. Please try again later.', 'danger')

            conn = psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO marks (student_id, subject, mark) VALUES (%s, %s, %s)",
                           (student_id, subject, mark))
            conn.commit()
            conn.close()
            
            flash('Marks submitted successfully!', 'success')
            return redirect(url_for('marks'))
        except Exception as e:
            print(f"Error processing form: {e}")
            flash('An error occurred while submitting the form. Please try again.', 'danger')
            return redirect(url_for('marks'))
    
    return render_template('marks.html')

@app.route('/add', methods=['GET', 'POST'])
@login_required
def addStudent():
    if request.method == 'POST':
        try:
            student_id = request.form['student_id']
            studentName = request.form['name']
            parentNumber = "+91" + request.form['parentNumber']
            
            student = get_student_info(student_id)
            if student:
                flash('Student id already exist, please add student with a new id', 'danger') 
                return redirect(url_for('addStudent'))
            else:
                conn = psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO students (student_id, name, parent_contact) VALUES (%s, %s, %s)",
                               (student_id, studentName, parentNumber))
                conn.commit()
                conn.close()

                flash('Student added to database successfully', 'success')
                return redirect(url_for('marks'))
        except Exception as e:
            print(f"Some unexpected error occurred: {e}")
            flash('Some unexpected error occurred. Please try again', 'danger')
            return redirect(url_for('marks'))

    return render_template('add.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
