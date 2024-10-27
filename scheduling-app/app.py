from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
import os
import math
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace with a secure key

# Load the CSV data
data = pd.read_csv('data/data.csv')

# Get the list of unique functions and audits with their details
audits_df = data[['Audit Number', 'Audit Title', 'Function']].drop_duplicates()
functions = audits_df['Function'].unique()

# Initialize utilization for employees, converting BankID to int
utilization = {int(emp_id): 0 for emp_id in data['BankID'].unique()}

# User credentials (for demonstration purposes)
users = {
    'admin': generate_password_hash('admin123'),
    # Add more users as needed
}

@app.template_filter('datetime')
def datetime_filter(value, format='%Y-%m-%d'):
    return datetime.strptime(value, format)

app.jinja_env.filters['datetime'] = datetime_filter

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Authentication logic
        user_password_hash = users.get(username)
        if user_password_hash and check_password_hash(user_password_hash, password):
            session['username'] = username
            return redirect(url_for('select_audit'))
        else:
            error = "Invalid username or password"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return redirect(url_for('select_audit'))

@app.route('/select_audit', methods=['GET'])
@login_required
def select_audit():
    selected_function = request.args.get('function')
    
    if selected_function and selected_function != 'all':
        filtered_audits = audits_df[audits_df['Function'] == selected_function]
    else:
        filtered_audits = audits_df

    audits = filtered_audits.to_dict('records')
    return render_template('select_audit.html', functions=functions, audits=audits)

@app.route('/view_resources/<audit_number>', methods=['GET', 'POST'])
@login_required
def view_resources(audit_number):
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 7  # Limit to 7 resources per page

    # Filter the data for the selected audit
    project_data = data[data['Audit Number'] == int(audit_number)]
    if project_data.empty:
        return "No data found for the selected audit."

    # Get audit title
    audit_title = project_data['Audit Title'].iloc[0]

    # Employees for the project
    employees = project_data.to_dict('records')

    # Build a set of selected employee IDs for the current audit
    selected_emp_ids = set()
    if 'selections' in session:
        selected_emp_ids = set(
            selection['BankID']
            for selection in session['selections']
            if selection['Audit Number'] == int(audit_number)
        )

    # Update employees with current utilization
    filtered_employees = []
    for emp in employees:
        emp_id = int(emp['BankID'])
        emp_utilization = utilization.get(emp_id, 0)
        emp['Utilization'] = emp_utilization
        emp['Utilization Percent'] = f"{(emp_utilization / 250) * 100:.2f}%"
        availability_from_date = datetime.strptime(emp['AvailabilityFROM'], '%Y-%m-%d')
        availability_to_date = datetime.strptime(emp['AvailabilityTO'], '%Y-%m-%d')
        emp['available_days'] = (availability_to_date - availability_from_date).days + 1
        emp['availability_dates'] = f"{emp['AvailabilityFROM']} to {emp['AvailabilityTO']} ({emp['available_days']} days)"

        # Add selected flag and role from previous selection
        if emp_id in selected_emp_ids:
            emp['selected'] = True
            selected_data = next((sel for sel in session['selections'] if sel['BankID'] == emp_id and sel['Audit Number'] == int(audit_number)), None)
            if selected_data:
                emp['RecommendedRole'] = selected_data.get('RecommendedRole')
                emp['selected_days'] = selected_data.get('SelectedDays')
        else:
            emp['selected'] = False
            emp['RecommendedRole'] = ''
            emp['selected_days'] = ''

        filtered_employees.append(emp)

    # Pagination logic
    total_employees = len(filtered_employees)
    total_pages = math.ceil(total_employees / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_employees = filtered_employees[start:end]

    if request.method == 'POST':
        # Process form submission
        selected_employees = request.form.getlist('selected_employees')
        roles = {}
        selected_days = {}
        for emp_id in selected_employees:
            role = request.form.get(f'role_{emp_id}')
            days = request.form.get(f'days_{emp_id}')
            roles[emp_id] = role
            selected_days[emp_id] = days

        # Initialize session data if not present
        if 'selections' not in session:
            session['selections'] = []

        # Update utilization and store selections
        for emp_id in selected_employees:
            emp_id_int = int(emp_id)
            role = roles[emp_id]
            days = int(selected_days[emp_id])

            utilization[emp_id_int] += days  # Update utilization

            # Store the selection in session, converting to native Python types
            session['selections'].append({
                'Audit Number': int(audit_number),
                'Audit Title': audit_title,
                'BankID': emp_id_int,
                'RecommendedRole': role,
                'SelectedDays': days,
                'Utilization': utilization[emp_id_int]
            })

        # Mark the session as modified
        session.modified = True

        return redirect(url_for('view_resources', audit_number=str(audit_number), page=page))

    return render_template(
        'view_resources.html',
        audits=audits_df.to_dict('records'),
        functions=functions,
        audit_number=int(audit_number),
        audit_title=audit_title,
        employees=paginated_employees,
        page=page,
        total_pages=total_pages
    )

@app.route('/clear/<audit_number>')
@login_required
def clear_selections(audit_number):
    if 'selections' in session:
        # Filter out selections for the current audit
        current_selections = [sel for sel in session['selections'] if sel['Audit Number'] == int(audit_number)]

        for selection in current_selections:
            # Decrease utilization accordingly
            emp_id = selection['BankID']
            days = selection.get('SelectedDays', 0)
            if emp_id in utilization and utilization[emp_id] >= days:
                utilization[emp_id] -= days

        # Update session data to remove current audit selections
        session['selections'] = [
            selection for selection in session['selections']
            if selection['Audit Number'] != int(audit_number)
        ]

        session.modified = True

    return redirect(url_for('view_resources', audit_number=str(audit_number)))

if __name__ == '__main__':
    app.run(debug=True)
