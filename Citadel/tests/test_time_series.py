from fastapi.testclient import TestClient

from services.time_series.main import app as ts_app


def test_forecast_and_anomaly():
    client = TestClient(ts_app)
    # Provide a small time series of 5 points
    data = [
        {"ds": "2025-01-01", "y": 10},
        {"ds": "2025-01-02", "y": 12},
        {"ds": "2025-01-03", "y": 14},
        {"ds": "2025-01-04", "y": 13},
        {"ds": "2025-01-05", "y": 15},
    ]
    resp = client.post("/forecast", json={"data": data, "horizon": 2})
    assert resp.status_code == 200
    result = resp.json()
    assert "forecast" in result
    assert len(result["forecast"]) >= 7  # 5 history + 2 future
    resp = client.post("/anomaly", json={"data": data, "horizon": 0})
    assert resp.status_code == 200
    anomalies = resp.json()["anomalies"]
    assert len(anomalies) == len(data)