"""Comprehensive end-to-end tests for ALL Fiedler models."""
import pytest
import os
from pathlib import Path
from fiedler.tools.send import fiedler_send


def check_api_keys():
    """Check if API keys are configured."""
    keys = {
        "gemini": os.getenv("GEMINI_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
        "together": os.getenv("TOGETHER_API_KEY"),
        "xai": os.getenv("XAI_API_KEY"),
    }
    return {k: bool(v and v != "your_api_key_here") for k, v in keys.items()}


@pytest.fixture
def test_prompt():
    """Simple test prompt that should work with all models."""
    return "Respond with exactly: 'OK'"


@pytest.fixture
def test_output_dir(tmp_path):
    """Set up test output directory."""
    output_dir = tmp_path / "fiedler_all_models_output"
    output_dir.mkdir()
    os.environ["FIEDLER_OUTPUT_DIR"] = str(output_dir)
    return output_dir


# Google Models
@pytest.mark.skipif(
    not check_api_keys().get("gemini", False),
    reason="GEMINI_API_KEY not configured"
)
def test_gemini_2_5_pro(test_prompt, test_output_dir):
    """Test Gemini 2.5 Pro."""
    result = fiedler_send(prompt=test_prompt, files=None, models=["gemini-2.5-pro"])
    assert result["status"] in ["success", "partial_success"]
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success"
    print(f"✓ Gemini 2.5 Pro: {result['results'][0]['duration']:.1f}s")


# OpenAI Models
@pytest.mark.skipif(
    not check_api_keys().get("openai", False),
    reason="OPENAI_API_KEY not configured"
)
def test_gpt_5(test_prompt, test_output_dir):
    """Test GPT-5 (o4-mini)."""
    result = fiedler_send(prompt=test_prompt, files=None, models=["gpt-5"])
    assert result["status"] in ["success", "partial_success"]
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success"
    print(f"✓ GPT-5: {result['results'][0]['duration']:.1f}s")


# Together AI Models (6 models)
@pytest.mark.skipif(
    not check_api_keys().get("together", False),
    reason="TOGETHER_API_KEY not configured"
)
def test_llama_3_1_70b(test_prompt, test_output_dir):
    """Test Llama 3.1 70B Instruct Turbo."""
    result = fiedler_send(prompt=test_prompt, files=None, models=["llama-70b"])
    assert result["status"] in ["success", "partial_success"]
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success"
    print(f"✓ Llama 3.1 70B: {result['results'][0]['duration']:.1f}s")


@pytest.mark.skipif(
    not check_api_keys().get("together", False),
    reason="TOGETHER_API_KEY not configured"
)
def test_llama_3_3_70b(test_prompt, test_output_dir):
    """Test Llama 3.3 70B Instruct Turbo."""
    result = fiedler_send(prompt=test_prompt, files=None, models=["llama-3.3"])
    assert result["status"] in ["success", "partial_success"]
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success"
    print(f"✓ Llama 3.3 70B: {result['results'][0]['duration']:.1f}s")


@pytest.mark.skipif(
    not check_api_keys().get("together", False),
    reason="TOGETHER_API_KEY not configured"
)
def test_deepseek_r1(test_prompt, test_output_dir):
    """Test DeepSeek R1."""
    result = fiedler_send(prompt=test_prompt, files=None, models=["deepseek"])
    assert result["status"] in ["success", "partial_success"]
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success"
    print(f"✓ DeepSeek R1: {result['results'][0]['duration']:.1f}s")


@pytest.mark.skipif(
    not check_api_keys().get("together", False),
    reason="TOGETHER_API_KEY not configured"
)
def test_qwen_2_5_72b(test_prompt, test_output_dir):
    """Test Qwen 2.5 72B Instruct Turbo."""
    result = fiedler_send(prompt=test_prompt, files=None, models=["qwen"])
    assert result["status"] in ["success", "partial_success"]
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success"
    print(f"✓ Qwen 2.5 72B: {result['results'][0]['duration']:.1f}s")


# DISABLED: Mistral-Large-2411 - Model not available on Together AI (404 error)
# DISABLED: nvidia/Llama-3.1-Nemotron-70B-Instruct-HF - Requires dedicated endpoint (non-serverless)


# xAI Models
@pytest.mark.skipif(
    not check_api_keys().get("xai", False),
    reason="XAI_API_KEY not configured"
)
def test_grok_4(test_prompt, test_output_dir):
    """Test Grok 4."""
    result = fiedler_send(prompt=test_prompt, files=None, models=["grok-4"])
    assert result["status"] in ["success", "partial_success"]
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success"
    print(f"✓ Grok 4: {result['results'][0]['duration']:.1f}s")


# Comprehensive parallel test
def test_all_models_parallel(test_prompt, test_output_dir):
    """Test ALL models in parallel."""
    available_keys = check_api_keys()
    models = []

    # Add all available models
    if available_keys.get("gemini"):
        models.append("gemini-2.5-pro")
    if available_keys.get("openai"):
        models.append("gpt-5")
    if available_keys.get("together"):
        models.extend(["llama-70b", "llama-3.3", "deepseek", "qwen"])
    if available_keys.get("xai"):
        models.append("grok-4")

    if len(models) < 2:
        pytest.skip("Need at least 2 API keys configured")

    print(f"\nTesting {len(models)} models in parallel...")
    result = fiedler_send(prompt=test_prompt, files=None, models=models)

    # Check all models succeeded
    assert result["status"] in ["success", "partial_success"]
    assert len(result["results"]) == len(models)

    success_count = sum(1 for r in result["results"] if r["status"] == "success")
    print(f"\n✓ {success_count}/{len(models)} models succeeded")

    # Print individual results
    for model_result in sorted(result["results"], key=lambda x: x["duration"]):
        status_icon = "✓" if model_result["status"] == "success" else "✗"
        print(f"{status_icon} {model_result['model']}: {model_result['duration']:.1f}s")

    # Require all to succeed
    assert success_count == len(models), f"Only {success_count}/{len(models)} models succeeded"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
