"""
Rogers Thought Engine - Cognitive layer for session management
Phase 1 implementation with conversational interface
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class Intent(Enum):
    """Recognized conversation intents"""
    CREATE_SESSION = "create_session"
    GET_SESSION = "get_session"
    UPDATE_SESSION = "update_session"
    SUSPEND_SESSION = "suspend_session"
    ARCHIVE_SESSION = "archive_session"
    LIST_SESSIONS = "list_sessions"
    SESSION_STATUS = "session_status"
    ADD_PARTICIPANT = "add_participant"
    REMOVE_PARTICIPANT = "remove_participant"
    UNKNOWN = "unknown"

class RogersThoughtEngine:
    """
    Thought Engine for Rogers - handles reasoning and conversation
    Phase 1: Basic intent parsing and conversational responses
    """

    def __init__(self, action_engine):
        """
        Initialize Thought Engine with connection to Action Engine

        Args:
            action_engine: The Rogers Action Engine for executing decisions
        """
        self.action_engine = action_engine
        self.conversation_context = {}

        # Intent patterns for Phase 1 (simple keyword matching)
        self.intent_patterns = {
            Intent.CREATE_SESSION: ["create", "new session", "start session", "initialize"],
            Intent.GET_SESSION: ["get", "retrieve", "show", "find session", "what about session"],
            Intent.UPDATE_SESSION: ["update", "modify", "change", "patch"],
            Intent.SUSPEND_SESSION: ["suspend", "pause", "sleep", "dormant"],
            Intent.ARCHIVE_SESSION: ["archive", "cold storage", "backup"],
            Intent.LIST_SESSIONS: ["list", "show all", "active sessions", "how many"],
            Intent.SESSION_STATUS: ["status", "state", "health", "is active"],
            Intent.ADD_PARTICIPANT: ["add participant", "join", "add mad"],
            Intent.REMOVE_PARTICIPANT: ["remove participant", "leave", "remove mad"]
        }

    async def converse(self, message: str, from_mad: str) -> str:
        """
        Main conversational interface for other MADs

        Args:
            message: Natural language message from another MAD
            from_mad: Identifier of the MAD making the request

        Returns:
            Natural language response
        """
        logger.info(f"Rogers received from {from_mad}: {message}")

        # Parse intent from message
        intent, entities = await self.parse_intent(message)

        # Reason about the request
        strategy = await self.reason_about_request(intent, entities, from_mad)

        # Execute via Action Engine
        result = await self.execute_strategy(strategy)

        # Generate conversational response
        response = await self.generate_response(intent, result, from_mad)

        logger.info(f"Rogers responding to {from_mad}: {response}")
        return response

    async def parse_intent(self, message: str) -> tuple[Intent, Dict[str, Any]]:
        """
        Parse intent and entities from natural language message
        Phase 1: Simple keyword matching (can upgrade to LLM in Phase 2)

        Args:
            message: Natural language message

        Returns:
            Tuple of (Intent, entities dict)
        """
        message_lower = message.lower()
        entities = {}

        # Extract potential session ID (simple pattern matching for Phase 1)
        import re
        session_pattern = r'session[- ]?([a-z0-9-]+)'
        session_match = re.search(session_pattern, message_lower)
        if session_match:
            entities['session_id'] = session_match.group(1)

        # Extract user ID
        user_pattern = r'user[- ]?([a-z0-9-]+)'
        user_match = re.search(user_pattern, message_lower)
        if user_match:
            entities['user_id'] = user_match.group(1)

        # Match intent based on keywords
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return intent, entities

        return Intent.UNKNOWN, entities

    async def reason_about_request(
        self,
        intent: Intent,
        entities: Dict[str, Any],
        from_mad: str
    ) -> Dict[str, Any]:
        """
        Make decisions about HOW to fulfill the request
        Phase 1: Simple decision logic (can enhance in Phase 2)

        Args:
            intent: Parsed intent
            entities: Extracted entities
            from_mad: Requesting MAD

        Returns:
            Strategy dictionary for Action Engine
        """
        strategy = {
            'intent': intent,
            'entities': entities,
            'from_mad': from_mad,
            'optimizations': []
        }

        # Phase 1 reasoning - simple rules
        if intent == Intent.CREATE_SESSION:
            # Decision: Should we pre-warm cache for this user?
            if from_mad == "Imperator":
                strategy['optimizations'].append('pre_warm_cache')

        elif intent == Intent.GET_SESSION:
            # Decision: Check cache first, then warm storage
            strategy['optimizations'].append('cache_first')

        elif intent == Intent.ARCHIVE_SESSION:
            # Decision: Coordinate with Dewey for conversation archival
            strategy['requires_coordination'] = ['Dewey']

        elif intent == Intent.LIST_SESSIONS:
            # Decision: Return summary, not full details
            strategy['summary_only'] = True

        return strategy

    async def execute_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute strategy using Action Engine

        Args:
            strategy: Strategy dictionary

        Returns:
            Result from Action Engine
        """
        intent = strategy['intent']
        entities = strategy['entities']

        try:
            # Route to appropriate Action Engine method
            if intent == Intent.CREATE_SESSION:
                user_id = entities.get('user_id', f"mad_{strategy['from_mad']}")
                result = await self.action_engine.create_session(user_id)

            elif intent == Intent.GET_SESSION:
                session_id = entities.get('session_id')
                if not session_id:
                    return {'error': 'No session ID provided'}
                result = await self.action_engine.get_session(session_id)

            elif intent == Intent.SUSPEND_SESSION:
                session_id = entities.get('session_id')
                if not session_id:
                    return {'error': 'No session ID provided'}
                result = await self.action_engine.suspend_session(session_id)

            elif intent == Intent.LIST_SESSIONS:
                result = await self.action_engine.list_active_sessions()

            elif intent == Intent.ADD_PARTICIPANT:
                session_id = entities.get('session_id')
                mad_name = strategy['from_mad']
                result = await self.action_engine.add_participant(session_id, mad_name)

            else:
                result = {'error': f'Intent {intent} not yet implemented'}

        except Exception as e:
            logger.error(f"Error executing strategy: {e}")
            result = {'error': str(e)}

        return result

    async def generate_response(
        self,
        intent: Intent,
        result: Dict[str, Any],
        from_mad: str
    ) -> str:
        """
        Generate natural language response
        Phase 1: Template-based responses (can use LLM in Phase 2)

        Args:
            intent: Original intent
            result: Execution result
            from_mad: MAD to respond to

        Returns:
            Natural language response
        """
        if 'error' in result:
            return f"I encountered an issue: {result['error']}. Could you clarify your request?"

        # Template responses based on intent
        if intent == Intent.CREATE_SESSION:
            return (f"I've created session {result.get('session_id', 'unknown')[:8]}... "
                   f"for {result.get('owner_id', 'unknown')}. The session is now active "
                   f"and ready for use.")

        elif intent == Intent.GET_SESSION:
            state = result.get('state', 'unknown')
            session_id = result.get('session_id', 'unknown')[:8]
            return (f"Session {session_id}... is currently {state}. "
                   f"It was created at {result.get('created_at', 'unknown time')}.")

        elif intent == Intent.SUSPEND_SESSION:
            return (f"I've suspended the session to dormant state. "
                   f"It can be reactivated when needed.")

        elif intent == Intent.LIST_SESSIONS:
            count = result.get('count', 0)
            if count == 0:
                return "There are no active sessions at the moment."
            elif count == 1:
                return "There is 1 active session."
            else:
                active = result.get('active', count)
                dormant = result.get('dormant', 0)
                return (f"I'm managing {count} sessions: {active} active"
                       f"{f', {dormant} dormant' if dormant > 0 else ''}.")

        elif intent == Intent.ADD_PARTICIPANT:
            return (f"I've added you to the session with a {result.get('lease_ttl', 30)} "
                   f"second lease. Remember to renew it before expiration.")

        else:
            return "I've processed your request. Let me know if you need more details."

    async def handle_inter_mad_coordination(
        self,
        request_type: str,
        target_mad: str,
        message: str
    ) -> str:
        """
        Coordinate with other MADs for complex operations
        Phase 1: Basic message passing (can enhance in Phase 2)

        Args:
            request_type: Type of coordination needed
            target_mad: MAD to coordinate with
            message: Message to send

        Returns:
            Coordination result
        """
        # Phase 1: Log the coordination need
        # Phase 2: Actually communicate with other MADs
        logger.info(f"Rogers needs to coordinate with {target_mad}: {message}")

        if target_mad == "Dewey" and request_type == "archive":
            return (f"Dewey, I need to archive conversations for this session. "
                   f"Can you prepare them for cold storage?")

        elif target_mad == "Godot" and request_type == "log":
            return f"Godot, please log this session event: {message}"

        return f"{target_mad}, I need your assistance with: {message}"

    async def learn_from_interaction(
        self,
        message: str,
        intent: Intent,
        success: bool
    ):
        """
        Learn from interactions to improve over time
        Phase 1: Simple pattern tracking (can enhance with ML in Phase 2)

        Args:
            message: Original message
            intent: Detected intent
            success: Whether execution succeeded
        """
        # Phase 1: Log for analysis
        logger.info(f"Learning: '{message}' -> {intent} ({'success' if success else 'failed'})")

        # Phase 2: Update intent patterns, improve parsing, etc.
        pass


class RogersActionEngine:
    """
    Action Engine wrapper for existing Rogers functionality
    This wraps the existing main.py functions
    """

    def __init__(self, app):
        """
        Initialize with FastAPI app instance

        Args:
            app: The FastAPI application
        """
        self.app = app
        # In real implementation, this would connect to the actual
        # Redis, MongoDB, and S3 backends

    async def create_session(self, user_id: str) -> Dict[str, Any]:
        """Create a new session"""
        # Call existing endpoint logic
        import uuid
        session_id = str(uuid.uuid4())
        return {
            'session_id': session_id,
            'version': 1,
            'state': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'owner_id': user_id
        }

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieve session by ID"""
        # In real implementation, check Redis -> MongoDB -> S3
        return {
            'session_id': session_id,
            'version': 1,
            'state': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'owner_id': 'test-user'
        }

    async def suspend_session(self, session_id: str) -> Dict[str, Any]:
        """Suspend session to dormant"""
        return {
            'session_id': session_id,
            'state': 'dormant',
            'suspended_at': datetime.utcnow().isoformat()
        }

    async def list_active_sessions(self) -> Dict[str, Any]:
        """List all active sessions"""
        # In real implementation, query Redis/MongoDB
        return {
            'count': 3,
            'active': 2,
            'dormant': 1,
            'sessions': []  # Summary only for Phase 1
        }

    async def add_participant(self, session_id: str, mad_name: str) -> Dict[str, Any]:
        """Add MAD participant to session"""
        return {
            'session_id': session_id,
            'participant': mad_name,
            'lease_ttl': 30,
            'status': 'added'
        }