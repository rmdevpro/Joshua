"""fiedler_send tool implementation."""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
import json

from ..utils import get_models, get_output_dir
from ..utils.logger import ProgressLogger
from ..utils.package import compile_package
from ..utils.tokens import check_token_budget
from ..utils.attachments import Attachment, resolve_attachment, ResolutionStatus
from ..providers import GeminiProvider, OpenAIProvider, TogetherProvider, XAIProvider


def create_provider(model_id: str, config: Dict[str, Any]):
    """Factory function to create appropriate provider."""
    # Find model in config
    for provider_name, provider_config in config["providers"].items():
        if model_id in provider_config["models"]:
            model_config = provider_config["models"][model_id]
            api_key_env = provider_config["api_key_env"]

            if provider_name == "google":
                return GeminiProvider(model_id, model_config, api_key_env)
            elif provider_name == "openai":
                return OpenAIProvider(model_id, model_config, api_key_env)
            elif provider_name == "together":
                base_url = provider_config.get("base_url", "https://api.together.xyz/v1")
                return TogetherProvider(model_id, model_config, api_key_env, base_url)
            elif provider_name == "xai":
                return XAIProvider(model_id, model_config, api_key_env)

    raise ValueError(f"Unknown model: {model_id}")


def send_to_model(
    model_id: str,
    package: str,
    prompt: str,
    output_dir: Path,
    correlation_id: str,
    config: Dict[str, Any],
    logger: ProgressLogger,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Send to single model (runs in thread)."""
    try:
        # Create provider
        provider = create_provider(model_id, config)

        # Check token budget (only for text content, attachments handled separately)
        full_input = f"{prompt}\n\n{package}" if package else prompt
        within_budget, estimated, warning = check_token_budget(
            full_input,
            provider.context_window,
            provider.max_completion_tokens,
            model_id
        )
        if warning:
            logger.log(warning, model_id)

        # Create output file
        output_file = output_dir / f"{model_id.replace('/', '_')}.md"

        # Send (with attachments if provider supports them)
        logger.log(f"Sending to {model_id}...", model_id)
        result = provider.send(package, prompt, output_file, logger, attachments=attachments)

        if result["success"]:
            logger.log(f"✓ {model_id} completed in {result['duration']:.1f}s", model_id)
            return {
                "model": model_id,
                "status": "success",
                "output_file": str(output_file),
                "duration": result["duration"],
                "tokens": result.get("tokens", {}),
            }
        else:
            logger.log(f"✗ {model_id} failed: {result.get('error', 'unknown error')}", model_id)
            return {
                "model": model_id,
                "status": "failed",
                "error": result.get("error", "unknown error"),
            }

    except Exception as e:
        logger.log(f"✗ {model_id} exception: {str(e)}", model_id)
        return {
            "model": model_id,
            "status": "failed",
            "error": str(e),
        }


def fiedler_send(
    prompt: str,
    files: Optional[List[str]] = None,
    models: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send prompt and optional package to configured models.

    Args:
        prompt: User prompt/question
        files: Optional list of file paths to compile into package
        models: Optional override of default models

    Returns:
        Dict with status, correlation_id, output_dir, results per model
    """
    # Load config
    from ..utils.paths import get_config_path
    from .models import build_alias_map

    config_path = get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Get models (use override or defaults)
    if models is None:
        models = get_models()
        if not models:
            # Fall back to config defaults
            models = config.get("defaults", {}).get("models", ["gemini-2.5-pro"])
    else:
        # Resolve aliases if models provided as override
        alias_map = build_alias_map(config)
        resolved = []
        for m in models:
            if m in alias_map:
                resolved.append(alias_map[m])
            else:
                raise ValueError(f"Unknown model or alias: {m}")
        models = resolved

    # Validate models list
    if not models:
        raise ValueError("No models configured. Use fiedler_set_models or pass models to fiedler_send.")

    # Get output directory
    output_base = get_output_dir()

    # Create correlation ID and timestamped directory
    correlation_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_base) / f"{timestamp}_{correlation_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logger
    log_file = output_dir / "fiedler.log"
    logger = ProgressLogger(correlation_id, log_file)

    logger.log(f"Starting Fiedler run (correlation_id: {correlation_id})")
    logger.log(f"Models: {', '.join(models)}")
    logger.log(f"Output: {output_dir}")

    # Compile package if files provided
    package = ""
    package_metadata = {}
    binary_files = []
    if files:
        logger.log(f"Compiling package from {len(files)} file(s)")
        package, package_metadata, binary_files = compile_package(files, logger)
        logger.log(f"Package compiled: {package_metadata['total_size']} bytes, {package_metadata['total_lines']} lines")

    # Resolve binary files as attachments for multimodal handling
    attachments = []
    if binary_files:
        logger.log(f"Resolving {len(binary_files)} binary file(s) as attachments...")
        for binary_file in binary_files:
            file_name = Path(binary_file).name
            logger.log(f"  Resolving: {file_name}")

            attachment = Attachment(source="file", content=binary_file)
            resolution = resolve_attachment(attachment)

            if resolution.status == ResolutionStatus.SUCCESS:
                # Convert stream to bytes for provider handling
                content_bytes = b"".join(resolution.content_stream())
                attachments.append({
                    "filename": file_name,
                    "mime_type": resolution.mime_type,
                    "data": content_bytes,
                    "sha256": resolution.sha256_hash
                })
                logger.log(f"  ✓ {file_name}: {resolution.mime_type}, {len(content_bytes):,} bytes, sha256={resolution.sha256_hash[:16]}...")
            else:
                logger.log(f"  ✗ {file_name}: {resolution.error_message}")
                raise ValueError(f"Failed to resolve attachment {file_name}: {resolution.error_message}")

    # Send to models in parallel
    results = []

    # Cap parallelism based on CPU count and environment variable
    max_workers = min(
        len(models),
        int(os.getenv("FIEDLER_MAX_WORKERS", str(max(2, (os.cpu_count() or 4)))))
    )

    logger.log(f"Sending to {len(models)} model(s) in parallel (max_workers={max_workers})")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                send_to_model,
                model_id,
                package,
                prompt,
                output_dir,
                correlation_id,
                config,
                logger,
                attachments=attachments if attachments else None
            ): model_id
            for model_id in models
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    # Create summary (with optional prompt redaction for security)
    save_prompt = os.getenv("FIEDLER_SAVE_PROMPT", "0") == "1"
    summary = {
        "correlation_id": correlation_id,
        "timestamp": timestamp,
        "prompt": prompt if save_prompt else f"<redacted - {len(prompt)} chars>",
        "prompt_length": len(prompt),
        "files": files or [],
        "package_metadata": package_metadata,
        "models": models,
        "results": results,
    }

    summary_file = output_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Determine overall status
    success_count = sum(1 for r in results if r["status"] == "success")
    if success_count == len(models):
        status = "success"
    elif success_count > 0:
        status = "partial_success"
    else:
        status = "failure"

    logger.log(f"Run complete: {success_count}/{len(models)} models succeeded")

    return {
        "status": status,
        "correlation_id": correlation_id,
        "output_dir": str(output_dir),
        "summary_file": str(summary_file),
        "results": results,
        "message": f"{success_count}/{len(models)} models succeeded"
    }
