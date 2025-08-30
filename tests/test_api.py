from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_recommend_price():
    resp = client.post("/agent/recommend-price", json={
        "stock_level":50,
        "last_price":90.0,
        "competitor_price":100.0,
        "sales_last_week":5
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "new_price_estimate" in data
    assert "explanation" in data
