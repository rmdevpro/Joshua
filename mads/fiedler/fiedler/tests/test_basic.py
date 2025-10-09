"""Basic tests for Fiedler MCP Server."""
import pytest
from pathlib import Path
import yaml

from fiedler.tools.models import fiedler_list_models, build_alias_map
from fiedler.tools.config import fiedler_set_models, fiedler_set_output, fiedler_get_config
from fiedler.utils.tokens import estimate_tokens, check_token_budget


def test_list_models():
    """Test that fiedler_list_models returns expected structure."""
    result = fiedler_list_models()

    assert "models" in result
    assert isinstance(result["models"], list)
    assert len(result["models"]) > 0

    # Check first model has required fields
    model = result["models"][0]
    assert "name" in model
    assert "provider" in model
    assert "aliases" in model
    assert "max_tokens" in model
    assert "capabilities" in model


def test_build_alias_map():
    """Test alias resolution."""
    config = {
        "providers": {
            "google": {
                "models": {
                    "gemini-2.5-pro": {
                        "aliases": ["gemini", "gemini-pro"]
                    }
                }
            }
        }
    }

    alias_map = build_alias_map(config)

    assert alias_map["gemini-2.5-pro"] == "gemini-2.5-pro"
    assert alias_map["gemini"] == "gemini-2.5-pro"
    assert alias_map["gemini-pro"] == "gemini-2.5-pro"


def test_set_models():
    """Test fiedler_set_models with valid aliases."""
    result = fiedler_set_models(["gemini", "gpt-5"])

    assert result["status"] == "configured"
    assert "gemini-2.5-pro" in result["models"]
    assert "gpt-5" in result["models"]
    assert "models configured" in result["message"]


def test_set_models_invalid():
    """Test fiedler_set_models with invalid model."""
    with pytest.raises(ValueError, match="Unknown model or alias"):
        fiedler_set_models(["invalid-model"])


def test_set_output():
    """Test fiedler_set_output."""
    test_dir = "/tmp/fiedler_test_output"
    result = fiedler_set_output(test_dir)

    assert result["status"] == "configured"
    assert result["output_dir"] == test_dir


def test_get_config():
    """Test fiedler_get_config returns all fields."""
    result = fiedler_get_config()

    assert "models" in result
    assert "output_dir" in result
    assert "total_available_models" in result
    assert isinstance(result["models"], list)
    assert isinstance(result["total_available_models"], int)


def test_estimate_tokens():
    """Test token estimation."""
    text = "hello world" * 100  # 1100 chars
    tokens = estimate_tokens(text)

    # ~4-5 chars/token with fallback estimation
    # tiktoken might give more accurate results if available
    assert 150 <= tokens <= 400


def test_check_token_budget():
    """Test token budget checking with new context_window + max_completion_tokens semantics."""
    # Within budget (small input + completion)
    within, estimated, warning = check_token_budget(
        "hello" * 10,
        context_window=10000,
        max_completion_tokens=4000,
        model_name="test-model"
    )
    assert within is True
    assert warning == ""

    # Warning threshold (>80% of context window)
    # With tiktoken: "x" * 3000 = ~375 tokens
    # Need total > 800 (80% of 1000), so use larger completion budget
    within, estimated, warning = check_token_budget(
        "x" * 3000,  # ~375 tokens with tiktoken
        context_window=1000,
        max_completion_tokens=500,  # Total: ~875 tokens (87.5% of 1000)
        model_name="test-model"
    )
    assert within is True
    assert "WARNING" in warning or "near context window limit" in warning

    # Over budget (input + completion exceeds context window)
    # With tiktoken: "x" * 4000 = ~500 tokens
    within, estimated, warning = check_token_budget(
        "x" * 4000,  # ~500 tokens with tiktoken
        context_window=1000,
        max_completion_tokens=600,  # Total: ~1100 tokens > 1000
        model_name="test-model"
    )
    assert within is False
    assert "exceeds" in warning


def test_models_yaml_structure():
    """Test that config/models.yaml has correct structure."""
    config_path = Path(__file__).parent.parent / "fiedler" / "config" / "models.yaml"

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    assert "providers" in config
    assert "defaults" in config

    # Check defaults
    assert "models" in config["defaults"]
    assert "output_dir" in config["defaults"]

    # Check each provider
    for provider_name, provider_config in config["providers"].items():
        assert "api_key_env" in provider_config
        assert "models" in provider_config

        # Check each model
        for model_id, model_config in provider_config["models"].items():
            assert "aliases" in model_config
            assert "max_tokens" in model_config
            assert "capabilities" in model_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
