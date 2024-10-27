import streamlit as st
import pandas as pd
import numpy as np
import math
import io

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'selections' not in st.session_state:
    st.session_state.selections = []
if 'utilization' not in st.session_state:
    st.session_state.utilization = {}
if 'current_audit' not in st.session_state:
    st.session_state.current_audit = None
if 'page' not in st.session_state:
    st.session_state.page = 1

# User credentials (for demonstration purposes)
users = {
    'admin': 'password123',
    # Add more users as needed
}

# Load the CSV data
@st.cache_data
def load_data():
    data = pd.read_csv('data/data.csv')
    return data

data = load_data()

# Mapping from SchedulingPhase to phase letter
phase_mapping = {
    '1': 'P',
    '2': 'F',
    '3': 'R',
    '4': 'C'  # Assuming 'C' for phase 4
}

# Get the list of unique audits with their details
audits_df = data[['Audit Number', 'Audit Title']].drop_duplicates()
audits = audits_df.to_dict('records')

# Initialize utilization for employees, converting BankID to int
if not st.session_state.utilization:
    st.session_state.utilization = {int(emp_id): 0 for emp_id in data['BankID'].unique()}

# Function to handle login
def login():
    st.title('Scheduling Assistant')
    st.write('---')
    st.header('Login')
    username = st.text_input('Username', key='login_username')
    password = st.text_input('Password', type='password', key='login_password')
    if st.button('Login'):
        if username in users and password == users[username]:
            st.session_state.logged_in = True
            st.session_state.username = username
            # Reset page number
            st.session_state.page = 1
            # Redirect to the main app
            main_app()
        else:
            st.error('Invalid username or password')

# Function to handle logout
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.selections = []
    st.session_state.utilization = {int(emp_id): 0 for emp_id in data['BankID'].unique()}
    st.session_state.page = 1
    st.session_state.current_audit = None
    # Redirect to the login page
    login()

# Main application
def main_app():
    st.set_page_config(layout='wide')
    # Banner
    st.markdown(
        """
        <div style="background-color:#00A1E0;padding:10px;">
            <h1 style="color:white;text-align:center;">
                <i class="fas fa-calendar-alt"></i> Scheduling Assistant
            </h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Welcome message and logout button
    cols = st.columns([8, 1])
    with cols[0]:
        st.write(f"Welcome, **{st.session_state.username}**")
    with cols[1]:
        if st.button('Logout'):
            logout()
            return

    # Sidebar for audit selection
    st.sidebar.title('Select Audit')
    audit_options = {f"{audit['Audit Number']} - {audit['Audit Title']}": audit['Audit Number'] for audit in audits}
    selected_audit_key = st.sidebar.selectbox('Audit', list(audit_options.keys()))
    audit_number = audit_options[selected_audit_key]
    st.session_state.current_audit = audit_number

    # Reset page number when audit changes
    if 'previous_audit' not in st.session_state or st.session_state.previous_audit != audit_number:
        st.session_state.page = 1
        st.session_state.previous_audit = audit_number

    # Main content
    audit_title = audits_df[audits_df['Audit Number'] == int(audit_number)]['Audit Title'].values[0]
    st.header(f'Audit {audit_number} - {audit_title}')

    # Pagination
    per_page = 7

    total_employees = 0  # Will update later after filtering

    # Fetch and process data
    def get_paginated_employees():
        nonlocal total_employees
        # Filter the data for the selected audit
        project_data = data[data['Audit Number'] == int(audit_number)]
        if project_data.empty:
            st.write("No data found for the selected audit.")
            return []

        employees = project_data.to_dict('records')

        # Build a set of selected employee IDs for the current audit
        selected_emp_ids = set(
            selection['BankID']
            for selection in st.session_state.selections
            if selection['Audit Number'] == int(audit_number)
        )

        # Update employees with current utilization
        filtered_employees = []
        for emp in employees:
            emp_id = int(emp['BankID'])
            emp_utilization = st.session_state.utilization.get(emp_id, 0)
            emp['Utilization'] = emp_utilization
            emp['Utilization Percent'] = f"{(emp_utilization / 250) * 100:.2f}%"

            # Check if employee is overutilized
            if emp_utilization >= 250:
                continue

            # Map phase number to letter
            scheduling_phase = str(emp['SchedulingPhase'])
            phase_letter = phase_mapping.get(scheduling_phase, '')
            if not phase_letter:
                continue  # Invalid phase

            # Check if employee is available for this phase
            availability_phases = emp['AuditPhaseAvailability'].split(',')
            availability_phases = [phase.strip() for phase in availability_phases]
            if phase_letter not in availability_phases:
                continue  # Employee not available for this phase

            # Add selected flag
            if emp_id in selected_emp_ids:
                emp['selected'] = True
            else:
                emp['selected'] = False

            # Add employee to the list
            emp['Phase'] = scheduling_phase  # Include phase in employee data
            filtered_employees.append(emp)

        # Sort the filtered employees by SimilarityScore in descending order
        filtered_employees.sort(key=lambda x: x.get('SimilarityScore', 0), reverse=True)

        total_employees = len(filtered_employees)
        total_pages = max(1, math.ceil(total_employees / per_page))
        st.session_state.total_pages = total_pages

        # Pagination logic
        start = (st.session_state.page - 1) * per_page
        end = start + per_page
        paginated_employees = filtered_employees[start:end]
        return paginated_employees

    paginated_employees = get_paginated_employees()

    if not paginated_employees:
        st.write("No employees available for selection.")
        return

    # Display employees in a table
    def display_employees():
        selected_indices = []
        roles = []
        st.write('---')
        # Table headers
        header_cols = st.columns([1, 1, 1, 2, 2, 1, 1, 2, 1, 1, 1])
        headers = ['Select', 'Phase', 'Bank ID', 'Full Name', 'Job Title', 'Country', 'City', 'Availability', 'Similarity Score', 'Role', 'Utilization']
        for col, header in zip(header_cols, headers):
            col.markdown(f"**{header}**")

        # Table rows
        for idx, emp in enumerate(paginated_employees):
            cols = st.columns([1, 1, 1, 2, 2, 1, 1, 2, 1, 1, 1])
            with cols[0]:
                if emp['selected']:
                    st.checkbox('', value=True, key=f"select_{audit_number}_{idx}", disabled=True)
                else:
                    selected = st.checkbox('', key=f"select_{audit_number}_{idx}")
                    if selected:
                        selected_indices.append(idx)
            with cols[1]:
                st.write(emp['Phase'])
            with cols[2]:
                st.write(emp['BankID'])
            with cols[3]:
                st.write(emp['FullName'])
            with cols[4]:
                st.write(emp['JobTitle'])
            with cols[5]:
                st.write(emp['CountryName'])
            with cols[6]:
                st.write(emp['LocationCity'])
            with cols[7]:
                st.write(f"{emp['AvailabilityFROM']} - {emp['AvailabilityTO']}")
            with cols[8]:
                st.write(emp['SimilarityScore'])
            with cols[9]:
                if emp['selected']:
                    st.selectbox('', ['Team Manager', 'Team Leader', 'Team Member'], key=f"role_{audit_number}_{idx}", disabled=True)
                else:
                    role = st.selectbox('', ['Team Manager', 'Team Leader', 'Team Member'], key=f"role_{audit_number}_{idx}")
                    roles.append((idx, role))
            with cols[10]:
                st.write(emp['Utilization Percent'])

        return selected_indices, dict(roles)

    selected_indices, roles = display_employees()
    st.write('---')

    # Combined Buttons and Pagination Controls
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button('Submit'):
            # Process form submission
            project_days = 30
            for idx in selected_indices:
                emp = paginated_employees[idx]
                emp_id_int = int(emp['BankID'])
                role = roles.get(idx, 'Team Member')
                st.session_state.utilization[emp_id_int] += project_days  # Update utilization

                # Store the selection in session state
                st.session_state.selections.append({
                    'Audit Number': int(audit_number),
                    'Audit Title': str(audit_title),
                    'SchedulingPhase': str(emp['Phase']),
                    'BankID': emp_id_int,
                    'Role': str(role),
                    'Utilization': int(st.session_state.utilization[emp_id_int])
                })
            # st.experimental_rerun() is not needed; the app will update automatically
            # Reset page to 1 after submission
            st.session_state.page = 1
            # Refresh the app by calling main_app()
            main_app()
            return

    with col2:
        # Pagination Controls
        prev_disabled = st.session_state.page <= 1
        next_disabled = st.session_state.page >= st.session_state.total_pages

        prev_col, page_col, next_col = st.columns([1, 2, 1])
        with prev_col:
            if st.button('Previous', disabled=prev_disabled):
                st.session_state.page -= 1
                # Refresh the app by calling main_app()
                main_app()
                return
        with page_col:
            st.markdown(f"<div style='text-align: center;'>Page {st.session_state.page} of {st.session_state.total_pages}</div>", unsafe_allow_html=True)
        with next_col:
            if st.button('Next', disabled=next_disabled):
                st.session_state.page += 1
                # Refresh the app by calling main_app()
                main_app()
                return

    with col3:
        if any(selection['Audit Number'] == int(audit_number) for selection in st.session_state.selections):
            if st.button('Download Scheduled Employees'):
                download_schedule()
            if st.button('Clear Selections'):
                clear_selections()
                # Refresh the app by calling main_app()
                main_app()
                return

# Function to download scheduled employees
def download_schedule():
    selections_df = pd.DataFrame(st.session_state.selections)

    # Merge with employee data to get additional details
    employee_details = data[['BankID', 'FullName', 'JobTitle', 'CountryName', 'LocationCity']].drop_duplicates()
    # Ensure BankID is of type int for merging
    employee_details['BankID'] = employee_details['BankID'].astype(int)

    merged_df = selections_df.merge(employee_details, left_on='BankID', right_on='BankID', how='left')

    # Rearrange columns
    merged_df = merged_df[
        ['Audit Number', 'Audit Title', 'SchedulingPhase', 'BankID', 'FullName', 'JobTitle', 'CountryName', 'LocationCity', 'Role', 'Utilization']
    ]

    # Sort by Audit Number and BankID for better readability
    merged_df.sort_values(['Audit Number', 'BankID'], inplace=True)

    # Create an in-memory CSV file
    csv = merged_df.to_csv(index=False).encode()

    st.download_button(
        label="Download Scheduled Employees",
        data=csv,
        file_name='scheduled_employees.csv',
        mime='text/csv',
    )

# Function to clear selections for the current audit
def clear_selections():
    # Filter out selections for the current audit
    st.session_state.selections = [
        selection for selection in st.session_state.selections
        if selection['Audit Number'] != int(st.session_state.current_audit)
    ]

    # Reset utilization for employees in the current audit
    # Get employee IDs for the current audit
    project_data = data[data['Audit Number'] == int(st.session_state.current_audit)]
    emp_ids_in_audit = project_data['BankID'].astype(int).unique()

    # Subtract project days from utilization for these employees
    project_days = 30
    for emp_id in emp_ids_in_audit:
        emp_id_int = int(emp_id)
        if st.session_state.utilization.get(emp_id_int, 0) >= project_days:
            st.session_state.utilization[emp_id_int] -= project_days
        else:
            st.session_state.utilization[emp_id_int] = 0

# Run the app
if st.session_state.logged_in:
    main_app()
else:
    login()
