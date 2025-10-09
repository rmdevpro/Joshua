#!/usr/bin/env python3
"""
Direct Gemini API Client
A reliable tool for calling Google's Gemini API without MCP overhead.
"""

import argparse
import base64
import json
import os
import sys
import time
from typing import Dict, List, Optional, Any
import requests


class GeminiClient:
    """Direct client for Google's Gemini API"""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set GEMINI_API_KEY environment variable or pass --api-key")

        self.session = requests.Session()
        self.session.headers.update({
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        })

    def upload_file(self, file_data: bytes, mime_type: str, display_name: str = "file") -> Dict[str, Any]:
        """Upload file to Gemini File API for large file handling.

        Args:
            file_data: Raw file bytes
            mime_type: MIME type of the file
            display_name: Display name for the file

        Returns:
            Dict with 'uri', 'name', and 'state' keys
        """
        # Use upload subdomain for File API
        upload_url = self.BASE_URL.replace("generativelanguage.googleapis.com", "generativelanguage.googleapis.com/upload")
        url = f"{upload_url}/files?key={self.api_key}"

        # Prepare metadata part (JSON)
        file_metadata = {
            "file": {
                "display_name": display_name
            }
        }

        # Prepare multipart request with TWO parts: metadata + file
        files = {
            'metadata': (None, json.dumps(file_metadata), 'application/json'),
            'file': (display_name, file_data, mime_type)
        }

        try:
            # Don't set Content-Type - requests will auto-generate multipart/form-data
            response = requests.post(url, files=files, timeout=300)
            response.raise_for_status()
            result = response.json()

            # Extract file info
            file_info = result.get('file', {})
            file_name = file_info.get('name')

            # Wait for file to become ACTIVE (required before using in generateContent)
            if file_name and file_info.get('state') == 'PROCESSING':
                max_wait = 300  # 5 minutes max wait for large audio/video files
                wait_interval = 5  # Check every 5 seconds
                elapsed = 0
                consecutive_500_errors = 0
                max_consecutive_500 = 60  # Allow up to 60 consecutive 500s (5 minutes worth)

                while elapsed < max_wait:
                    time.sleep(wait_interval)
                    elapsed += wait_interval

                    # Poll file status (use standard URL, not upload URL)
                    status_url = f"{self.BASE_URL}/{file_name}?key={self.api_key}"

                    try:
                        status_response = requests.get(status_url, timeout=30)

                        # Handle transient 500 errors during processing
                        # File API returns 500s while file is processing - this is normal
                        if status_response.status_code == 500:
                            consecutive_500_errors += 1
                            if consecutive_500_errors >= max_consecutive_500:
                                # Too many 500s - file processing likely failed
                                return {"error": f"File processing timeout - {consecutive_500_errors} consecutive 500 errors"}
                            continue

                        # Reset 500 error counter on successful response
                        consecutive_500_errors = 0

                        status_response.raise_for_status()
                        status_result = status_response.json()

                        current_state = status_result.get('state')
                        if current_state == 'ACTIVE':
                            file_info = status_result
                            break
                        elif current_state == 'FAILED':
                            return {"error": f"File processing failed: {status_result.get('error', 'Unknown error')}"}
                        elif current_state == 'PROCESSING':
                            # Still processing - continue waiting
                            continue
                    except (requests.exceptions.RequestException, json.JSONDecodeError):
                        # Other transient errors during polling - continue
                        continue

            return {
                "uri": file_info.get('uri'),
                "name": file_info.get('name'),
                "state": file_info.get('state'),
                "size_bytes": file_info.get('sizeBytes'),
            }
        except requests.exceptions.RequestException as e:
            return {"error": f"File upload failed: {str(e)}"}

    def generate_content(
        self,
        prompt: str,
        model: str = "gemini-pro",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        safety_settings: Optional[List[Dict]] = None,
        stream: bool = False,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate content using Gemini API

        Args:
            prompt: Text prompt
            model: Gemini model to use
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            safety_settings: Safety configuration
            stream: Whether to stream response (not implemented)
            attachments: List of dicts with keys: 'mime_type', 'data' (bytes)
        """

        url = f"{self.BASE_URL}/models/{model}:generateContent"

        # Build parts array with text and optional attachments
        parts = [{"text": prompt}]

        # Size threshold for using File API (4MB = 4 * 1024 * 1024 bytes)
        FILE_API_THRESHOLD = 4 * 1024 * 1024

        if attachments:
            for i, attachment in enumerate(attachments):
                file_data = attachment["data"]
                mime_type = attachment["mime_type"]
                file_size = len(file_data)

                # Use File API for files > threshold, inline_data for smaller files
                if file_size > FILE_API_THRESHOLD:
                    # Upload file to File API
                    display_name = attachment.get("filename", f"attachment_{i}")
                    upload_result = self.upload_file(file_data, mime_type, display_name)

                    if "error" in upload_result:
                        return {"error": f"Failed to upload {display_name}: {upload_result['error']}"}

                    # Use file_data with URI from File API
                    parts.append({
                        "file_data": {
                            "mime_type": mime_type,
                            "file_uri": upload_result["uri"]
                        }
                    })
                else:
                    # Use inline_data for small files
                    encoded_data = base64.b64encode(file_data).decode('utf-8')
                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": encoded_data
                        }
                    })

        payload = {
            "contents": [
                {
                    "parts": parts
                }
            ],
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        if safety_settings:
            payload["safetySettings"] = safety_settings

        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json=payload, timeout=600)  # 10 minutes for large documents

                # Handle rate limiting
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                    else:
                        return {"error": "Rate limit exceeded after retries"}

                response.raise_for_status()
                result = response.json()
                return self._process_response(result)

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    return {"error": "Request timeout after retries"}

            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    return {"error": "Connection error after retries"}

            except requests.exceptions.RequestException as e:
                error_detail = str(e)
                # Try to get response body for more details
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_body = e.response.text
                        error_detail = f"{str(e)} | Response: {error_body[:500]}"
                    except:
                        pass
                return {"error": f"Request failed: {error_detail}"}

            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON response: {str(e)}"}

        return {"error": "Max retries exceeded"}

    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process API response and extract content"""

        if "error" in response:
            return {"error": response["error"]}

        candidates = response.get("candidates", [])
        if not candidates:
            return {"error": "No candidates in response"}

        candidate = candidates[0]

        # Check for content filtering
        if candidate.get("finishReason") == "SAFETY":
            safety_ratings = candidate.get("safetyRatings", [])
            return {
                "error": "Content filtered for safety",
                "safety_ratings": safety_ratings
            }

        # Extract content
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        if not parts:
            return {"error": "No content parts in response"}

        text = parts[0].get("text", "")

        return {
            "text": text,
            "finish_reason": candidate.get("finishReason"),
            "safety_ratings": candidate.get("safetyRatings", []),
            "usage": response.get("usageMetadata", {})
        }

    def list_models(self) -> Dict[str, Any]:
        """List available models"""
        url = f"{self.BASE_URL}/models"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to list models: {str(e)}"}


def get_safety_settings(level: str = "default") -> List[Dict]:
    """Get safety settings based on level"""

    categories = [
        "HARM_CATEGORY_HARASSMENT",
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT"
    ]

    if level == "strict":
        threshold = "BLOCK_LOW_AND_ABOVE"
    elif level == "minimal":
        threshold = "BLOCK_ONLY_HIGH"
    elif level == "none":
        threshold = "BLOCK_NONE"
    else:  # default
        threshold = "BLOCK_MEDIUM_AND_ABOVE"

    return [
        {"category": category, "threshold": threshold}
        for category in categories
    ]


def main():
    parser = argparse.ArgumentParser(description="Direct Gemini API Client")
    parser.add_argument("prompt", nargs="?", help="Text prompt to send")
    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY)")
    parser.add_argument("--model", default="gemini-pro", help="Model to use (default: gemini-pro)")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature (0.0-1.0)")
    parser.add_argument("--max-tokens", type=int, help="Maximum output tokens")
    parser.add_argument("--safety", choices=["strict", "default", "minimal", "none"],
                       default="default", help="Safety level")
    parser.add_argument("--json", action="store_true", help="Output JSON response")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--stdin", action="store_true", help="Read prompt from stdin")

    args = parser.parse_args()

    try:
        client = GeminiClient(args.api_key)

        if args.list_models:
            result = client.list_models()
            print(json.dumps(result, indent=2))
            return

        # Get prompt
        if args.stdin:
            prompt = sys.stdin.read().strip()
        elif args.prompt:
            prompt = args.prompt
        else:
            print("Error: Provide prompt as argument or use --stdin", file=sys.stderr)
            sys.exit(1)

        if not prompt:
            print("Error: Empty prompt", file=sys.stderr)
            sys.exit(1)

        # Generate content
        safety_settings = get_safety_settings(args.safety)

        result = client.generate_content(
            prompt=prompt,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            safety_settings=safety_settings
        )

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if "error" in result:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
            else:
                print(result.get("text", ""))

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()