import pandas as pd
import random
from datetime import datetime, timedelta

# Parameters
num_audits = 10
resources_per_audit = 30
phases = [1, 2, 3, 4]  # Scheduling Phases
audit_numbers = range(1001, 1001 + num_audits)
bank_ids = range(2001, 2001 + num_audits * resources_per_audit)

# Sample Data
first_names = ['John', 'Jane', 'Bob', 'Alice', 'Michael', 'Linda', 'William', 'Barbara', 'James', 'Patricia', 'Robert', 'Jennifer', 'Mary', 'David', 'Richard', 'Susan', 'Joseph', 'Thomas', 'Charles', 'Lisa']
last_names = ['Doe', 'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Garcia', 'Rodriguez', 'Wilson', 'Martinez', 'Anderson', 'Taylor', 'Thomas', 'Hernandez', 'Moore', 'Martin', 'Jackson', 'Thompson']
job_titles = ['Auditor', 'Senior Auditor', 'Audit Manager']
countries = ['USA', 'UK', 'Canada', 'Australia', 'India', 'Germany', 'Japan', 'Brazil', 'France', 'South Africa']
cities = ['New York', 'London', 'Toronto', 'Sydney', 'Mumbai', 'Berlin', 'Tokyo', 'Sao Paulo', 'Paris', 'Cape Town']
team_names = ['Team A', 'Team B', 'Team C', 'Team D', 'Team E', 'Team F', 'Team G', 'Team H', 'Team I', 'Team J']
phase_letters = {1: 'P', 2: 'F', 3: 'R', 4: 'C'}
Function = ['Operations', 'Technology', 'Banking', 'Helpdesk']

data_rows = []

# Generate data
current_bank_id = 2001
for audit_number in audit_numbers:
    audit_title = f"Audit of Company {audit_number}"
    audit_team = team_names[(audit_number - 1001) % len(team_names)]
    for phase in phases:
        for _ in range(resources_per_audit // len(phases)):
            full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            job_title = random.choice(job_titles)
            availability_from = datetime(2023, random.randint(1, 12), random.randint(1, 28))
            availability_to = availability_from + timedelta(days=random.randint(30, 180))
            unavailable_dates = ';'.join([
                (availability_from + timedelta(days=random.randint(0, (availability_to - availability_from).days))).strftime('%Y-%m-%d')
                for _ in range(random.randint(0, 2))
            ])
            country = random.choice(countries)
            city = random.choice(cities)
            audit_phase_availability = ','.join(random.sample(['P', 'F', 'R', 'C'], random.randint(1, 4)))
            similarity_score = round(random.uniform(0.75, 0.95), 2)
            
            data_rows.append({
                'Audit Number': audit_number,
                'Audit Title': audit_title,
                'SchedulingPhase': phase,
                'BankID': current_bank_id,
                'FullName': full_name,
                'JobTitle': job_title,
                'AvailabilityFROM': availability_from.strftime('%Y-%m-%d'),
                'AvailabilityTO': availability_to.strftime('%Y-%m-%d'),
                'UnavailableDates': unavailable_dates,
                'CountryName': country,
                'LocationCity': city,
                'AuditTeamName': audit_team,
                'AuditPhaseAvailability': audit_phase_availability,
                'SimilarityScore': similarity_score
            })
            
            current_bank_id += 1

# Create DataFrame and save to CSV
df = pd.DataFrame(data_rows)
df.to_csv('data/data.csv', index=False)

print("data.csv has been generated with", len(df), "rows.")
