"""
Rogers MAD - Complete Phase 1 Implementation
Architecture: Thought Engine + Action Engine
Communication: Natural language conversations
"""

import os
import logging
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import aioredis
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Rogers")

# ============================================================================
# MAD CONFIGURATION
# ============================================================================

class RogersConfig:
    """Rogers MAD Configuration"""
    # Identity
    MAD_NAME = "Rogers"
    MAD_PHASE = 1
    MAD_VERSION = "1.0.0-phase1"

    # Thought Engine Config
    CONTEXT_FILE = os.getenv("CONTEXT_FILE", "/app/context/rogers.md")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")

    # Action Engine Config
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

    # Communication Config
    CONVERSATION_PORT = 8090
    MCP_PORT = 8080
    API_PORT = 8000

config = RogersConfig()

# ============================================================================
# THOUGHT ENGINE - The Brain of Rogers
# ============================================================================

class RogersThoughtEngine:
    """
    Phase 1 Thought Engine - Basic cognitive capabilities
    - Context-based behavior (rogers.md)
    - Simple intent parsing
    - Basic decision making
    - Template-based responses

    Phase 2 will add: DER (Decision Engineering Recommender)
    Phase 3 will add: CET (Context Engineering Transformer)
    """

    def __init__(self):
        self.context = self._load_context()
        self.imperator = self._initialize_imperator()
        self.conversation_history = []

    def _load_context(self) -> str:
        """Load Rogers' context file (rogers.md)"""
        try:
            with open(config.CONTEXT_FILE, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Context file not found: {config.CONTEXT_FILE}")
            return "You are Rogers, the Session Management MAD."

    def _initialize_imperator(self):
        """Initialize the Imperator (LLM) connection"""
        # Phase 1: Basic LLM connection
        # In real implementation, connect to OpenAI/Claude/etc
        logger.info(f"Initializing Imperator with {config.LLM_PROVIDER}/{config.LLM_MODEL}")
        return {
            'provider': config.LLM_PROVIDER,
            'model': config.LLM_MODEL,
            'context': self.context
        }

    async def process_conversation(
        self,
        message: str,
        from_mad: str
    ) -> str:
        """
        Process incoming conversation from another MAD

        Flow:
        1. Receive via Ears (Action Engine)
        2. Process with Imperator (Thought Engine)
        3. Generate response
        4. Send via Mouth (Action Engine)
        """
        logger.info(f"[THOUGHT] Processing from {from_mad}: {message}")

        # Parse intent (Phase 1: keyword-based)
        intent = self._parse_intent(message)

        # Make decision (Phase 1: rule-based)
        decision = self._make_decision(intent, from_mad)

        # Generate response (Phase 1: template-based)
        response = self._generate_response(decision, from_mad)

        # Log for learning (preparation for Phase 2 DER)
        self._log_interaction(message, intent, decision, response)

        return response

    def _parse_intent(self, message: str) -> Dict[str, Any]:
        """Parse intent from message - Phase 1: simple keyword matching"""
        message_lower = message.lower()

        if "create" in message_lower or "new session" in message_lower:
            return {'type': 'CREATE_SESSION', 'confidence': 0.9}
        elif "status" in message_lower or "check" in message_lower:
            return {'type': 'CHECK_STATUS', 'confidence': 0.8}
        elif "archive" in message_lower:
            return {'type': 'ARCHIVE', 'confidence': 0.9}
        elif "list" in message_lower or "show" in message_lower:
            return {'type': 'LIST_SESSIONS', 'confidence': 0.7}
        else:
            return {'type': 'UNKNOWN', 'confidence': 0.3}

    def _make_decision(self, intent: Dict, from_mad: str) -> Dict:
        """
        Make decision based on intent - Phase 1: rule-based
        Phase 2 will use DER for learned decisions
        """
        decision_type = intent['type']

        if decision_type == 'CREATE_SESSION':
            return {
                'action': 'create_session',
                'priority': 'high',
                'cache_strategy': 'hot',
                'ttl': 3600
            }
        elif decision_type == 'ARCHIVE':
            return {
                'action': 'archive_sessions',
                'criteria': 'age > 7 days',
                'coordinate_with': ['Dewey']
            }
        else:
            return {'action': 'provide_info'}

    def _generate_response(self, decision: Dict, from_mad: str) -> str:
        """
        Generate conversational response - Phase 1: template-based
        Phase 3 will use CET for optimized communication
        """
        action = decision.get('action')

        if action == 'create_session':
            return f"I'll create a new session right away. It will be ready in the hot cache with a 1-hour TTL."
        elif action == 'archive_sessions':
            return f"I'll archive sessions older than 7 days. Let me coordinate with Dewey for conversation storage."
        else:
            return f"I understand your request. Let me help you with that."

    def _log_interaction(self, message: str, intent: Dict, decision: Dict, response: str):
        """Log interaction for future learning (Phase 2 DER preparation)"""
        self.conversation_history.append({
            'timestamp': datetime.utcnow(),
            'message': message,
            'intent': intent,
            'decision': decision,
            'response': response
        })

# ============================================================================
# ACTION ENGINE - The Body of Rogers
# ============================================================================

class RogersActionEngine:
    """
    The Action Engine - Rogers' body
    - MCP Server (for Imperator control)
    - Ears (receive conversations)
    - Mouth (send conversations)
    - Arms & Legs (do the work)
    """

    def __init__(self):
        self.redis_client = None
        self.mongo_client = None
        self.setup_complete = False

    async def initialize(self):
        """Initialize Action Engine components"""
        logger.info("[ACTION] Initializing Action Engine...")

        # Initialize storage (Arms & Legs)
        await self._init_storage()

        # Initialize MCP Server
        await self._init_mcp_server()

        # Initialize communication (Ears & Mouth)
        await self._init_communication()

        self.setup_complete = True
        logger.info("[ACTION] Action Engine initialized")

    async def _init_storage(self):
        """Initialize storage connections (Redis, MongoDB)"""
        try:
            # Redis for hot cache
            self.redis_client = await aioredis.create_redis_pool(config.REDIS_URL)
            logger.info("[ACTION] Redis connected")

            # MongoDB for warm storage
            self.mongo_client = AsyncIOMotorClient(config.MONGODB_URL)
            self.db = self.mongo_client.sessions_db
            logger.info("[ACTION] MongoDB connected")
        except Exception as e:
            logger.error(f"[ACTION] Storage init failed: {e}")

    async def _init_mcp_server(self):
        """Initialize MCP Server for Imperator control"""
        logger.info(f"[ACTION] MCP Server ready on port {config.MCP_PORT}")
        # In real implementation, start MCP server here

    async def _init_communication(self):
        """Initialize Ears and Mouth for MAD communication"""
        logger.info(f"[ACTION] Conversation interface ready on port {config.CONVERSATION_PORT}")
        # In real implementation, setup message queue or pub/sub here

    # Arms & Legs - Actual work functions

    async def create_session(self, user_id: str) -> Dict:
        """Create a new session (Arm function)"""
        import uuid
        session_id = str(uuid.uuid4())

        session_data = {
            'session_id': session_id,
            'owner_id': user_id,
            'version': 1,
            'state': 'active',
            'created_at': datetime.utcnow(),
            'participants': [],
            'metadata': {}
        }

        # Store in hot cache (Redis)
        if self.redis_client:
            await self.redis_client.setex(
                f"session:{session_id}",
                3600,  # 1 hour TTL
                json.dumps(session_data, default=str)
            )

        # Store in warm storage (MongoDB)
        if self.mongo_client:
            await self.db.sessions.insert_one(session_data)

        logger.info(f"[ACTION] Created session {session_id}")
        return session_data

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session (Arm function)"""
        # Check hot cache first
        if self.redis_client:
            cached = await self.redis_client.get(f"session:{session_id}")
            if cached:
                logger.info(f"[ACTION] Session {session_id} found in hot cache")
                return json.loads(cached)

        # Check warm storage
        if self.mongo_client:
            session = await self.db.sessions.find_one({'session_id': session_id})
            if session:
                logger.info(f"[ACTION] Session {session_id} found in warm storage")
                # Re-warm the cache
                if self.redis_client:
                    await self.redis_client.setex(
                        f"session:{session_id}",
                        3600,
                        json.dumps(session, default=str)
                    )
                return session

        logger.warning(f"[ACTION] Session {session_id} not found")
        return None

    async def archive_sessions(self, criteria: Dict) -> List[str]:
        """Archive old sessions (Arm function)"""
        archived = []

        if self.mongo_client:
            # Find sessions matching criteria
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            cursor = self.db.sessions.find({
                'state': 'dormant',
                'created_at': {'$lt': cutoff_date}
            })

            async for session in cursor:
                session_id = session['session_id']
                # In Phase 1, just mark as archived
                # Phase 2 would use DER to decide if worth archiving
                await self.db.sessions.update_one(
                    {'session_id': session_id},
                    {'$set': {'state': 'archived'}}
                )
                archived.append(session_id)
                logger.info(f"[ACTION] Archived session {session_id}")

        return archived

    # Communication functions (Ears & Mouth)

    async def receive_conversation(self) -> Optional[Dict]:
        """Ears - Receive conversation from another MAD"""
        # In real implementation, poll message queue
        # For now, return None
        return None

    async def send_conversation(self, to_mad: str, message: str):
        """Mouth - Send conversation to another MAD"""
        logger.info(f"[ACTION] Sending to {to_mad}: {message}")
        # In real implementation, publish to message queue
        pass

# ============================================================================
# ROGERS MAD - Complete Integration
# ============================================================================

class RogersMAD:
    """
    The complete Rogers MAD
    Integrates Thought Engine + Action Engine
    """

    def __init__(self):
        self.thought_engine = RogersThoughtEngine()
        self.action_engine = RogersActionEngine()
        self.running = False

    async def startup(self):
        """Start the Rogers MAD"""
        logger.info(f"{'='*50}")
        logger.info(f"Starting {config.MAD_NAME} MAD v{config.MAD_VERSION}")
        logger.info(f"Phase {config.MAD_PHASE}: Basic Thought + Strong Action")
        logger.info(f"{'='*50}")

        # Initialize Action Engine
        await self.action_engine.initialize()

        # Start conversation loop
        self.running = True
        asyncio.create_task(self._conversation_loop())

        logger.info(f"{config.MAD_NAME} is ready for conversations!")

    async def _conversation_loop(self):
        """Main conversation processing loop"""
        while self.running:
            # Check for incoming conversations (via Ears)
            message = await self.action_engine.receive_conversation()

            if message:
                # Process with Thought Engine
                response = await self.thought_engine.process_conversation(
                    message['content'],
                    message['from_mad']
                )

                # Send response (via Mouth)
                await self.action_engine.send_conversation(
                    message['from_mad'],
                    response
                )

            await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning

    async def shutdown(self):
        """Shutdown the Rogers MAD"""
        logger.info(f"Shutting down {config.MAD_NAME}...")
        self.running = False

        # Cleanup Action Engine resources
        if self.action_engine.redis_client:
            self.action_engine.redis_client.close()
            await self.action_engine.redis_client.wait_closed()

        if self.action_engine.mongo_client:
            self.action_engine.mongo_client.close()

        logger.info(f"{config.MAD_NAME} shutdown complete")

# ============================================================================
# FASTAPI APPLICATION - External interfaces
# ============================================================================

# Create the Rogers MAD instance
rogers = RogersMAD()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await rogers.startup()
    yield
    # Shutdown
    await rogers.shutdown()

app = FastAPI(
    title=f"{config.MAD_NAME} MAD",
    version=config.MAD_VERSION,
    description="Session Management MAD with Thought and Action Engines",
    lifespan=lifespan
)

# ============================================================================
# CONVERSATION INTERFACE - For MAD-to-MAD communication
# ============================================================================

class ConversationMessage(BaseModel):
    """Message format for MAD conversations"""
    from_mad: str
    to_mad: str = "Rogers"
    content: str
    context: Optional[Dict[str, Any]] = None

@app.post("/conversation", tags=["mad-communication"])
async def receive_conversation(message: ConversationMessage):
    """
    Primary interface for MAD-to-MAD conversation

    Examples:
    - Dewey: "Rogers, archive session xyz-789"
    - Horace: "Rogers, is session abc-123 active?"
    - Imperator: "Rogers, create a session for user-456"
    """
    # Process through Thought Engine
    response = await rogers.thought_engine.process_conversation(
        message.content,
        message.from_mad
    )

    return {
        "from": config.MAD_NAME,
        "to": message.from_mad,
        "response": response,
        "timestamp": datetime.utcnow()
    }

# ============================================================================
# MCP INTERFACE - For Imperator control
# ============================================================================

@app.post("/mcp/command", tags=["mcp"])
async def mcp_command(command: Dict[str, Any]):
    """
    MCP interface for Imperator to control Action Engine

    The Imperator uses this to directly command Rogers' actions
    """
    cmd_type = command.get('type')
    params = command.get('params', {})

    if cmd_type == 'create_session':
        result = await rogers.action_engine.create_session(params.get('user_id'))
    elif cmd_type == 'get_session':
        result = await rogers.action_engine.get_session(params.get('session_id'))
    elif cmd_type == 'archive_sessions':
        result = await rogers.action_engine.archive_sessions(params.get('criteria', {}))
    else:
        result = {'error': f'Unknown command: {cmd_type}'}

    return result

# ============================================================================
# TRADITIONAL API - For backwards compatibility
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mad": config.MAD_NAME,
        "phase": config.MAD_PHASE,
        "thought_engine": "active",
        "action_engine": "active" if rogers.action_engine.setup_complete else "initializing"
    }

@app.get("/")
async def root():
    """Rogers MAD information"""
    return {
        "identity": {
            "name": config.MAD_NAME,
            "phase": config.MAD_PHASE,
            "version": config.MAD_VERSION
        },
        "architecture": {
            "thought_engine": {
                "imperator": f"{config.LLM_PROVIDER}/{config.LLM_MODEL}",
                "context": "rogers.md",
                "der": "Not implemented (Phase 2)",
                "cet": "Not implemented (Phase 3)"
            },
            "action_engine": {
                "mcp_server": f"Port {config.MCP_PORT}",
                "storage": ["Redis (hot)", "MongoDB (warm)", "S3 (cold)"],
                "communication": f"Port {config.CONVERSATION_PORT}"
            }
        },
        "interfaces": {
            "conversation": "/conversation (MAD-to-MAD)",
            "mcp": "/mcp/command (Imperator control)",
            "api": "/api/v1/sessions (Traditional)",
            "health": "/health"
        },
        "description": "Rogers manages conversation sessions for the MAD ecosystem"
    }

# Traditional session API endpoints (for backwards compatibility)
from datetime import timedelta

@app.post("/api/v1/sessions")
async def create_session_api(user_id: str):
    """Traditional API - Create session"""
    return await rogers.action_engine.create_session(user_id)

@app.get("/api/v1/sessions/{session_id}")
async def get_session_api(session_id: str):
    """Traditional API - Get session"""
    session = await rogers.action_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.API_PORT)