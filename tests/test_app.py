"""
Tests for the High School Management System API

These tests cover all the endpoints in the application:
- GET / (redirect)
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/participants/{email}
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    for activity in activities.values():
        activity["participants"] = []
    yield


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that we have all expected activities
        expected_activities = [
            "swimming", "chess", "painting", "basketball",
            "soccer", "theater", "photography", "debate", "robotics"
        ]
        assert set(data.keys()) == set(expected_activities)

    def test_activity_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check structure of first activity
        swimming = data["swimming"]
        assert "name" in swimming
        assert "description" in swimming
        assert "schedule" in swimming
        assert "max_participants" in swimming
        assert "participants" in swimming
        assert isinstance(swimming["participants"], list)

    def test_activities_start_empty(self, client):
        """Test that activities start with no participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity in data.values():
            assert len(activity["participants"]) == 0


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/swimming/signup?email=student@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "student@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup adds participant to activity"""
        # Sign up a student
        client.post("/activities/chess/signup?email=alice@mergington.edu")
        
        # Check that participant was added
        response = client.get("/activities")
        data = response.json()
        assert "alice@mergington.edu" in data["chess"]["participants"]

    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signup is rejected"""
        email = "bob@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/painting/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/painting/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/nonexistent/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_activity_full(self, client):
        """Test that signup is rejected when activity is full"""
        # Fill up the painting activity (max 12 participants)
        for i in range(12):
            response = client.post(
                f"/activities/painting/signup?email=student{i}@mergington.edu"
            )
            assert response.status_code == 200
        
        # Try to add one more (should fail)
        response = client.post(
            "/activities/painting/signup?email=student13@mergington.edu"
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"]

    def test_signup_multiple_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multi@mergington.edu"
        
        response1 = client.post(f"/activities/swimming/signup?email={email}")
        response2 = client.post(f"/activities/chess/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Check both activities have the student
        activities_data = client.get("/activities").json()
        assert email in activities_data["swimming"]["participants"]
        assert email in activities_data["chess"]["participants"]


class TestDeleteParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_delete_participant_success(self, client):
        """Test successful removal of a participant"""
        email = "remove@mergington.edu"
        
        # First, sign up the student
        client.post(f"/activities/basketball/signup?email={email}")
        
        # Then remove them
        response = client.delete(f"/activities/basketball/participants/{email}")
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]

    def test_delete_participant_removes_from_list(self, client):
        """Test that delete actually removes participant from activity"""
        email = "delete@mergington.edu"
        
        # Sign up
        client.post(f"/activities/soccer/signup?email={email}")
        
        # Verify they're in the list
        activities_data = client.get("/activities").json()
        assert email in activities_data["soccer"]["participants"]
        
        # Delete
        client.delete(f"/activities/soccer/participants/{email}")
        
        # Verify they're not in the list
        activities_data = client.get("/activities").json()
        assert email not in activities_data["soccer"]["participants"]

    def test_delete_nonexistent_participant(self, client):
        """Test delete for participant not in activity"""
        response = client.delete(
            "/activities/theater/participants/nothere@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_from_nonexistent_activity(self, client):
        """Test delete from non-existent activity"""
        response = client.delete(
            "/activities/fake/participants/student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_delete_one_participant_keeps_others(self, client):
        """Test that deleting one participant doesn't affect others"""
        # Sign up multiple students
        client.post("/activities/debate/signup?email=student1@mergington.edu")
        client.post("/activities/debate/signup?email=student2@mergington.edu")
        client.post("/activities/debate/signup?email=student3@mergington.edu")
        
        # Delete one
        client.delete("/activities/debate/participants/student2@mergington.edu")
        
        # Check that others remain
        activities_data = client.get("/activities").json()
        participants = activities_data["debate"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" not in participants
        assert "student3@mergington.edu" in participants
        assert len(participants) == 2


class TestIntegrationScenarios:
    """Integration tests for complete user workflows"""

    def test_complete_signup_and_delete_workflow(self, client):
        """Test a complete workflow of signup and deletion"""
        email = "workflow@mergington.edu"
        activity = "robotics"
        
        # 1. Initially, activity should be empty
        data = client.get("/activities").json()
        assert len(data[activity]["participants"]) == 0
        
        # 2. Sign up for activity
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # 3. Verify participant is in the list
        data = client.get("/activities").json()
        assert email in data[activity]["participants"]
        assert len(data[activity]["participants"]) == 1
        
        # 4. Remove participant
        response = client.delete(f"/activities/{activity}/participants/{email}")
        assert response.status_code == 200
        
        # 5. Verify participant is removed
        data = client.get("/activities").json()
        assert email not in data[activity]["participants"]
        assert len(data[activity]["participants"]) == 0

    def test_multiple_students_same_activity(self, client):
        """Test multiple students signing up for the same activity"""
        activity = "photography"
        emails = [f"student{i}@mergington.edu" for i in range(5)]
        
        # Sign up all students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all are in the list
        data = client.get("/activities").json()
        participants = data[activity]["participants"]
        assert len(participants) == 5
        for email in emails:
            assert email in participants

    def test_capacity_limits_work_correctly(self, client):
        """Test that capacity limits are enforced correctly"""
        activity = "debate"  # max 12 participants
        
        # Add 12 students (should all succeed)
        for i in range(12):
            response = client.post(
                f"/activities/{activity}/signup?email=student{i}@mergington.edu"
            )
            assert response.status_code == 200
        
        # 13th should fail
        response = client.post(
            f"/activities/{activity}/signup?email=student13@mergington.edu"
        )
        assert response.status_code == 400
        
        # Remove one student
        client.delete(f"/activities/{activity}/participants/student5@mergington.edu")
        
        # Now another student should be able to join
        response = client.post(
            f"/activities/{activity}/signup?email=student14@mergington.edu"
        )
        assert response.status_code == 200
