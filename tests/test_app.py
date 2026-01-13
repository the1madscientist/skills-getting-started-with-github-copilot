"""
Tests for the High School Management System API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state after each test"""
    # Store original state
    original_activities = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state
    for name, activity in original_activities.items():
        activities[name]["participants"] = activity["participants"].copy()


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that all expected activities are present
        expected_activities = [
            "Soccer Team", "Basketball Club", "Drama Club",
            "Art Studio", "Debate Team", "Science Olympiad",
            "Chess Club", "Programming Class", "Gym Class"
        ]
        for activity_name in expected_activities:
            assert activity_name in data
    
    def test_activity_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check structure of first activity
        soccer = data["Soccer Team"]
        assert "description" in soccer
        assert "schedule" in soccer
        assert "max_participants" in soccer
        assert "participants" in soccer
        assert isinstance(soccer["participants"], list)


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant_success(self, client, reset_activities):
        """Test successfully signing up a new participant"""
        response = client.post(
            "/activities/Soccer Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Soccer Team"]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client, reset_activities):
        """Test that signing up a duplicate participant fails"""
        email = "alex@mergington.edu"  # Already in Soccer Team
        response = client.post(
            f"/activities/Soccer Team/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_with_url_encoded_activity_name(self, client, reset_activities):
        """Test signup with URL-encoded activity name"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=newcoder@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newcoder@mergington.edu" in activities_data["Programming Class"]["participants"]


class TestDeleteParticipantEndpoint:
    """Tests for the DELETE /activities/{activity_name}/participant endpoint"""
    
    def test_delete_participant_success(self, client, reset_activities):
        """Test successfully removing a participant"""
        email = "alex@mergington.edu"
        response = client.delete(
            f"/activities/Soccer Team/participant?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Soccer Team"]["participants"]
    
    def test_delete_nonexistent_participant_fails(self, client, reset_activities):
        """Test that removing non-registered participant fails"""
        response = client.delete(
            "/activities/Soccer Team/participant?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()
    
    def test_delete_from_nonexistent_activity_fails(self, client, reset_activities):
        """Test that deleting from nonexistent activity fails"""
        response = client.delete(
            "/activities/Nonexistent Activity/participant?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_delete_with_url_encoded_activity_name(self, client, reset_activities):
        """Test delete with URL-encoded activity name"""
        email = "emma@mergington.edu"
        response = client.delete(
            f"/activities/Programming%20Class/participant?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Programming Class"]["participants"]


class TestEndToEndWorkflow:
    """Integration tests for complete workflows"""
    
    def test_signup_and_delete_workflow(self, client, reset_activities):
        """Test complete workflow of signing up and then deleting a participant"""
        email = "testworkflow@mergington.edu"
        activity = "Chess Club"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
        
        # Delete
        delete_response = client.delete(
            f"/activities/{activity}/participant?email={email}"
        )
        assert delete_response.status_code == 200
        
        # Verify deletion
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity]["participants"]
    
    def test_multiple_signups_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        email = "multisport@mergington.edu"
        
        # Sign up for Soccer
        response1 = client.post(
            f"/activities/Soccer Team/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for Basketball
        response2 = client.post(
            f"/activities/Basketball Club/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Soccer Team"]["participants"]
        assert email in activities_data["Basketball Club"]["participants"]
