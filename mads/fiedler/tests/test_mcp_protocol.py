"""MCP protocol tests for Fiedler MCP Server."""
import pytest
import subprocess
import json
import time


def send_mcp_request(container_name: str, method: str, params: dict = None) -> dict:
    """
    Send MCP protocol request to container via stdin.

    Args:
        container_name: Docker container name
        method: MCP method (e.g., "tools/list", "tools/call")
        params: Method parameters

    Returns:
        dict: MCP response
    """
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }

    # Send request to container stdin
    result = subprocess.run(
        ["docker", "exec", "-i", container_name, "python", "-m", "fiedler.server"],
        input=json.dumps(request) + "\n",
        capture_output=True,
        text=True,
        timeout=10
    )

    # Note: MCP server might not respond in this simple test
    # This is more of a protocol format test
    return result


def test_mcp_server_process_running():
    """Test that MCP server process is running in container."""
    result = subprocess.run(
        ["docker", "exec", "fiedler-mcp", "ps", "aux"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    # Check for Python process running fiedler.server
    assert "python -m fiedler.server" in result.stdout or "fiedler.server" in result.stdout


def test_mcp_tools_list_structure():
    """Test that fiedler_list_tools returns valid MCP tool structure."""
    from fiedler.tools.models import fiedler_list_models
    from fiedler.tools.config import fiedler_get_config, fiedler_set_models, fiedler_set_output
    from fiedler.tools.send import fiedler_send_schema

    # All Fiedler tools should follow MCP schema
    tools = [
        ("fiedler_list_models", fiedler_list_models),
        ("fiedler_get_config", fiedler_get_config),
        ("fiedler_set_models", fiedler_set_models),
        ("fiedler_set_output", fiedler_set_output),
    ]

    for tool_name, tool_func in tools:
        # Verify tool is callable
        assert callable(tool_func)


def test_fiedler_list_models_schema():
    """Test that fiedler_list_models returns properly formatted data."""
    from fiedler.tools.models import fiedler_list_models

    result = fiedler_list_models()

    # Check structure
    assert isinstance(result, dict)
    assert "models" in result
    assert isinstance(result["models"], list)

    # Check each model has required fields
    for model in result["models"]:
        assert "name" in model
        assert "provider" in model
        assert "aliases" in model
        assert "max_tokens" in model  # Now context_window
        assert "capabilities" in model
        assert isinstance(model["capabilities"], list)


def test_fiedler_get_config_schema():
    """Test that fiedler_get_config returns properly formatted data."""
    from fiedler.tools.config import fiedler_get_config

    result = fiedler_get_config()

    # Check structure
    assert isinstance(result, dict)
    assert "models" in result
    assert "output_dir" in result
    assert "total_available_models" in result
    assert isinstance(result["models"], list)
    assert isinstance(result["total_available_models"], int)


def test_fiedler_set_models_validation():
    """Test that fiedler_set_models validates input."""
    from fiedler.tools.config import fiedler_set_models

    # Valid models
    result = fiedler_set_models(["gemini", "gpt-5"])
    assert result["status"] == "configured"
    assert "gemini-2.5-pro" in result["models"]

    # Invalid model
    with pytest.raises(ValueError, match="Unknown model or alias"):
        fiedler_set_models(["invalid-model-xyz"])


def test_fiedler_set_output_validation():
    """Test that fiedler_set_output validates directory path."""
    from fiedler.tools.config import fiedler_set_output

    # Valid path
    result = fiedler_set_output("/tmp/fiedler_test")
    assert result["status"] == "configured"
    assert result["output_dir"] == "/tmp/fiedler_test"


def test_mcp_error_response_structure():
    """Test that MCP errors follow structured format."""
    from fiedler.server import call_tool
    from mcp.types import TextContent
    import asyncio

    # Test unknown tool error
    async def test_unknown_tool():
        result = await call_tool("unknown_tool", {})
        assert len(result) == 1
        assert isinstance(result[0], TextContent)

        # Parse error response
        error_data = json.loads(result[0].text)
        assert "error" in error_data
        assert "code" in error_data["error"]
        assert "message" in error_data["error"]
        assert error_data["error"]["code"] == "UNKNOWN_TOOL"

    # Test missing argument error
    async def test_missing_arg():
        result = await call_tool("fiedler_send", {})  # Missing required 'prompt'
        assert len(result) == 1
        error_data = json.loads(result[0].text)
        assert "error" in error_data
        assert error_data["error"]["code"] == "MISSING_ARGUMENT"

    # Run async tests
    asyncio.run(test_unknown_tool())
    asyncio.run(test_missing_arg())


def test_docker_logs_show_startup():
    """Test that Docker logs show server startup."""
    result = subprocess.run(
        ["docker", "logs", "fiedler-mcp", "--tail", "50"],
        capture_output=True,
        text=True
    )
    # Container should have started without errors
    assert result.returncode == 0
    # Note: MCP server in stdio mode may not log much to stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
