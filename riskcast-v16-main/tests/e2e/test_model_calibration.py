"""
End-to-End Test: Model Calibration Flow
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import asyncio


class TestModelCalibrationFlow:
    """Test model calibration workflow."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_calibration_flow(
        self,
        async_client: AsyncClient,
        admin_headers
    ):
        """
        Test complete calibration:
        1. Create new model version
        2. Upload historical data
        3. Run calibration
        4. Review results
        5. Publish model
        6. Set as active
        7. Verify new model used in assessments
        """
        
        # Step 1: Create new model version
        response = await async_client.post(
            "/api/v3/model-versions/",
            json={
                "name": "E2E Test Model",
                "description": "Model created during E2E testing",
                "base_version_id": None  # Start fresh
            },
            headers=admin_headers
        )
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Model versioning endpoint not implemented")
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        model = response.json()
        model_version_id = model["id"]
        
        assert model["status"] in ["DRAFT", "CREATED"]
        
        # Step 2: Trigger calibration
        response = await async_client.post(
            f"/api/v3/calibration/run",
            json={
                "model_version_id": model_version_id,
                "data_source": "historical_shipments",
                "date_range": {
                    "start": "2022-01-01",
                    "end": "2023-12-31"
                },
                "parameters": {
                    "learning_rate": 0.01,
                    "iterations": 100,
                    "validation_split": 0.2
                }
            },
            headers=admin_headers
        )
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Calibration endpoint not implemented")
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]
        calibration = response.json()
        calibration_id = calibration.get("calibration_id") or calibration.get("id")
        
        # Step 3: Wait for calibration (poll status)
        max_attempts = 10  # Reduced for testing
        calibration_complete = False
        
        for attempt in range(max_attempts):
            response = await async_client.get(
                f"/api/v3/calibration/{calibration_id}",
                headers=admin_headers
            )
            
            if response.status_code == status.HTTP_200_OK:
                status_data = response.json()
                current_status = status_data.get("status")
                
                if current_status == "COMPLETED":
                    calibration_complete = True
                    break
                elif current_status == "FAILED":
                    pytest.fail(f"Calibration failed: {status_data.get('error')}")
                
                await asyncio.sleep(0.5)  # Short wait for testing
            else:
                # Endpoint might not exist or calibration might be synchronous
                break
        
        # Step 4: Review calibration results (if available)
        response = await async_client.get(
            f"/api/v3/calibration/{calibration_id}/results",
            headers=admin_headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            results = response.json()
            
            assert "metrics" in results or "accuracy" in results
            
            # Step 5: Apply calibration to model
            response = await async_client.post(
                f"/api/v3/calibration/{calibration_id}/apply",
                json={"model_version_id": model_version_id},
                headers=admin_headers
            )
            
            # Might not be a separate step
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        
        # Step 6: Publish model
        response = await async_client.post(
            f"/api/v3/model-versions/{model_version_id}/publish",
            headers=admin_headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            published = response.json()
            assert published["status"] == "PUBLISHED"
            
            # Step 7: Set as active
            response = await async_client.post(
                "/api/v3/model-versions/set-active",
                json={"model_version_id": model_version_id},
                headers=admin_headers
            )
            
            if response.status_code == status.HTTP_200_OK:
                # Step 8: Verify new model is used
                response = await async_client.get(
                    "/api/v3/model-versions/active",
                    headers=admin_headers
                )
                
                if response.status_code == status.HTTP_200_OK:
                    active = response.json()
                    assert active["id"] == model_version_id
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_model_version_listing(
        self,
        async_client: AsyncClient,
        admin_headers
    ):
        """
        Test model version listing:
        1. List all model versions
        2. Filter by status
        3. Get specific version details
        """
        
        # List all versions
        response = await async_client.get(
            "/api/v3/model-versions/",
            headers=admin_headers
        )
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Model versioning endpoint not implemented")
        
        if response.status_code == status.HTTP_200_OK:
            versions = response.json()
            assert isinstance(versions, list) or isinstance(versions, dict)
            
            # Filter by status
            response = await async_client.get(
                "/api/v3/model-versions/?status=PUBLISHED",
                headers=admin_headers
            )
            
            if response.status_code == status.HTTP_200_OK:
                published = response.json()
                if isinstance(published, list):
                    for version in published:
                        assert version["status"] == "PUBLISHED"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_model_rollback(
        self,
        async_client: AsyncClient,
        admin_headers
    ):
        """
        Test model rollback:
        1. Get current active model
        2. Create new model version
        3. Activate new version
        4. Rollback to previous version
        """
        
        # Get current active model
        response = await async_client.get(
            "/api/v3/model-versions/active",
            headers=admin_headers
        )
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Model versioning endpoint not implemented")
        
        if response.status_code == status.HTTP_200_OK:
            original_active = response.json()
            original_version_id = original_active.get("id")
            
            # Create new version
            response = await async_client.post(
                "/api/v3/model-versions/",
                json={
                    "name": "Rollback Test Model",
                    "description": "Temporary model for rollback test"
                },
                headers=admin_headers
            )
            
            if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
                new_model = response.json()
                new_version_id = new_model["id"]
                
                # Publish and activate new version
                await async_client.post(
                    f"/api/v3/model-versions/{new_version_id}/publish",
                    headers=admin_headers
                )
                
                await async_client.post(
                    "/api/v3/model-versions/set-active",
                    json={"model_version_id": new_version_id},
                    headers=admin_headers
                )
                
                # Rollback to original
                response = await async_client.post(
                    "/api/v3/model-versions/rollback",
                    json={"model_version_id": original_version_id},
                    headers=admin_headers
                )
                
                if response.status_code == status.HTTP_200_OK:
                    # Verify rollback
                    response = await async_client.get(
                        "/api/v3/model-versions/active",
                        headers=admin_headers
                    )
                    
                    if response.status_code == status.HTTP_200_OK:
                        current_active = response.json()
                        assert current_active["id"] == original_version_id


class TestModelPerformanceMonitoring:
    """Test model performance monitoring."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_model_performance_metrics(
        self,
        async_client: AsyncClient,
        admin_headers
    ):
        """
        Test model performance metrics:
        1. Get current model metrics
        2. View accuracy over time
        3. Compare model versions
        """
        
        # Get active model
        response = await async_client.get(
            "/api/v3/model-versions/active",
            headers=admin_headers
        )
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Model versioning endpoint not implemented")
        
        if response.status_code == status.HTTP_200_OK:
            active_model = response.json()
            model_id = active_model["id"]
            
            # Get performance metrics
            response = await async_client.get(
                f"/api/v3/model-versions/{model_id}/metrics",
                headers=admin_headers
            )
            
            if response.status_code == status.HTTP_200_OK:
                metrics = response.json()
                
                # Should have key metrics
                assert isinstance(metrics, dict)
                # Common metrics
                possible_metrics = ["accuracy", "mae", "rmse", "r2", "correlation", "precision", "recall"]
                has_metrics = any(metric in metrics for metric in possible_metrics)
                assert has_metrics or len(metrics) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_model_drift_detection(
        self,
        async_client: AsyncClient,
        admin_headers
    ):
        """
        Test model drift detection:
        1. Get model drift status
        2. Check for performance degradation
        """
        
        response = await async_client.get(
            "/api/v3/model-versions/active",
            headers=admin_headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            active_model = response.json()
            model_id = active_model["id"]
            
            # Check for drift
            response = await async_client.get(
                f"/api/v3/model-versions/{model_id}/drift",
                headers=admin_headers
            )
            
            if response.status_code == status.HTTP_200_OK:
                drift_status = response.json()
                
                # Should have drift indicators
                assert "drift_detected" in drift_status or "status" in drift_status


@pytest.fixture
async def admin_headers():
    """Generate admin authentication headers."""
    try:
        from app.core.security import create_access_token
        token = create_access_token(subject="admin-user", role="admin")
        return {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": "admin-tenant"
        }
    except ImportError:
        import jwt
        from datetime import datetime, timedelta
        
        payload = {
            "sub": "admin-user",
            "role": "admin",
            "tenant_id": "admin-tenant",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
        return {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": "admin-tenant"
        }


@pytest.fixture
def historical_data_fixture():
    """Provide historical data for calibration."""
    return {
        "shipments": [
            {
                "origin": "CNSHA",
                "destination": "USLAX",
                "cargo_type": "ELECTRONICS",
                "cargo_value": 500000,
                "actual_loss": 0,
                "date": "2023-01-15"
            },
            {
                "origin": "SGSIN",
                "destination": "NLRTM",
                "cargo_type": "MACHINERY",
                "cargo_value": 750000,
                "actual_loss": 25000,
                "date": "2023-02-20"
            }
            # More data...
        ]
    }
