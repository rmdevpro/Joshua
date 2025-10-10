#!/usr/bin/env python3
"""
Integration tests for deployed SessionManager API
Tests against the actual deployed service on Irina
"""

import requests
import json
import uuid
import time
from datetime import datetime

# Configuration for deployed service on Irina
BASE_URL = "http://192.168.1.210:8000"
API_V1 = f"{BASE_URL}/api/v1"

def test_health_check():
    """Test health endpoint is responding"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "SessionManager"
    print("✓ Health check passed")

def test_metrics_endpoint():
    """Test metrics endpoint is available"""
    response = requests.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "sessions_total" in data
    assert "cache_hits" in data
    assert "cache_misses" in data
    print("✓ Metrics endpoint passed")

def test_create_session():
    """Test creating a new session"""
    user_id = f"test-user-{uuid.uuid4()}"
    response = requests.post(
        f"{API_V1}/sessions",
        json={"user_id": user_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["version"] == 1
    assert data["state"] == "active"
    assert data["owner_id"] == user_id
    print(f"✓ Session creation passed (ID: {data['session_id'][:8]}...)")
    return data["session_id"]

def test_get_session(session_id=None):
    """Test retrieving a session by ID"""
    if not session_id:
        session_id = test_create_session()

    response = requests.get(f"{API_V1}/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["state"] == "active"
    print(f"✓ Session retrieval passed")

def test_session_not_found():
    """Test 404 for non-existent session"""
    response = requests.get(f"{API_V1}/sessions/test-404")
    assert response.status_code == 404
    print("✓ Session not found (404) test passed")

def test_update_session():
    """Test updating a session with version control"""
    session_id = test_create_session()

    # Update with correct version
    response = requests.patch(
        f"{API_V1}/sessions/{session_id}",
        params={"expected_version": 1},
        json={"status": "updated"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 2
    assert data["updated"] == True
    print("✓ Session update with version control passed")

def test_version_conflict():
    """Test version conflict detection"""
    session_id = test_create_session()

    # Try update with wrong version
    response = requests.patch(
        f"{API_V1}/sessions/{session_id}",
        params={"expected_version": 0},
        json={"status": "should_fail"}
    )
    assert response.status_code == 409
    print("✓ Version conflict detection passed")

def test_add_participant():
    """Test adding a MAD participant to session"""
    session_id = test_create_session()

    response = requests.post(
        f"{API_V1}/sessions/{session_id}/participants",
        params={"mad_name": "test-mad-worker"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["participant"] == "test-mad-worker"
    assert "lease_ttl" in data
    print("✓ Add participant passed")

def test_suspend_session():
    """Test suspending a session to dormant state"""
    session_id = test_create_session()

    response = requests.post(f"{API_V1}/sessions/{session_id}/suspend")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["state"] == "dormant"
    print("✓ Session suspension passed")

def test_blue_green_deployment():
    """Test both blue and green deployments are accessible"""
    # Test blue deployment directly
    response = requests.get("http://192.168.1.210:8001/health")
    assert response.status_code == 200
    blue_data = response.json()
    assert blue_data["status"] == "ok"
    print("✓ Blue deployment accessible")

    # Test green deployment directly
    response = requests.get("http://192.168.1.210:8002/health")
    assert response.status_code == 200
    green_data = response.json()
    assert green_data["status"] == "ok"
    print("✓ Green deployment accessible")

    # Test nginx router
    response = requests.get("http://192.168.1.210:8000/health")
    assert response.status_code == 200
    print("✓ Nginx router working")

def run_all_tests():
    """Run all deployment tests"""
    print("\n" + "="*50)
    print("SessionManager Deployment Tests")
    print("="*50 + "\n")

    tests = [
        test_health_check,
        test_metrics_endpoint,
        test_create_session,
        test_get_session,
        test_session_not_found,
        test_update_session,
        test_version_conflict,
        test_add_participant,
        test_suspend_session,
        test_blue_green_deployment
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1

    print("\n" + "="*50)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*50 + "\n")

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)