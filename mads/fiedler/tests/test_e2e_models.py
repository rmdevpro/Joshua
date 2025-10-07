"""End-to-end tests for Fiedler model invocations."""
import pytest
import os
from pathlib import Path
from fiedler.tools.send import fiedler_send


# Skip if no API keys configured
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
    output_dir = tmp_path / "fiedler_e2e_output"
    output_dir.mkdir()
    os.environ["FIEDLER_OUTPUT_DIR"] = str(output_dir)
    return output_dir


@pytest.mark.skipif(
    not check_api_keys().get("gemini", False),
    reason="GEMINI_API_KEY not configured"
)
def test_gemini_2_5_pro(test_prompt, test_output_dir):
    """Test Gemini 2.5 Pro end-to-end."""
    result = fiedler_send(
        prompt=test_prompt,
        files=None,
        models=["gemini-2.5-pro"]
    )

    # Check structure
    assert "correlation_id" in result
    assert "results" in result
    assert len(result["results"]) == 1

    # Check Gemini result
    gemini_result = result["results"][0]
    assert gemini_result["model"] == "gemini-2.5-pro"
    assert gemini_result["status"] == "success"
    assert "output_file" in gemini_result

    # Read the response from output file
    from pathlib import Path
    output_file = Path(gemini_result["output_file"])
    assert output_file.exists()
    response = output_file.read_text()
    assert len(response) > 0

    print(f"Gemini 2.5 Pro response: {response[:100]}")


@pytest.mark.skipif(
    not check_api_keys().get("openai", False),
    reason="OPENAI_API_KEY not configured"
)
def test_gpt_5(test_prompt, test_output_dir):
    """Test GPT-5 end-to-end."""
    result = fiedler_send(
        prompt=test_prompt,
        files=None,
        models=["gpt-5"]
    )

    # Check structure
    assert "correlation_id" in result
    assert "results" in result
    assert len(result["results"]) == 1

    # Check GPT-5 result
    from pathlib import Path
    gpt5_result = result["results"][0]
    assert gpt5_result["model"] == "gpt-5"
    assert gpt5_result["status"] == "success"
    output_file = Path(gpt5_result["output_file"])
    response = output_file.read_text()
    assert len(response) > 0

    print(f"GPT-5 response: {response[:100]}")


@pytest.mark.skipif(
    not check_api_keys().get("together", False),
    reason="TOGETHER_API_KEY not configured"
)
def test_llama_70b(test_prompt, test_output_dir):
    """Test Llama 3.1 70B end-to-end."""
    result = fiedler_send(
        prompt=test_prompt,
        files=None,
        models=["llama-70b"]
    )

    # Check structure
    assert "correlation_id" in result
    assert "results" in result
    assert len(result["results"]) == 1

    # Check Llama result
    from pathlib import Path
    llama_result = result["results"][0]
    assert llama_result["model"] == "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    assert llama_result["status"] == "success"
    output_file = Path(llama_result["output_file"])
    response = output_file.read_text()
    assert len(response) > 0

    print(f"Llama 3.1 70B response: {response[:100]}")


@pytest.mark.skipif(
    not check_api_keys().get("xai", False),
    reason="XAI_API_KEY not configured"
)
def test_grok_4(test_prompt, test_output_dir):
    """Test Grok 4 end-to-end."""
    result = fiedler_send(
        prompt=test_prompt,
        files=None,
        models=["grok-4"]
    )

    # Check structure
    assert "correlation_id" in result
    assert "results" in result
    assert len(result["results"]) == 1

    # Check Grok result
    from pathlib import Path
    grok_result = result["results"][0]
    assert grok_result["model"] == "grok-4-0709"
    assert grok_result["status"] == "success"
    output_file = Path(grok_result["output_file"])
    response = output_file.read_text()
    assert len(response) > 0

    print(f"Grok 4 response: {response[:100]}")


def test_multiple_models_parallel(test_prompt, test_output_dir):
    """Test sending to multiple models in parallel."""
    # Get available models based on API keys
    available_keys = check_api_keys()
    models = []

    if available_keys.get("gemini"):
        models.append("gemini-2.5-pro")
    if available_keys.get("openai"):
        models.append("gpt-5")
    if available_keys.get("together"):
        models.append("llama-70b")
    if available_keys.get("xai"):
        models.append("grok-4")

    if len(models) < 2:
        pytest.skip("Need at least 2 API keys configured for parallel test")

    result = fiedler_send(
        prompt=test_prompt,
        files=None,
        models=models
    )

    # Check structure
    assert "correlation_id" in result
    assert "results" in result
    assert len(result["results"]) == len(models)

    # Check all models returned success
    from pathlib import Path
    # Build alias to model ID map
    model_aliases = {
        "gemini-2.5-pro": "gemini-2.5-pro",
        "gpt-5": "gpt-5",
        "llama-70b": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "grok-4": "grok-4-0709"
    }
    expected_model_ids = [model_aliases[m] for m in models]

    for model_result in result["results"]:
        assert model_result["model"] in expected_model_ids
        assert model_result["status"] == "success"
        output_file = Path(model_result["output_file"])
        response = output_file.read_text()
        print(f"{model_result['model']}: {response[:50]}")


def test_with_file_package(test_output_dir, tmp_path):
    """Test sending with a file package."""
    available_keys = check_api_keys()

    # Pick first available model
    model = None
    if available_keys.get("openai"):
        model = "gpt-5"
    elif available_keys.get("gemini"):
        model = "gemini-2.5-pro"
    elif available_keys.get("xai"):
        model = "grok-4"
    elif available_keys.get("together"):
        model = "llama-70b"

    if not model:
        pytest.skip("No API keys configured")

    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("This is test content for the file package.")

    # Set allowed roots to include tmp_path
    os.environ["FIEDLER_ALLOWED_FILE_ROOTS"] = str(tmp_path)

    result = fiedler_send(
        prompt="What does the provided file contain? Respond in one sentence.",
        files=[str(test_file)],
        models=[model]
    )

    # Check structure
    from pathlib import Path
    assert "correlation_id" in result
    assert "results" in result
    assert len(result["results"]) == 1

    model_result = result["results"][0]
    assert model_result["model"] == model
    assert model_result["status"] == "success"
    output_file = Path(model_result["output_file"])
    response = output_file.read_text()

    # Response should mention the file content
    response_lower = response.lower()
    assert "test" in response_lower or "content" in response_lower or "file" in response_lower

    print(f"{model} with file: {response[:100]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
