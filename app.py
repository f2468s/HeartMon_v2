from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


import sqlite3
import csv
import io
import os
import tempfile

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a strong and unique secret key
login_manager = LoginManager(app)


# Create an SQLite database and a table to store the blood pressure data
conn = sqlite3.connect('blood_pressure.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS blood_pressure (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dateTime TEXT NOT NULL,
        systolic REAL NOT NULL,
        diastolic REAL NOT NULL,
        pulse REAL NOT NULL
    )
''')
conn.commit()
conn.close()


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

# Replace this with your actual user authentication logic
def authenticate(username, password):
    # Example: Check if username and password match a database entry
    if username == 'your_username' and password == 'your_password':
        return User(username)
    return None

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate(username, password)
        if user:
            login_user(user)
            return redirect(url_for('protected'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/protected')
@login_required
def protected():
    return render_template('index.html')



@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/add_data', methods=['POST'])
def add_data():
    try:
        data = request.get_json()

        if data:
            conn = sqlite3.connect('blood_pressure.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO blood_pressure (dateTime, systolic, diastolic, pulse)
                VALUES (?, ?, ?, ?)
            ''', (data['dateTime'], data['systolic'], data['diastolic'], data['pulse']))
            conn.commit()
            conn.close()

            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/get_data')
def get_data():
    try:
        conn = sqlite3.connect('blood_pressure.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM blood_pressure')
        data = cursor.fetchall()
        conn.close()

        blood_pressure_data = [{'dateTime': row[1], 'systolic': row[2], 'diastolic': row[3], 'pulse': row[4]} for row in data]
        return jsonify({'data': blood_pressure_data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Endpoint to export data as SQLite database
@app.route('/export_db')
def export_db():
    # Connect to the SQLite database
    conn = sqlite3.connect('blood_pressure.db')

    # Create a temporary file to store the backup
    temp_backup_file = tempfile.NamedTemporaryFile(delete=False)
    temp_backup_file_name = temp_backup_file.name

    # Create a new SQLite database file and connect to it
    conn_backup = sqlite3.connect(temp_backup_file_name)

    # Execute a SQL command to copy the schema and data
    with conn_backup:
        for line in conn.iterdump():
            conn_backup.execute(line)

    # Close the connections
    conn.close()
    conn_backup.close()

    # Create a file-like object to store the backup
    file_like = io.BytesIO()

    # Read the contents of the temporary file into the file-like object
    with open(temp_backup_file_name, 'rb') as temp_db:
        file_like.write(temp_db.read())

    # Remove the temporary file
    temp_backup_file.close()

    # Seek to the beginning of the file-like object
    file_like.seek(0)

    # Send the SQLite database file for download
    return send_file(file_like, as_attachment=True, download_name='blood_pressure_export.db', mimetype='application/x-sqlite3')
# Endpoint to export data as CSV
@app.route('/export_csv')
def export_csv():
    # Connect to the SQLite database
    conn = sqlite3.connect('blood_pressure.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM blood_pressure')
    data = cursor.fetchall()
    conn.close()

    # Create a CSV file in-memory in binary mode
    csv_file = io.BytesIO()

    # Write the header
    header = ','.join(['ID','Date and Time', 'Systolic', 'Diastolic', 'Pulse'])
    csv_file.write((header + '\n').encode('utf-8'))

    # Write the data
    for row in data:
        # Format the row as a CSV line
        csv_line = ','.join([str(cell) for cell in row])
        csv_file.write((csv_line + '\n').encode('utf-8'))

    csv_file.seek(0)

    # Send the CSV file for download
    return send_file(csv_file, as_attachment=True, download_name='blood_pressure_export.csv', mimetype='text/csv')



if __name__ == '__main__':
    app.run(debug=True)
