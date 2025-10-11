"""fiedler_send tool implementation."""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import json
import asyncio

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


async def send_to_model(
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
            await logger.log("WARN", warning, "fiedler-tools", data={"model": model_id})

        # Create output file
        output_file = output_dir / f"{model_id.replace('/', '_')}.md"

        # Send (with attachments if provider supports them)
        await logger.log("INFO", f"Sending to {model_id}...", "fiedler-tools", data={"model": model_id})
        result = await provider.send(package, prompt, output_file, logger, attachments=attachments)

        if result["success"]:
            await logger.log("INFO", f"{model_id} completed in {result['duration']:.1f}s", "fiedler-tools", data={"model": model_id})
            return {
                "model": model_id,
                "status": "success",
                "output_file": str(output_file),
                "duration": result["duration"],
                "tokens": result.get("tokens", {}),
            }
        else:
            await logger.log("ERROR", f"{model_id} failed: {result.get('error', 'unknown error')}", "fiedler-tools", data={"model": model_id})
            return {
                "model": model_id,
                "status": "failed",
                "error": result.get("error", "unknown error"),
            }

    except Exception as e:
        await logger.log("ERROR", f"{model_id} exception: {str(e)}", "fiedler-tools", data={"model": model_id})
        return {
            "model": model_id,
            "status": "failed",
            "error": str(e),
        }


async def fiedler_send(
    prompt: str,
    files: Optional[List[str]] = None,
    models: Optional[List[str]] = None,
    correlation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send prompt and optional package to configured models.

    Args:
        prompt: User prompt/question
        files: Optional list of file paths to compile into package
        models: Optional override of default models
        correlation_id: Optional pre-generated correlation ID

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
    # FIXED: Use provided correlation_id or generate a new one
    cid = correlation_id or str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_base) / f"{timestamp}_{cid}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logger
    log_file = output_dir / "fiedler.log"
    logger = ProgressLogger(cid, log_file)

    await logger.log("INFO", f"Starting Fiedler run (correlation_id: {cid})", "fiedler-tools")
    await logger.log("INFO", f"Models: {', '.join(models)}", "fiedler-tools")
    await logger.log("INFO", f"Output: {output_dir}", "fiedler-tools")

    # Compile package if files provided
    package = ""
    package_metadata = {}
    binary_files = []
    if files:
        await logger.log("INFO", f"Compiling package from {len(files)} file(s)", "fiedler-tools")
        package, package_metadata, binary_files = await compile_package(files, logger)
        await logger.log("INFO", f"Package compiled: {package_metadata['total_size']} bytes, {package_metadata['total_lines']} lines", "fiedler-tools")

    # Resolve binary files as attachments for multimodal handling
    attachments = []
    if binary_files:
        await logger.log("INFO", f"Resolving {len(binary_files)} binary file(s) as attachments...", "fiedler-tools")
        for binary_file in binary_files:
            file_name = Path(binary_file).name
            await logger.log("INFO", f"  Resolving: {file_name}", "fiedler-tools")

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
                await logger.log("INFO", f"  {file_name}: {resolution.mime_type}, {len(content_bytes):,} bytes, sha256={resolution.sha256_hash[:16]}...", "fiedler-tools")
            else:
                await logger.log("ERROR", f"  {file_name}: {resolution.error_message}", "fiedler-tools")
                raise ValueError(f"Failed to resolve attachment {file_name}: {resolution.error_message}")

    # Send to models in parallel
    results = []

    # Cap parallelism based on CPU count and environment variable
    max_workers = min(
        len(models),
        int(os.getenv("FIEDLER_MAX_WORKERS", str(max(2, (os.cpu_count() or 4)))))
    )

    await logger.log("INFO", f"Sending to {len(models)} model(s) in parallel (max_workers={max_workers})", "fiedler-tools")

    # Use asyncio.gather for parallel async execution
    tasks = [
        send_to_model(
            model_id,
            package,
            prompt,
            output_dir,
            cid,
            config,
            logger,
            attachments=attachments if attachments else None
        )
        for model_id in models
    ]

    results = await asyncio.gather(*tasks)

    # Create summary (with optional prompt redaction for security)
    save_prompt = os.getenv("FIEDLER_SAVE_PROMPT", "0") == "1"
    summary = {
        "correlation_id": cid,
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

    await logger.log("INFO", f"Run complete: {success_count}/{len(models)} models succeeded", "fiedler-tools")

    return {
        "status": status,
        "correlation_id": cid,
        "output_dir": str(output_dir),
        "summary_file": str(summary_file),
        "results": results,
        "message": f"{success_count}/{len(models)} models succeeded"
    }
