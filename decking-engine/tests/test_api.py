from fastapi.testclient import TestClient

from app.main import app


def test_health_route_is_available():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}


def test_predict_decking_accepts_valid_request():
    with TestClient(app) as client:
        response = client.post(
            "/api/predict-decking",
            json={"containerId": "ABCD1234567", "weightKg": 25000, "reefer": True},
        )
        assert response.status_code == 200
        body = response.json()
        assert "placed" in body


def test_predict_decking_rejects_malformed_container_id():
    with TestClient(app) as client:
        response = client.post(
            "/api/predict-decking",
            json={"containerId": "BAD-ID", "weightKg": 25000, "reefer": False},
        )
        assert response.status_code == 422


def test_predict_decking_rejects_non_positive_weight():
    with TestClient(app) as client:
        response = client.post(
            "/api/predict-decking",
            json={"containerId": "ABCD1234567", "weightKg": 0, "reefer": False},
        )
        assert response.status_code == 422


def test_predict_decking_rejects_missing_reefer_flag():
    with TestClient(app) as client:
        response = client.post(
            "/api/predict-decking",
            json={"containerId": "ABCD1234567", "weightKg": 15000},
        )
        assert response.status_code == 422


def test_yard_route_returns_full_grid():
    with TestClient(app) as client:
        response = client.get("/api/yard")
        assert response.status_code == 200
        slots = response.json()["slots"]
        # 3 standard blocks (4x5x5) + 1 reefer block (3x4x5) = 300 + 60
        assert len(slots) == 360


def test_yard_route_uses_camelcase_keys_for_the_react_frontend():
    with TestClient(app) as client:
        placement = client.post(
            "/api/predict-decking",
            json={"containerId": "CMLC0001112", "weightKg": 4000, "reefer": False},
        ).json()
        if not placement["placed"]:
            return  # yard state is shared across tests; skip if this run had no room

        slots = client.get("/api/yard").json()["slots"]
        occupied = next(s for s in slots if s.get("containerId") == "CMLC0001112")
        assert "container_id" not in occupied
        assert "weight_kg" not in occupied
        assert occupied["weightKg"] == 4000


def test_alerts_route_is_available():
    with TestClient(app) as client:
        response = client.get("/api/alerts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_release_slot_reports_not_found_for_unknown_container():
    with TestClient(app) as client:
        response = client.post("/api/release-slot", json={"containerId": "ZZZZ0000000"})
        assert response.status_code == 200
        body = response.json()
        assert body["released"] is False


def test_release_slot_round_trips_a_placed_container():
    with TestClient(app) as client:
        placement = client.post(
            "/api/predict-decking",
            json={"containerId": "RTRT1112223", "weightKg": 4000, "reefer": False},
        ).json()

        release = client.post("/api/release-slot", json={"containerId": "RTRT1112223"}).json()

        if placement["placed"]:
            # released cleanly unless something happened to be seeded on top,
            # which the assigned-tier algorithm avoids by construction here
            assert release["released"] is True
        else:
            assert release["released"] is False


def test_predict_decking_response_includes_penalty_flag():
    with TestClient(app) as client:
        response = client.post(
            "/api/predict-decking",
            json={"containerId": "PNFL0001112", "weightKg": 22000, "reefer": True},
        )
        body = response.json()
        if body["placed"]:
            assert body["penaltyFlag"] in ("HIGH", "MEDIUM", "LOW")


def test_efficiency_index_route_is_available_and_bounded():
    with TestClient(app) as client:
        response = client.get("/api/yard/efficiency-index")
        assert response.status_code == 200
        body = response.json()
        assert 0.0 <= body["efficiencyIndex"] <= 100.0
        assert body["occupiedSlots"] >= 0


def test_vessel_load_route_accepts_valid_request():
    with TestClient(app) as client:
        response = client.post(
            "/api/vessel/load",
            json={"containerId": "VSSL0001112", "weightKg": 15000, "bay": 1, "row": 1, "tier": 1},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["loaded"] is True
        assert body["bay"] == 1


def test_vessel_load_route_rejects_double_booking_the_same_slot():
    with TestClient(app) as client:
        client.post(
            "/api/vessel/load",
            json={"containerId": "VSSL0002223", "weightKg": 15000, "bay": 2, "row": 1, "tier": 1},
        )
        second = client.post(
            "/api/vessel/load",
            json={"containerId": "VSSL0003334", "weightKg": 15000, "bay": 2, "row": 1, "tier": 1},
        )
        assert second.json()["loaded"] is False


def test_vessel_route_returns_full_grid():
    with TestClient(app) as client:
        response = client.get("/api/vessel")
        assert response.status_code == 200
        slots = response.json()["slots"]
        # 6 bays x 4 rows x 4 tiers
        assert len(slots) == 96


def test_model_metrics_route_exposes_evaluation_results():
    with TestClient(app) as client:
        response = client.get("/api/model/metrics")
        assert response.status_code == 200
        body = response.json()

        assert body["dataSource"] in ("synthetic", "history")
        assert body["maeDays"] > 0
        assert body["baselineMaeDays"] > 0
        assert body["beatsBaseline"] is True
        assert set(body["featureImportances"]) == {"weight_kg", "reefer", "tier", "is_heavy"}
        assert body["selectedModel"] in ("linear_regression", "random_forest")
        assert set(body["modelSelection"]) == {"linear_regression", "random_forest"}


def test_model_retrain_route_returns_fresh_metrics():
    with TestClient(app) as client:
        response = client.post("/api/model/retrain")
        assert response.status_code == 200
        body = response.json()
        # no gateway reachable from the test process, so it must fall back cleanly
        assert body["dataSource"] == "synthetic"
        assert body["provenance"]["source"] == "synthetic"
        assert "fallback_reason" in body["provenance"]


def test_vessel_stability_route_reflects_loaded_weight():
    with TestClient(app) as client:
        client.post(
            "/api/vessel/load",
            json={"containerId": "VSSL0004445", "weightKg": 25000, "bay": 3, "row": 1, "tier": 3},
        )
        response = client.get("/api/vessel/stability")
        assert response.status_code == 200
        body = response.json()
        assert body["totalDeckWeight"] >= 25000
        assert any(v["containerId"] == "VSSL0004445" for v in body["violations"])
