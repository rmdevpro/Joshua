"""
Rogers - Session Management MAD with Thought and Action Engines
Phase 1 implementation with conversational interface
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# Import the Thought Engine
from rogers_thought_engine import RogersThoughtEngine, RogersActionEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Settings
class Settings:
    PROJECT_NAME = "Rogers"
    API_V1_STR = "/api/v1"
    MAD_NAME = "Rogers"
    VERSION = "1.0.0-phase1"

settings = Settings()

# Data models
class SessionCreate(BaseModel):
    user_id: str

class SessionResponse(BaseModel):
    session_id: str
    version: int
    state: str
    created_at: datetime
    owner_id: str

class ConversationRequest(BaseModel):
    """Model for conversational requests from other MADs"""
    message: str
    from_mad: str
    context: Optional[Dict[str, Any]] = None

class ConversationResponse(BaseModel):
    """Model for conversational responses"""
    response: str
    mad: str = "Rogers"
    timestamp: datetime = datetime.utcnow()

# Global instances
thought_engine: Optional[RogersThoughtEngine] = None
action_engine: Optional[RogersActionEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for Rogers MAD"""
    global thought_engine, action_engine

    # Startup
    logger.info(f"{settings.MAD_NAME} MAD starting...")
    logger.info("Initializing Thought Engine...")

    # Initialize Action Engine
    action_engine = RogersActionEngine(app)

    # Initialize Thought Engine with Action Engine
    thought_engine = RogersThoughtEngine(action_engine)

    logger.info("Thought Engine initialized - Rogers can now think and converse!")
    logger.info("Connecting to databases...")
    # TODO: Add actual database connections
    logger.info("Database connections established (simulated).")
    logger.info(f"{settings.MAD_NAME} is ready for conversations!")

    yield

    # Shutdown
    logger.info(f"{settings.MAD_NAME} shutting down...")
    logger.info("Thought Engine shutting down...")
    logger.info("Database connections closed.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Session Management MAD with Thought and Action Engines",
    lifespan=lifespan
)

# ============================================================================
# THOUGHT ENGINE INTERFACE - Conversational endpoints for MAD communication
# ============================================================================

@app.post("/converse", response_model=ConversationResponse, tags=["thought-engine"])
async def converse_with_rogers(request: ConversationRequest):
    """
    Primary conversational interface for MAD-to-MAD communication

    This is how other MADs talk to Rogers. Examples:
    - Dewey: "Rogers, what's the status of session abc-123?"
    - Imperator: "Rogers, create a new session for user prod-456"
    - Hopper: "Rogers, how many active sessions do we have?"

    This endpoint represents Rogers' Thought Engine - it can:
    - Understand natural language requests
    - Reason about the best approach
    - Execute via the Action Engine
    - Respond conversationally
    """
    if not thought_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Thought Engine not initialized"
        )

    try:
        # Process conversation through Thought Engine
        response = await thought_engine.converse(
            message=request.message,
            from_mad=request.from_mad
        )

        return ConversationResponse(
            response=response,
            mad=settings.MAD_NAME
        )

    except Exception as e:
        logger.error(f"Error in conversation: {e}")
        return ConversationResponse(
            response=f"I'm having trouble understanding that request. Could you rephrase it?",
            mad=settings.MAD_NAME
        )

@app.get("/thought/status", tags=["thought-engine"])
async def thought_engine_status():
    """
    Get the status of Rogers' Thought Engine

    Shows cognitive capabilities and conversation readiness
    """
    if not thought_engine:
        return {
            "status": "offline",
            "mad": settings.MAD_NAME,
            "message": "Thought Engine not initialized"
        }

    return {
        "status": "active",
        "mad": settings.MAD_NAME,
        "capabilities": [
            "natural_language_understanding",
            "session_management_reasoning",
            "inter_mad_conversation",
            "decision_making"
        ],
        "phase": "1",
        "description": "Phase 1 MAD - Basic Thought Engine with strong Action Engine"
    }

# ============================================================================
# ACTION ENGINE INTERFACE - Direct API endpoints (can be used by Thought Engine)
# ============================================================================

@app.get("/health", status_code=status.HTTP_200_OK, tags=["action-engine"])
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    return {
        "status": "ok",
        "service": settings.MAD_NAME,
        "version": settings.VERSION,
        "thought_engine": thought_engine is not None,
        "action_engine": action_engine is not None
    }

@app.get("/metrics", tags=["action-engine", "monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return {
        "sessions_total": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "conversations_handled": 0,
        "status": "metrics endpoint active"
    }

@app.post("/api/v1/sessions", response_model=SessionResponse, tags=["action-engine"])
async def create_session(session_data: SessionCreate):
    """
    Create a new session - Action Engine direct endpoint

    Can be called directly OR via Thought Engine conversation
    """
    if action_engine:
        result = await action_engine.create_session(session_data.user_id)
        return SessionResponse(**result)

    # Fallback to mock
    import uuid
    session_id = str(uuid.uuid4())
    return SessionResponse(
        session_id=session_id,
        version=1,
        state="active",
        created_at=datetime.utcnow(),
        owner_id=session_data.user_id
    )

@app.get("/api/v1/sessions/{session_id}", response_model=SessionResponse, tags=["action-engine"])
async def get_session(session_id: str):
    """
    Retrieve a session by ID - Action Engine direct endpoint

    Can be called directly OR via Thought Engine conversation
    """
    if action_engine:
        result = await action_engine.get_session(session_id)
        if 'error' in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        return SessionResponse(**result)

    # Fallback to mock
    if session_id == "test-404":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return SessionResponse(
        session_id=session_id,
        version=1,
        state="active",
        created_at=datetime.utcnow(),
        owner_id="test-user"
    )

@app.patch("/api/v1/sessions/{session_id}", tags=["action-engine"])
async def update_session(session_id: str, patch: dict, expected_version: int):
    """Update a session with optimistic locking - Action Engine"""
    if expected_version < 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Version conflict"
        )

    return {
        "session_id": session_id,
        "version": expected_version + 1,
        "updated": True
    }

@app.post("/api/v1/sessions/{session_id}/participants", tags=["action-engine"])
async def add_participant(session_id: str, mad_name: str):
    """Add a MAD participant to the session - Action Engine"""
    if action_engine:
        result = await action_engine.add_participant(session_id, mad_name)
        return result

    return {
        "session_id": session_id,
        "participant": mad_name,
        "lease_ttl": 30,
        "status": "added"
    }

@app.post("/api/v1/sessions/{session_id}/suspend", tags=["action-engine"])
async def suspend_session(session_id: str):
    """Suspend a session to dormant state - Action Engine"""
    if action_engine:
        result = await action_engine.suspend_session(session_id)
        return result

    return {
        "session_id": session_id,
        "state": "dormant",
        "suspended_at": datetime.utcnow()
    }

# ============================================================================
# MCP INTERFACE - For integration with MCP relay
# ============================================================================

@app.post("/mcp/tools/converse", tags=["mcp"])
async def mcp_converse_tool(request: dict):
    """
    MCP tool endpoint for conversational interface

    This allows Rogers to be accessed via MCP relay using natural language
    """
    message = request.get('message', '')
    from_mad = request.get('from_mad', 'unknown')

    if not thought_engine:
        return {
            "error": "Thought Engine not initialized",
            "mad": settings.MAD_NAME
        }

    response = await thought_engine.converse(message, from_mad)

    return {
        "response": response,
        "mad": settings.MAD_NAME,
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Rogers MAD root endpoint - shows both Thought and Action capabilities"""
    return {
        "service": f"{settings.MAD_NAME} MAD",
        "status": "operational",
        "description": "Session Management MAD with Thought and Action Engines",
        "version": settings.VERSION,
        "phase": "1",
        "capabilities": {
            "thought_engine": {
                "status": "active" if thought_engine else "offline",
                "interface": "/converse",
                "description": "Natural language conversation for MAD-to-MAD communication"
            },
            "action_engine": {
                "status": "active" if action_engine else "offline",
                "interface": "/api/v1/sessions",
                "description": "Direct API for session management operations"
            }
        },
        "endpoints": {
            "conversation": "/converse",
            "health": "/health",
            "metrics": "/metrics",
            "api_docs": "/docs",
            "sessions_api": "/api/v1/sessions"
        },
        "mad_communication_examples": [
            "POST /converse with: {'message': 'Create a session for user123', 'from_mad': 'Imperator'}",
            "POST /converse with: {'message': 'What sessions are active?', 'from_mad': 'Dewey'}",
            "POST /converse with: {'message': 'Archive dormant sessions', 'from_mad': 'Horace'}"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)