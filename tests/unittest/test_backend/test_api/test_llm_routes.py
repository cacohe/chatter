"""Tests for llm routes."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.backend.api.deps import get_llm_service
from src.backend.api.routes.llm import llm_router
from src.shared.schemas import llm as llm_schema


class TestLLMRoutes:
    """Tests for LLM routes."""

    @pytest.fixture
    def app(self, mock_llm_service):
        """Create a test FastAPI app."""
        app = FastAPI()
        app.include_router(llm_router)
        app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service."""
        service = Mock()
        service.get_models = AsyncMock(return_value=llm_schema.LLMListResponse(
            models=[llm_schema.LLMInfo(id="gpt-4o", name='gpt', provider='OpenAI'),
                    llm_schema.LLMInfo(id="gpt-3.5-turbo", name='gpt', provider='OpenAI')],
            current_model_id="gpt-4o"
        ))
        service.switch_model = AsyncMock(return_value=llm_schema.ModelSwitchResponse(
            session_id=1,
            active_model_id="gpt-4o",
            success=True
        ))
        return service

    def test_list_models_route_defined(self, client):
        """Test list models route is defined."""
        response = client.get("/api/v1.0/llm/list")
        # Route exists
        assert response.status_code in [200, 500]

    def test_switch_model_route_defined(self, client):
        """Test switch model route is defined."""
        response = client.post("/api/v1.0/llm/switch", json={
            "session_id": 1,
            "model_id": "gpt-4o"
        })
        # Route exists (may fail due to dependencies)
        assert response.status_code in [202, 500, 422]

    def test_list_models_returns_200_on_success(self, app, mock_llm_service):
        """Test list models returns 200 on success."""
        with patch('src.backend.api.routes.llm.get_llm_service', return_value=mock_llm_service):
            client = TestClient(app)
            response = client.get("/api/v1.0/llm/list")
            assert response.status_code == 200

    def test_switch_model_returns_202_on_success(self, app, mock_llm_service):
        """Test switch model returns 202 on success."""
        with patch('src.backend.api.routes.llm.get_llm_service', return_value=mock_llm_service):
            client = TestClient(app)
            response = client.post("/api/v1.0/llm/switch", json={
                "session_id": 1,
                "model_id": "gpt-4o"
            })
            assert response.status_code == 202

    def test_list_models_response_structure(self, app, mock_llm_service):
        """Test list models response has correct structure."""
        with patch('src.backend.api.routes.llm.get_llm_service', return_value=mock_llm_service):
            client = TestClient(app)
            response = client.get("/api/v1.0/llm/list")
            assert response.status_code == 200
            data = response.json()
            assert "models" in data
            assert "current_model_id" in data

    def test_switch_model_response_structure(self, app, mock_llm_service):
        """Test switch model response has correct structure."""
        with patch('src.backend.api.routes.llm.get_llm_service', return_value=mock_llm_service):
            client = TestClient(app)
            response = client.post("/api/v1.0/llm/switch", json={
                "session_id": 1,
                "model_id": "gpt-4o"
            })
            assert response.status_code == 202
            data = response.json()
            assert "session_id" in data
            assert "active_model_id" in data
            assert "success" in data

    def test_llm_router_prefix(self):
        """Test llm router has correct prefix."""
        assert llm_router.prefix == "/api/v1.0/llm"

    def test_list_models_endpoint_has_correct_method(self):
        """Test list models endpoint uses GET method."""
        list_route = [r for r in llm_router.routes if hasattr(r, 'path') and 'list' in r.path]
        assert len(list_route) > 0
        assert 'GET' in list_route[0].methods

    def test_switch_model_endpoint_has_correct_method(self):
        """Test switch model endpoint uses POST method."""
        switch_route = [r for r in llm_router.routes if hasattr(r, 'path') and 'switch' in r.path]
        assert len(switch_route) > 0
        assert switch_route[0].methods == {'POST'}

    def test_switch_model_with_missing_session_id(self, app, mock_llm_service):
        """Test switch model with missing session_id returns validation error."""
        with patch('src.backend.api.routes.llm.get_llm_service', return_value=mock_llm_service):
            client = TestClient(app)
            response = client.post("/api/v1.0/llm/switch", json={
                "model_id": "gpt-4o"
            })
            assert response.status_code == 422

    def test_switch_model_with_missing_model_id(self, app, mock_llm_service):
        """Test switch model with missing model_id returns validation error."""
        with patch('src.backend.api.routes.llm.get_llm_service', return_value=mock_llm_service):
            client = TestClient(app)
            response = client.post("/api/v1.0/llm/switch", json={
                "session_id": 1
            })
            assert response.status_code == 422

    def test_switch_model_with_session_id_zero(self, app, mock_llm_service):
        """Test switch model with session_id=0."""
        with patch('src.backend.api.routes.llm.get_llm_service', return_value=mock_llm_service):
            client = TestClient(app)
            response = client.post("/api/v1.0/llm/switch", json={
                "session_id": 0,
                "model_id": "gpt-4o"
            })
            assert response.status_code in [202, 422]

    def test_switch_model_with_negative_session_id(self, app, mock_llm_service):
        """Test switch model with negative session_id."""
        with patch('src.backend.api.routes.llm.get_llm_service', return_value=mock_llm_service):
            client = TestClient(app)
            response = client.post("/api/v1.0/llm/switch", json={
                "session_id": -1,
                "model_id": "gpt-4o"
            })
            assert response.status_code in [202, 422]

    def test_list_models_with_empty_model_list(self, app, mock_llm_service):
        """Test list models with empty model list."""
        mock_llm_service.get_models = AsyncMock(return_value=llm_schema.LLMListResponse(
            models=[],
            current_model_id="gpt-4o"
        ))
        with patch('src.backend.api.routes.llm.get_llm_service', return_value=mock_llm_service):
            client = TestClient(app)
            response = client.get("/api/v1.0/llm/list")
            assert response.status_code == 200
            data = response.json()
            assert data["models"] == []

    def test_list_models_with_many_models(self, app, mock_llm_service):
        """Test list models with many models."""
        models = [llm_schema.LLMInfo(id=f"model-{i}", name=f'model-{i}', provider='OpenAI') for i in range(100)]
        mock_llm_service.get_models = AsyncMock(return_value=llm_schema.LLMListResponse(
            models=models,
            current_model_id="model-0"
        ))
        with patch('src.backend.api.routes.llm.get_llm_service', return_value=mock_llm_service):
            client = TestClient(app)
            response = client.get("/api/v1.0/llm/list")
            assert response.status_code == 200
            data = response.json()
            assert len(data["models"]) == 100

    def test_switch_model_success_field_is_true(self, app, mock_llm_service):
        """Test switch model response success field is True."""
        with patch('src.backend.api.routes.llm.get_llm_service', return_value=mock_llm_service):
            client = TestClient(app)
            response = client.post("/api/v1.0/llm/switch", json={
                "session_id": 1,
                "model_id": "gpt-4o"
            })
            assert response.status_code == 202
            data = response.json()
            assert data["success"] is True

    def test_llm_router_has_tags(self):
        """Test llm router has tags."""
        assert llm_router.tags == ["Model Management"]
