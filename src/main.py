from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
import uvicorn

from src.agent import create_agent_setup
from src.api import router
from src.clients import LLMClientRegistry, get_http_client
from src.clients.http_client import close_http_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build the agent and its clients at startup and reuse them."""
    registry = LLMClientRegistry()
    await registry.register_llm_clients()
    app.state.llm_registry = registry
    app.state.http_client = get_http_client()

    app.state.agent_setups = {
        name: create_agent_setup(llm_model=model)
        for name, model in registry._clients.items()
    }
    try:
        yield
    finally:
        await close_http_client()
        await registry.close_all_clients()


app = FastAPI(title="Deep Agent", version="0.1.0", lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Health Check Endpoint"""
    return {"status": "healthy"}

@app.get("/actuator/health/readiness")
async def readiness_check():
    """Readiness Check Endpoint"""
    return {"status": "ready"}

@app.get("/actuator/health/liveness")
async def liveness_check():
    """Liveness Check Endpoint"""
    return {"status": "live"}

app.include_router(router)


def main() -> None:
    """Run the Deep Agent API."""
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000)
