from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# Function to read users from CSV
def read_users():
    users = {}
    with open('users.csv', mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            users[row['username']] = row['password']
    return users

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = read_users()
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid Credentials. Please try again.'
            return render_template('login.html', error=error)
    else:
        return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        username = session['username']
        return render_template('dashboard.html', username=username)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
