"""Tests for Triathlon Coach AI API"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.api.main import app


client = TestClient(app)


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_check_endpoint_exists(self):
        """Test that health endpoint exists"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_response_format(self):
        """Test health check response format"""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert isinstance(data["services"], dict)


class TestRoot:
    """Root endpoint tests"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestActivitiesEndpoints:
    """Activity endpoint tests"""
    
    def test_activities_without_strava_client(self):
        """Test activities endpoint without Strava client"""
        response = client.get("/api/activities/latest?limit=5")
        # Will return 503 if Strava not configured
        assert response.status_code in [200, 503]
    
    def test_sync_endpoint(self):
        """Test sync endpoint"""
        response = client.post("/api/activities/sync")
        # Will return 503 if Strava not configured
        assert response.status_code in [200, 503]


class TestAthleteEndpoints:
    """Athlete endpoint tests"""
    
    def test_athlete_endpoint(self):
        """Test athlete endpoint"""
        response = client.get("/api/athlete")
        # Will return 503 if Strava not configured
        assert response.status_code in [200, 503]


class TestCoachingEndpoints:
    """Coaching endpoint tests"""
    
    def test_analyze_endpoint(self):
        """Test analyze endpoint"""
        response = client.post("/api/coach/analyze?days_back=7")
        # Will return 503 if services not configured
        assert response.status_code in [200, 503]


class TestModelsEndpoint:
    """Models endpoint tests"""
    
    def test_models_endpoint(self):
        """Test models endpoint"""
        response = client.get("/api/models")
        # Will return 503 if Ollama not running
        assert response.status_code in [200, 503]


class TestErrorHandling:
    """Error handling tests"""
    
    def test_404_not_found(self):
        """Test 404 error handling"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
