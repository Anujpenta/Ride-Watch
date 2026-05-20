from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "RideWatch API is running"}

def test_post_location():
    response = client.post("/location", json={
        "driver_id": "test_driver",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "speed": 42.5
    })
    assert response.status_code == 200
    assert response.json()["status"] == "saved"

def test_get_locations():
    response = client.get("/locations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_driver_locations():
    response = client.get("/locations/test_driver?minutes=10")
    assert response.status_code == 200
    data = response.json()
    assert "driver_id" in data
    assert "total_updates" in data

def test_get_anomalies():
    response = client.get("/anomalies/test_driver?minutes=10")
    assert response.status_code == 200
    data = response.json()
    assert "anomalies_found" in data