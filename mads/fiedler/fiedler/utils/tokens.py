"""Token estimation utilities."""

# Try to import tiktoken for better estimation (optional dependency)
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


def estimate_tokens(text: str, model_id: str = None) -> int:
    """
    Estimate token count for text.

    Uses tiktoken if available (more accurate), otherwise falls back to
    rough approximation of ~4 characters per token.

    Args:
        text: Input text
        model_id: Optional model ID for model-specific tokenization

    Returns:
        Estimated token count
    """
    if TIKTOKEN_AVAILABLE:
        try:
            # Try to get encoding for specific model
            if model_id:
                # Map model IDs to tiktoken encodings
                if "gpt" in model_id.lower():
                    encoding = tiktoken.encoding_for_model(model_id)
                    return len(encoding.encode(text))

            # Fallback to cl100k_base (GPT-4, GPT-3.5-turbo)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            # If tiktoken fails, fall back to rough estimation
            pass

    # Rough approximation: ~4 characters per token
    return len(text) // 4


def check_token_budget(
    text: str,
    context_window: int,
    max_completion_tokens: int,
    model_name: str
) -> tuple[bool, int, str]:
    """
    Check if text + completion budget fits within model's context window.

    Args:
        text: Input text (prompt + package)
        context_window: Model's total context window (input + output)
        max_completion_tokens: Model's maximum completion tokens
        model_name: Model name for warning message

    Returns:
        Tuple of (is_ok, estimated_input_tokens, warning_message)
    """
    estimated_input = estimate_tokens(text)
    total_needed = estimated_input + max_completion_tokens
    threshold = int(context_window * 0.8)  # Warn at 80%

    if total_needed > context_window:
        return (
            False,
            estimated_input,
            f"WARNING: {model_name}: Input ({estimated_input}) + completion ({max_completion_tokens}) "
            f"= {total_needed} tokens exceeds context window ({context_window})"
        )
    elif total_needed > threshold:
        return (
            True,
            estimated_input,
            f"WARNING: {model_name}: Input ({estimated_input}) + completion ({max_completion_tokens}) "
            f"= {total_needed} tokens near context window limit ({context_window})"
        )
    else:
        return (True, estimated_input, "")
