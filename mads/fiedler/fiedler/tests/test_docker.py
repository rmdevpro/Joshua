"""Docker integration tests for Fiedler MCP Server."""
import pytest
import subprocess
import json
import time


def test_docker_container_running():
    """Test that Fiedler container is running."""
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=fiedler-mcp", "--format", "{{.Status}}"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Up" in result.stdout


def test_docker_container_healthy():
    """Test that Fiedler container is healthy."""
    # Wait a bit for health checks
    time.sleep(5)

    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Health.Status}}", "fiedler-mcp"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "healthy"


def test_docker_environment_variables():
    """Test that required environment variables are set in container."""
    result = subprocess.run(
        ["docker", "exec", "fiedler-mcp", "env"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0

    env_output = result.stdout

    # Check required variables
    assert "FIEDLER_GEMINI_CLIENT=/app/clients/gemini_client.py" in env_output
    assert "FIEDLER_GROK_CLIENT=/app/clients/grok_client.py" in env_output
    assert "FIEDLER_ALLOWED_FILE_ROOTS=/app/allowed_files,/app/fiedler_output" in env_output
    assert "FIEDLER_SAVE_PROMPT=0" in env_output


def test_docker_volumes_mounted():
    """Test that volumes are properly mounted."""
    # Check output volume exists
    result = subprocess.run(
        ["docker", "exec", "fiedler-mcp", "ls", "-la", "/app/fiedler_output"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0

    # Check allowed_files volume exists
    result = subprocess.run(
        ["docker", "exec", "fiedler-mcp", "ls", "-la", "/app/allowed_files"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0

    # Check client scripts are mounted read-only
    result = subprocess.run(
        ["docker", "exec", "fiedler-mcp", "ls", "-la", "/app/clients/gemini_client.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0


def test_docker_port_exposed():
    """Test that port 9010 is exposed."""
    result = subprocess.run(
        ["docker", "port", "fiedler-mcp"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "9010" in result.stdout
    assert "8080" in result.stdout


def test_docker_python_dependencies():
    """Test that required Python packages are installed."""
    result = subprocess.run(
        ["docker", "exec", "fiedler-mcp", "pip", "list"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0

    pip_output = result.stdout

    # Check critical dependencies
    assert "tiktoken" in pip_output
    assert "pydantic" in pip_output
    assert "mcp" in pip_output or "model-context-protocol" in pip_output


def test_docker_fiedler_module_importable():
    """Test that fiedler module can be imported in container."""
    result = subprocess.run(
        ["docker", "exec", "fiedler-mcp", "python", "-c", "import fiedler; print('OK')"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "OK" in result.stdout


def test_docker_restart_policy():
    """Test that container has correct restart policy."""
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.HostConfig.RestartPolicy.Name}}", "fiedler-mcp"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "unless-stopped"


def test_docker_network():
    """Test that container is on correct network."""
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{json .NetworkSettings.Networks}}", "fiedler-mcp"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    networks = json.loads(result.stdout)
    assert "fiedler_fiedler_network" in networks


def test_docker_stdin_open():
    """Test that stdin is kept open for MCP stdio protocol."""
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.Config.OpenStdin}}", "fiedler-mcp"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "true"


def test_docker_tty_allocated():
    """Test that TTY is allocated for MCP stdio protocol."""
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.Config.Tty}}", "fiedler-mcp"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "true"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
