# I13: Agentic Infrastructure Architecture (AutoGen + MCP)

**Version:** 1.0
**Date:** 2025-10-01
**Status:** Draft
**Phase:** Foundation Enhancement (Weeks 25-28)
**Dependencies:** I02 (foundation), I03 (LLM infrastructure)
**Enables:** Modular Agentic Duos, scalable agent orchestration

---

## Executive Summary

This document specifies the transition from traditional infrastructure to an **agentic architecture** using:
- **AutoGen** for multi-agent coordination and conversation patterns
- **MCP (Model Context Protocol)** for standardized tool interfaces
- **Modular Agentic Duos** pattern where CETs pair with agents as optional learning enhancements

**Core Principle:** "An agent sits in front of every function" - infrastructure exposed through intelligent agents that can reason, coordinate, and learn.

**Timeline:** 4 weeks (after Phase 3 completion)
**Critical Milestone:** 6 functional agents operational, first Modular Agentic Duo (CET-D + Requirements Agent) deployed
**Success Criteria:** All infrastructure accessible via agents, MCP layer functional, CET-D duo improves requirements extraction

---

## Architecture Overview

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   AutoGen Agent Layer                        │
│  (Coordination, Conversation, Reasoning)                     │
│                                                              │
│  [Data Agent] [LLM Agent] [Execution Agent]                 │
│  [Validation Agent] [Training Agent] [Monitoring Agent]     │
└─────────────────────────────────────────────────────────────┘
                            ↓ calls tools via
┌─────────────────────────────────────────────────────────────┐
│                      MCP Tool Layer                          │
│  (Standardized Interfaces, Protocol)                         │
│                                                              │
│  MCP Server: data-agent-tools                               │
│  MCP Server: llm-orchestrator-tools                         │
│  MCP Server: execution-agent-tools                          │
│  MCP Server: monitoring-agent-tools                         │
└─────────────────────────────────────────────────────────────┘
                            ↓ wraps
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  (Existing Systems)                                          │
│                                                              │
│  PostgreSQL + pgvector | vLLM (6 models) | Docker           │
│  Prometheus + Grafana  | Training Pipeline | File System    │
└─────────────────────────────────────────────────────────────┘
```

### Modular Agentic Duo Pattern

```
┌──────────────────────────────────────────┐
│         Modular Agentic Duo              │
│                                          │
│  ┌─────────────┐      ┌──────────────┐  │
│  │   CET-D     │─────→│ Requirements │  │
│  │  (Learns)   │      │    Agent     │  │
│  │             │      │   (Acts)     │  │
│  └─────────────┘      └──────────────┘  │
│                                          │
│  CET provides intelligence               │
│  Agent provides execution                │
└──────────────────────────────────────────┘
```

**Key Insight:** CETs are **optional learning enhancements** for agents, not standalone components. Agents function independently; CETs make them smarter.

---

## The 6 Core Agents

### 1. Data Agent
**Purpose:** Manages all data operations (storage, retrieval, embeddings)

**AutoGen Configuration:**
```python
from autogen import AssistantAgent

data_agent = AssistantAgent(
    name="DataAgent",
    system_message="""I manage data storage and retrieval for ICCM.

    Capabilities:
    - Store conversations with embeddings (PostgreSQL + pgvector)
    - Vector similarity search
    - Store training signals and metrics
    - Manage conversation history

    I coordinate with other agents to persist their data.""",

    llm_config={
        "config_list": [{"model": "gpt-4", "api_key": "..."}],
        "functions": [
            {
                "name": "store_conversation",
                "description": "Store conversation with vector embeddings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string"},
                        "messages": {"type": "array"},
                        "metadata": {"type": "object"}
                    }
                }
            },
            {
                "name": "retrieve_similar",
                "description": "Vector search over conversations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"}
                    }
                }
            },
            {
                "name": "store_training_signal",
                "description": "Store training results for CET learning",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app_id": {"type": "string"},
                        "requirements": {"type": "string"},
                        "test_results": {"type": "object"}
                    }
                }
            }
        ]
    }
)
```

**MCP Integration:**
Each function calls an MCP tool:
```python
# AutoGen function implementation
async def store_conversation(conversation_id, messages, metadata):
    # Call MCP server tool
    result = await mcp_client.call_tool(
        server="data-agent-mcp",
        tool="store_conversation",
        arguments={
            "conversation_id": conversation_id,
            "messages": messages,
            "metadata": metadata
        }
    )
    return result
```

**Infrastructure Wrapped:**
- PostgreSQL database (conversations, apps, test results)
- pgvector extension (embeddings, similarity search)
- Connection pooling and caching

---

### 2. LLM Orchestrator Agent
**Purpose:** Coordinates the 6-model LLM orchestra for code generation

**AutoGen Configuration:**
```python
llm_orchestrator = AssistantAgent(
    name="LLMOrchestrator",
    system_message="""I coordinate multiple local LLMs for code generation.

    Available Models:
    - DeepSeek-Coder-33B (code specialist)
    - CodeLlama-34B (Meta's code model)
    - Llama-3.1-70B (general reasoning)
    - Mistral-7B (fast inference)
    - Qwen-2.5-14B (multilingual)
    - Phi-3-mini (efficient small model)

    I manage model rotation based on VRAM constraints and generate
    implementations from all models for reconstruction testing.""",

    llm_config={
        "functions": [
            {
                "name": "generate_implementations",
                "description": "Generate code from requirements using all LLMs",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "requirements": {"type": "string"},
                        "models": {"type": "array", "items": {"type": "string"}},
                        "temperature": {"type": "number", "default": 0.2}
                    }
                }
            },
            {
                "name": "rotate_models",
                "description": "Swap models based on VRAM availability",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "unload_model": {"type": "string"},
                        "load_model": {"type": "string"}
                    }
                }
            }
        ]
    }
)
```

**GroupChat for Multi-LLM Coordination:**
```python
from autogen import GroupChat, GroupChatManager

# Create GroupChat for parallel LLM coordination
llm_group = GroupChat(
    agents=[
        llm_orchestrator,
        deepseek_agent,
        codellama_agent,
        llama_agent,
        mistral_agent,
        qwen_agent,
        phi_agent
    ],
    messages=[],
    max_round=6  # One round per model
)

llm_manager = GroupChatManager(groupchat=llm_group)
```

**Infrastructure Wrapped:**
- vLLM serving (6 models)
- Model rotation scheduler
- Generation caching
- VRAM management

---

### 3. Execution Agent
**Purpose:** Executes tests in isolated Docker containers

**AutoGen Configuration:**
```python
execution_agent = AssistantAgent(
    name="ExecutionAgent",
    system_message="""I execute tests in isolated Docker containers.

    Capabilities:
    - Create isolated execution environments
    - Run test suites against implementations
    - Capture test results and logs
    - Clean up containers
    - Manage resource limits

    I ensure safe, isolated execution of untrusted code.""",

    llm_config={
        "functions": [
            {
                "name": "execute_tests",
                "description": "Run tests in Docker container",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app_id": {"type": "string"},
                        "implementation": {"type": "string"},
                        "test_suite": {"type": "string"},
                        "timeout": {"type": "integer", "default": 300}
                    }
                }
            },
            {
                "name": "create_container",
                "description": "Create isolated execution environment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "base_image": {"type": "string"},
                        "resources": {"type": "object"}
                    }
                }
            },
            {
                "name": "cleanup_containers",
                "description": "Remove finished containers",
                "parameters": {"type": "object"}
            }
        ]
    }
)
```

**Infrastructure Wrapped:**
- Docker Engine (container creation/execution)
- Test harness (test execution framework)
- Resource limits (CPU, memory, timeout)
- Log collection

---

### 4. Validation Agent (Orchestrator)
**Purpose:** Orchestrates reconstruction testing across all agents

**AutoGen Configuration (GroupChat Manager):**
```python
validation_agent = GroupChatManager(
    groupchat=GroupChat(
        agents=[
            requirements_agent,  # CET-D duo (when available)
            llm_orchestrator,
            execution_agent,
            data_agent,
            monitoring_agent
        ],
        messages=[],
        max_round=10,
        speaker_selection_method="auto"
    ),
    system_message="""I orchestrate reconstruction testing.

    Workflow:
    1. Requirements Agent extracts requirements from source code
    2. LLM Orchestrator generates implementations from all models
    3. Execution Agent runs tests on each implementation
    4. Data Agent stores results
    5. Monitoring Agent tracks metrics
    6. I compute final validation metrics (pass rate, variance)
    """
)
```

**Orchestration Flow:**
```python
async def validate_app(app_id):
    # Validation Agent initiates GroupChat workflow
    validation_result = await validation_agent.initiate_chat(
        message=f"""Validate app {app_id} via reconstruction testing:

        1. Extract requirements from source code
        2. Generate implementations from all LLMs
        3. Execute tests on each implementation
        4. Store results and compute metrics
        """,
        recipient=requirements_agent  # Start with requirements
    )

    # GroupChat automatically routes through:
    # Requirements Agent → LLM Orchestrator → Execution Agent → Data Agent → Monitoring Agent

    return validation_result
```

**Infrastructure Wrapped:**
- Validation pipeline logic
- Metric computation
- Agent coordination

---

### 5. Training Agent
**Purpose:** Manages CET training loops and convergence

**AutoGen Configuration:**
```python
training_agent = AssistantAgent(
    name="TrainingAgent",
    system_message="""I manage CET training loops.

    Capabilities:
    - Execute training steps (forward, loss, backward, update)
    - Save/load checkpoints
    - Monitor convergence
    - Coordinate with Validation Agent for reward signals

    I implement the 4-phase training methodology.""",

    llm_config={
        "functions": [
            {
                "name": "train_step",
                "description": "Execute one training step",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phase": {"type": "string"},
                        "batch": {"type": "object"}
                    }
                }
            },
            {
                "name": "evaluate_convergence",
                "description": "Check if training has converged",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "loss_history": {"type": "array"},
                        "reward_history": {"type": "array"}
                    }
                }
            },
            {
                "name": "checkpoint",
                "description": "Save model checkpoint",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "epoch": {"type": "integer"},
                        "metrics": {"type": "object"}
                    }
                }
            }
        ]
    }
)
```

**Training Loop with Agent Coordination:**
```python
async def train_phase3():
    for epoch in range(num_epochs):
        for app in training_apps:
            # 1. Training Agent requests reconstruction
            reconstruction_result = await training_agent.initiate_chat(
                message=f"Validate app {app['id']} for training signal",
                recipient=validation_agent
            )

            # 2. Extract reward from validation
            reward = reconstruction_result['mean_pass_rate']

            # 3. Training Agent updates CET-D
            await training_agent.call_function(
                "train_step",
                phase="phase3",
                batch={"app_id": app['id'], "reward": reward}
            )
```

**Infrastructure Wrapped:**
- PyTorch training loop
- Checkpoint management
- Convergence detection
- Optimizer state

---

### 6. Monitoring Agent
**Purpose:** Collects metrics and triggers alerts

**AutoGen Configuration:**
```python
monitoring_agent = AssistantAgent(
    name="MonitoringAgent",
    system_message="""I monitor system health and training progress.

    Capabilities:
    - Collect infrastructure metrics (GPU, database, Docker)
    - Track training metrics (loss, reward, pass rate)
    - Detect anomalies and trigger alerts
    - Monitor catastrophic forgetting via canary set

    I ensure the system operates within acceptable parameters.""",

    llm_config={
        "functions": [
            {
                "name": "collect_metrics",
                "description": "Collect current system metrics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric_type": {"type": "string"},
                        "window": {"type": "string"}
                    }
                }
            },
            {
                "name": "trigger_alert",
                "description": "Send alert for anomaly",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string"},
                        "message": {"type": "string"}
                    }
                }
            },
            {
                "name": "check_canary_set",
                "description": "Test for catastrophic forgetting",
                "parameters": {"type": "object"}
            }
        ]
    }
)
```

**Infrastructure Wrapped:**
- Prometheus (metrics collection)
- Grafana (visualization)
- Alertmanager (alert routing)
- Canary set testing

---

## Modular Agentic Duo Pattern

### First Duo: CET-D + Requirements Agent

**Concept:** CET-D learns requirements extraction, Requirements Agent acts on requirements

**Requirements Agent (without CET-D):**
```python
requirements_agent_base = AssistantAgent(
    name="RequirementsAgent",
    system_message="""I extract requirements from source code.

    I use base LLM prompting to extract functional requirements.""",

    llm_config={
        "functions": [
            {
                "name": "extract_requirements",
                "description": "Extract requirements from source code",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "source_code": {"type": "string"}
                    }
                }
            }
        ]
    }
)

# Base implementation (before CET-D training)
async def extract_requirements(source_code):
    # Use LLM with prompt engineering
    prompt = f"""Extract functional requirements from this code:

    {source_code}

    Return requirements as structured JSON."""

    return await llm.generate(prompt)
```

**Requirements Agent (with CET-D) - Modular Agentic Duo:**
```python
class RequirementsAgentDuo(AssistantAgent):
    def __init__(self, cet_d_model=None):
        self.cet_d = cet_d_model  # Optional CET-D enhancement

        super().__init__(
            name="RequirementsAgent",
            system_message="""I extract requirements from source code.

            When CET-D is available, I use it for learned extraction.
            Otherwise, I fall back to base LLM prompting.""",

            llm_config={
                "functions": [
                    {
                        "name": "extract_requirements",
                        "description": "Extract requirements (CET-D enhanced if available)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "source_code": {"type": "string"}
                            }
                        }
                    }
                ]
            }
        )

    async def extract_requirements(self, source_code):
        if self.cet_d is not None:
            # Use learned CET-D model
            return self.cet_d.extract(source_code)
        else:
            # Fall back to base LLM
            return await self._base_extract(source_code)

    async def _base_extract(self, source_code):
        prompt = f"""Extract functional requirements from this code:

        {source_code}

        Return requirements as structured JSON."""

        return await self.llm.generate(prompt)
```

**Training the Duo:**
```python
async def train_duo_phase3():
    """Train CET-D while Requirements Agent provides feedback."""

    # Start with base Requirements Agent (no CET-D)
    requirements_agent = RequirementsAgentDuo(cet_d_model=None)

    for epoch in range(num_epochs):
        for app in training_apps:
            # 1. CET-D generates requirements
            requirements = cet_d.generate_requirements(app['source_code'])

            # 2. Requirements Agent validates via reconstruction
            validation_result = await validation_agent.initiate_chat(
                message=f"Validate these requirements: {requirements}",
                recipient=llm_orchestrator  # Generate implementations
            )

            # 3. CET-D learns from reconstruction quality
            reward = validation_result['mean_pass_rate']
            cet_d.update(requirements, reward)

    # After training, upgrade Requirements Agent with CET-D
    requirements_agent = RequirementsAgentDuo(cet_d_model=cet_d)
```

### Future Duos

**CET-P + Personal Context Agent** (Future):
- CET-P learns user preferences and patterns
- Personal Context Agent provides personalized responses

**CET-T + Team Context Agent** (Future):
- CET-T learns team conventions and standards
- Team Context Agent enforces team practices

**Pattern is reusable:** Any agent can be enhanced with a learned CET component

---

## MCP Integration Layer

### MCP Servers for Each Agent Domain

**1. Data Agent MCP Server:**
```python
# data_agent_mcp.py
from mcp.server import MCPServer
import asyncpg

app = MCPServer("data-agent-mcp")

@app.list_tools()
async def list_tools():
    return [
        {
            "name": "store_conversation",
            "description": "Store conversation with vector embeddings",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "string"},
                    "messages": {"type": "array"},
                    "metadata": {"type": "object"}
                }
            }
        },
        {
            "name": "retrieve_similar",
            "description": "Vector similarity search",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"}
                }
            }
        }
    ]

@app.call_tool()
async def call_tool(name, arguments):
    if name == "store_conversation":
        # Connect to PostgreSQL
        conn = await asyncpg.connect(DATABASE_URL)

        # Store conversation
        await conn.execute("""
            INSERT INTO conversations (id, messages, metadata, embedding)
            VALUES ($1, $2, $3, $4)
        """,
        arguments['conversation_id'],
        arguments['messages'],
        arguments['metadata'],
        generate_embedding(arguments['messages'])
        )

        await conn.close()
        return {"status": "success"}

    elif name == "retrieve_similar":
        conn = await asyncpg.connect(DATABASE_URL)

        # Vector search
        results = await conn.fetch("""
            SELECT id, messages, metadata
            FROM conversations
            ORDER BY embedding <-> $1
            LIMIT $2
        """,
        generate_embedding(arguments['query']),
        arguments['limit']
        )

        await conn.close()
        return {"results": results}
```

**2. LLM Orchestrator MCP Server:**
```python
# llm_orchestrator_mcp.py
from mcp.server import MCPServer
import asyncio

app = MCPServer("llm-orchestrator-mcp")

@app.list_tools()
async def list_tools():
    return [
        {
            "name": "generate_implementations",
            "description": "Generate code from all LLMs",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "requirements": {"type": "string"},
                    "models": {"type": "array"},
                    "temperature": {"type": "number"}
                }
            }
        }
    ]

@app.call_tool()
async def call_tool(name, arguments):
    if name == "generate_implementations":
        requirements = arguments['requirements']
        models = arguments.get('models', ALL_MODELS)
        temperature = arguments.get('temperature', 0.2)

        # Generate from all models in parallel
        tasks = [
            generate_from_model(model, requirements, temperature)
            for model in models
        ]

        implementations = await asyncio.gather(*tasks)

        return {
            "implementations": implementations,
            "models_used": models
        }

async def generate_from_model(model_name, requirements, temperature):
    # Call vLLM for generation
    response = await vllm_client.generate(
        model=model_name,
        prompt=f"Implement these requirements:\n\n{requirements}",
        temperature=temperature
    )

    return {
        "model": model_name,
        "implementation": response
    }
```

**3. Execution Agent MCP Server:**
```python
# execution_agent_mcp.py
from mcp.server import MCPServer
import docker

app = MCPServer("execution-agent-mcp")
docker_client = docker.from_env()

@app.call_tool()
async def call_tool(name, arguments):
    if name == "execute_tests":
        app_id = arguments['app_id']
        implementation = arguments['implementation']
        test_suite = arguments['test_suite']
        timeout = arguments.get('timeout', 300)

        # Create isolated container
        container = docker_client.containers.run(
            image="python:3.11-slim",
            command=f"pytest /app/tests.py",
            volumes={
                '/tmp/impl': {'bind': '/app', 'mode': 'rw'}
            },
            detach=True,
            mem_limit="512m",
            cpu_quota=50000
        )

        # Write implementation to volume
        with open(f'/tmp/impl/implementation.py', 'w') as f:
            f.write(implementation)

        with open(f'/tmp/impl/tests.py', 'w') as f:
            f.write(test_suite)

        # Wait for completion (with timeout)
        try:
            result = container.wait(timeout=timeout)
            logs = container.logs().decode('utf-8')

            # Parse test results
            test_pass_rate = parse_pytest_output(logs)

            return {
                "status": "success",
                "test_pass_rate": test_pass_rate,
                "logs": logs
            }
        finally:
            container.remove(force=True)
```

### AutoGen ↔ MCP Bridge

**Function Implementation Pattern:**
```python
from mcp import Client as MCPClient

# Create MCP client
mcp_client = MCPClient()

# AutoGen function calls MCP tool
async def autogen_function_to_mcp(function_name, server_name, tool_name, arguments):
    """Bridge AutoGen function calls to MCP tools."""

    result = await mcp_client.call_tool(
        server=server_name,
        tool=tool_name,
        arguments=arguments
    )

    return result

# Example: Data Agent store_conversation function
async def store_conversation(conversation_id, messages, metadata):
    return await autogen_function_to_mcp(
        function_name="store_conversation",
        server_name="data-agent-mcp",
        tool_name="store_conversation",
        arguments={
            "conversation_id": conversation_id,
            "messages": messages,
            "metadata": metadata
        }
    )
```

---

## Implementation Timeline

### Week 25-26: Infrastructure Setup

**Tasks:**
1. Install AutoGen: `pip install pyautogen`
2. Create MCP servers for each agent domain
3. Build agent-to-MCP bridge utilities
4. Test MCP connectivity

**Deliverables:**
- AutoGen installed and configured
- 6 MCP servers operational (data, llm, execution, monitoring)
- Bridge utilities tested

### Week 27: Agent Implementation

**Tasks:**
1. Implement 6 core AutoGen agents
2. Configure GroupChat for LLM orchestration
3. Configure GroupChatManager for Validation Agent
4. Test agent-to-agent communication

**Deliverables:**
- All 6 agents functional
- GroupChat coordination working
- Agent communication via MCP verified

### Week 28: Duo Integration

**Tasks:**
1. Create Requirements Agent (base version, no CET-D)
2. Integrate CET-D model from Phase 3 training
3. Build Modular Agentic Duo (CET-D + Requirements Agent)
4. Test duo performance vs. base agent

**Deliverables:**
- Requirements Agent operational (with/without CET-D)
- CET-D duo integrated
- Performance comparison: duo vs. base (expect >10% improvement)

---

## Migration Strategy

### Phase 0: Current State (Weeks 1-24)
- Non-agentic infrastructure
- Direct tool calls (PostgreSQL, vLLM, Docker)
- Training scripts calling infrastructure directly

### Phase 1: Agent Layer (Weeks 25-26)
- Add MCP servers wrapping infrastructure
- Infrastructure unchanged
- Both direct and agent access available

### Phase 2: Agent Migration (Week 27)
- Replace direct infrastructure calls with agent calls
- Training scripts use Validation Agent
- Monitoring uses Monitoring Agent
- All access via agents

### Phase 3: Duo Enablement (Week 28)
- Integrate first duo (CET-D + Requirements Agent)
- Measure improvement
- Plan future duos based on results

### Rollback Plan
If agentic architecture fails:
- Week 25-26: MCP layer is optional, can be disabled
- Week 27: Agents can be bypassed, fall back to direct calls
- Week 28: Duo is optional enhancement, can use base agent

---

## Performance Considerations

### Agent Overhead
- **AutoGen coordination:** ~100-200ms per agent call
- **MCP protocol:** ~50ms per tool call
- **Total overhead:** ~150-250ms per operation

**Mitigation:**
- Batch operations where possible
- Cache agent responses
- Use async/await for parallelism

### Resource Usage
- **AutoGen agents:** ~200MB RAM per agent (6 agents = ~1.2GB)
- **MCP servers:** ~100MB RAM per server (4 servers = ~400MB)
- **Total:** ~1.6GB additional RAM

**Mitigation:**
- RAM upgrade already planned ($200, Paper 08)
- 256GB total RAM sufficient for all agents

### Latency Impact on Training
- Phase 3 training: 40 apps × 10 epochs = 400 reconstructions
- Without agents: ~60 seconds per reconstruction
- With agents: ~65 seconds per reconstruction (+8% overhead)
- Total impact: ~33 minutes additional training time (acceptable)

---

## Testing and Validation

### Agent Unit Tests

```python
import pytest
from autogen import AssistantAgent

@pytest.mark.asyncio
async def test_data_agent_store():
    """Test Data Agent stores conversation correctly."""

    data_agent = create_data_agent()

    result = await data_agent.call_function(
        "store_conversation",
        conversation_id="test_123",
        messages=[{"role": "user", "content": "test"}],
        metadata={"source": "test"}
    )

    assert result['status'] == 'success'

@pytest.mark.asyncio
async def test_llm_orchestrator_generation():
    """Test LLM Orchestrator generates from all models."""

    llm_agent = create_llm_orchestrator()

    result = await llm_agent.call_function(
        "generate_implementations",
        requirements="Create a function that adds two numbers",
        models=["deepseek", "codellama"]
    )

    assert len(result['implementations']) == 2
    assert result['models_used'] == ["deepseek", "codellama"]

@pytest.mark.asyncio
async def test_validation_orchestration():
    """Test Validation Agent orchestrates full workflow."""

    validation_agent = create_validation_agent()

    result = await validation_agent.initiate_chat(
        message="Validate app_001 via reconstruction",
        recipient=requirements_agent
    )

    assert 'mean_pass_rate' in result
    assert result['implementations_tested'] == 6
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_reconstruction_via_agents():
    """Test end-to-end reconstruction using agent architecture."""

    # Load test app
    app = load_app("app_001")

    # Initiate via Validation Agent
    validation_result = await validation_agent.initiate_chat(
        message=f"Validate {app['id']} via reconstruction",
        recipient=requirements_agent
    )

    # Verify workflow executed
    assert validation_result['requirements_extracted']
    assert len(validation_result['implementations']) == 6
    assert validation_result['tests_executed']
    assert validation_result['mean_pass_rate'] >= 0.7

@pytest.mark.asyncio
async def test_duo_performance():
    """Test CET-D duo improves over base agent."""

    app = load_app("app_001")

    # Base Requirements Agent (no CET-D)
    base_agent = RequirementsAgentDuo(cet_d_model=None)
    base_requirements = await base_agent.extract_requirements(app['source_code'])
    base_result = await validate_requirements(base_requirements, app)

    # CET-D Duo
    duo_agent = RequirementsAgentDuo(cet_d_model=trained_cet_d)
    duo_requirements = await duo_agent.extract_requirements(app['source_code'])
    duo_result = await validate_requirements(duo_requirements, app)

    # Duo should perform better
    assert duo_result['mean_pass_rate'] > base_result['mean_pass_rate']
```

---

## Success Metrics

### Agent Layer Success (Week 26)
- ✅ All 6 agents respond to function calls
- ✅ MCP connectivity: <100ms latency
- ✅ Agent coordination: GroupChat routes correctly

### Migration Success (Week 27)
- ✅ All infrastructure accessible via agents
- ✅ Training pipeline uses Validation Agent
- ✅ Overhead: <20% additional latency

### Duo Success (Week 28)
- ✅ CET-D duo operational
- ✅ Performance: Duo >10% better than base agent
- ✅ Duo seamlessly upgrades base agent (no API changes)

---

## Next Steps

**Immediate:**
1. Review this document with team
2. Send to AI reviewers (Fiedler's default models 
3. Get approval for agentic architecture approach
4. Begin Week 25 execution (install AutoGen, build MCP servers)

**Dependencies:**
- **Requires:** I02 (foundation), I03 (LLM infrastructure), I08 (CET-D trained)
- **Enables:** Scalable agent architecture, future duos, advanced coordination
- **Parallel:** Can proceed after Phase 3 training complete

**Week 29 Preview:**
- Evaluate additional duos (CET-P, CET-T)
- Optimize agent performance
- Scale testing to 50-app dataset

---

## References

- **AutoGen Documentation:** https://microsoft.github.io/autogen/
- **MCP Protocol:** https://modelcontextprotocol.io/
- **LangGraph (comparison):** https://langchain-ai.github.io/langgraph/
- **Paper 01:** ICCM Primary Paper (Modular Agentic Duo concept)
- **Paper 02:** Progressive Training Methodology (CET training phases)
- **Paper 03:** CET Architecture (CET-D, CET-P, CET-T specifications)
- **I08:** Phase 3 Training (CET-D training that produces duo component)

---

## Appendix: Agent Communication Patterns

### Pattern 1: Sequential Delegation
```python
# Validation Agent delegates sequentially
result = await validation_agent.initiate_chat(
    message="Extract requirements from app_001",
    recipient=requirements_agent
)

implementations = await validation_agent.initiate_chat(
    message=f"Generate implementations from: {result['requirements']}",
    recipient=llm_orchestrator
)
```

### Pattern 2: Parallel Coordination (GroupChat)
```python
# LLM Orchestrator coordinates 6 models in parallel
result = await llm_manager.initiate_chat(
    message="Generate implementations from all models",
    recipient=llm_orchestrator
)
# GroupChat automatically distributes to all model agents
```

### Pattern 3: Feedback Loop
```python
# Training Agent requests validation, receives feedback
for epoch in range(epochs):
    reconstruction = await training_agent.initiate_chat(
        message=f"Validate app {app_id}",
        recipient=validation_agent
    )

    reward = reconstruction['mean_pass_rate']

    await training_agent.call_function(
        "train_step",
        phase="phase3",
        batch={"reward": reward}
    )
```

### Pattern 4: Monitoring Trigger
```python
# Monitoring Agent observes, triggers on anomaly
metrics = await monitoring_agent.call_function("collect_metrics")

if metrics['canary_degradation'] > 0.10:
    await monitoring_agent.call_function(
        "trigger_alert",
        severity="critical",
        message="Catastrophic forgetting detected"
    )

    # Coordinate with Training Agent for rollback
    await monitoring_agent.initiate_chat(
        message="Rollback to previous checkpoint",
        recipient=training_agent
    )
```
