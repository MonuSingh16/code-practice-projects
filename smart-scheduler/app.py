from flask import Flask, request, jsonify, send_file
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack
from sklearn.ensemble import RandomForestClassifier
from datetime import timedelta
import matplotlib.pyplot as plt
import io

app = Flask(__name__)

# Sample data (replace with your actual data)
# Sample data (same as before)
person_data = {
    'PersonID': [1, 2, 3, 4, 5],
    'Skills': ['Python, ML, Data Science', 'Java, Backend, Microservices', 'Python, AI, Deep Learning', 'JavaScript, Frontend, React', 'SQL, Database, ETL'],
    'PastExperience': ['E-commerce, Healthcare', 'Finance, Banking', 'Healthcare, Robotics', 'E-commerce, Social Media', 'Banking, Retail']
}
df_persons = pd.DataFrame(person_data)

leave_data = {
    'PersonID': [1, 2, 3, 4, 5],
    'LeaveStart': ['2024-12-20', '2024-12-25', '2024-12-15', '2024-12-10', '2024-12-05'],
    'LeaveEnd': ['2024-12-30', '2025-01-05', '2024-12-20', '2024-12-15', '2024-12-10']
}
df_leaves = pd.DataFrame(leave_data)
df_leaves['LeaveStart'] = pd.to_datetime(df_leaves['LeaveStart'])
df_leaves['LeaveEnd'] = pd.to_datetime(df_leaves['LeaveEnd'])

project_data = {
    'ProjectID': [101, 102, 103, 104, 105],
    'RequiredSkills': ['Python, Data Science', 'Java, Microservices', 'AI, Deep Learning', 'JavaScript, React', 'SQL, ETL'],
    'StartDate': ['2024-12-10', '2024-12-20', '2024-12-25', '2024-12-15', '2024-12-05'],
    'Mandays': [10, 15, 20, 12, 8]
}
df_projects = pd.DataFrame(project_data)
df_projects['StartDate'] = pd.to_datetime(df_projects['StartDate'])
df_projects['EndDate'] = df_projects['StartDate'] + pd.to_timedelta(df_projects['Mandays'], unit='D')
# Vectorizing skills and past experience
vectorizer = TfidfVectorizer()
df_persons['CombinedFeatures'] = df_persons['Skills'] + " " + df_persons['PastExperience']
df_projects['CombinedFeatures'] = df_projects['RequiredSkills'] + " " + df_projects['ProjectID'].astype(str)
vectorizer.fit(pd.concat([df_persons['CombinedFeatures'], df_projects['CombinedFeatures']]))
X_persons = vectorizer.transform(df_persons['CombinedFeatures'])
X_projects = vectorizer.transform(df_projects['CombinedFeatures'])

# Train a RandomForest model
pairs = []
labels = []
for project_id in df_projects['ProjectID']:
    project_idx = df_projects[df_projects['ProjectID'] == project_id].index[0]
    project_features = X_projects[project_idx]
    
    for person_id in df_persons['PersonID']:
        person_idx = df_persons[df_persons['PersonID'] == person_id].index[0]
        person_features = X_persons[person_idx]
        combined_features = hstack([person_features, project_features])
        similarity_score = (combined_features * combined_features.T).toarray()[0][0]
        pairs.append(combined_features.toarray())
        labels.append(1 if similarity_score > 0.5 else 0)

X = np.array(pairs).reshape(len(pairs), -1)
y = np.array(labels)
clf = RandomForestClassifier()
clf.fit(X, y)

# Utility functions
def is_person_available(person_id, project_start, project_end):
    leave = df_leaves[df_leaves['PersonID'] == person_id]
    if not leave.empty:
        leave_start = leave['LeaveStart'].iloc[0]
        leave_end = leave['LeaveEnd'].iloc[0]
        if (project_start <= leave_end) and (project_end >= leave_start):
            return False
    return True

def get_available_persons_for_project(project_id):
    project = df_projects[df_projects['ProjectID'] == project_id]
    project_start = project['StartDate'].iloc[0]
    project_end = project['EndDate'].iloc[0]
    
    available_persons = []
    for person_id in df_persons['PersonID']:
        if is_person_available(person_id, project_start, project_end):
            available_persons.append(person_id)
    
    return available_persons

def recommend_person_for_project(project_id):
    project_idx = df_projects[df_projects['ProjectID'] == project_id].index[0]
    project_features = X_projects[project_idx]
    
    scores = []
    available_persons = get_available_persons_for_project(project_id)
    
    for person_id in available_persons:
        person_idx = df_persons[df_persons['PersonID'] == person_id].index[0]
        person_features = X_persons[person_idx]
        combined_features = hstack([person_features, project_features]).toarray().reshape(1, -1)
        score = clf.predict_proba(combined_features)[0][1]
        scores.append((person_id, score))
    
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores

def generate_gantt_chart_for_projects(project_recommendations):
    plt.figure(figsize=(12, len(project_recommendations) * 2))
    colors = ['green', 'red', 'blue', 'orange', 'purple']

    for i, (project_id, recommendations) in enumerate(project_recommendations.items()):
        project = df_projects[df_projects['ProjectID'] == project_id]
        start_date = project['StartDate'].iloc[0]
        end_date = project['EndDate'].iloc[0]
        date_range = pd.date_range(start=start_date, end=end_date)

        for j, (person_id, _) in enumerate(recommendations):
            leave = df_leaves[df_leaves['PersonID'] == person_id]
            available_days = []
            leave_days = []
            for date in date_range:
                if not leave.empty and leave['LeaveStart'].iloc[0] <= date <= leave['LeaveEnd'].iloc[0]:
                    leave_days.append(date)
                else:
                    available_days.append(date)
            
            plt.plot(available_days, [i + j * 0.1] * len(available_days), 's', color=colors[j % len(colors)], label=f'Person {person_id} Available' if i == 0 and j == 0 else "")
            plt.plot(leave_days, [i + j * 0.1] * len(leave_days), 's', color='red', label='On Leave' if i == 0 and j == 0 else "")
        
        plt.text(start_date - timedelta(days=2), i, f'Project {project_id}', va='center', ha='right')

    plt.yticks([])
    plt.xticks(rotation=90)
    plt.xlabel("Date")
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

# API endpoint to get recommendations for multiple projects and generate Gantt charts
@app.route("/recommend_projects", methods=["POST"])
def recommend_projects():
    data = request.get_json()
    project_ids = data.get("project_ids")
    if not project_ids:
        return jsonify({"message": "No project IDs provided"}), 400
    
    project_recommendations = {}
    for project_id in project_ids:
        if project_id not in df_projects['ProjectID'].values:
            return jsonify({"message": f"Project {project_id} not found"}), 404
        
        recommendations = recommend_person_for_project(project_id)
        if recommendations:
            project_recommendations[project_id] = recommendations

    if not project_recommendations:
        return jsonify({"message": "No available persons for the provided projects."})

    # Generate Gantt chart image for all projects
    buf = generate_gantt_chart_for_projects(project_recommendations)
    return send_file(buf, mimetype='image/png')

# Running the Flask application
if __name__ == "__main__":
    app.run(port=5000, debug=True)
