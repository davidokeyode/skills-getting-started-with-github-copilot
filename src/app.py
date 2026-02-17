"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "swimming": {
        "name": "Swimming",
        "description": "Join our swimming club and improve your technique",
        "schedule": "Monday and Wednesday, 6-7 PM",
        "participants": []
    },
    "chess": {
        "name": "Chess Club",
        "description": "Learn and play chess with other students",
        "schedule": "Tuesday and Thursday, 4-5 PM",
        "participants": []
    },
    "painting": {
        "name": "Painting",
        "description": "Express yourself through painting",
        "schedule": "Friday, 3-5 PM",
        "participants": []
    },
    "basketball": {
        "name": "Basketball",
        "description": "Play basketball and improve your skills on the court",
        "schedule": "Tuesday and Thursday, 5-7 PM",
        "participants": []
    },
    "soccer": {
        "name": "Soccer",
        "description": "Join our soccer team for practice and matches",
        "schedule": "Monday and Friday, 4-6 PM",
        "participants": []
    },
    "theater": {
        "name": "Theater",
        "description": "Participate in drama and theater performances",
        "schedule": "Wednesday, 6-8 PM",
        "participants": []
    },
    "photography": {
        "name": "Photography",
        "description": "Learn photography techniques and capture stunning images",
        "schedule": "Saturday, 10 AM-12 PM",
        "participants": []
    },
    "debate": {
        "name": "Debate Club",
        "description": "Develop critical thinking and public speaking skills",
        "schedule": "Thursday, 5-6:30 PM",
        "participants": []
    },
    "robotics": {
        "name": "Robotics",
        "description": "Build and program robots in our engineering lab",
        "schedule": "Friday, 4-6 PM",
        "participants": []
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}
