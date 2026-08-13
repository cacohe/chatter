"""Tests for API exception handlers."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.exception_handlers import register_exception_handlers
from domain.exceptions import BusinessException


class TestRegisterExceptionHandlers:
    @pytest.fixture
    def app(self):
        return FastAPI()

    @pytest.fixture
    def request_obj(self):
        return Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/test",
                "headers": [],
                "query_string": b"",
            },
            receive=AsyncMock(),
        )

    def test_register(self, app):
        assert register_exception_handlers(app) is None

    @pytest.mark.asyncio
    async def test_business_exception(self, app, request_obj):
        register_exception_handlers(app)
        handler = app.exception_handlers[BusinessException]
        response = await handler(request_obj, BusinessException("bad", status_code=400))
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_global_exception(self, app, request_obj):
        register_exception_handlers(app)
        handler = app.exception_handlers[Exception]
        response = await handler(request_obj, Exception("boom"))
        assert response.status_code == 500
