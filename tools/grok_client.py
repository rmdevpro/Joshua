#!/usr/bin/env python3
"""
Grok API Client - OpenAI-Compatible Integration
Uses OpenAI Python SDK with xAI endpoint for Grok models
"""

import os
import sys
from openai import OpenAI

class GrokClient:
    """Client for xAI's Grok API using OpenAI-compatible interface"""

    def __init__(self, api_key: str = None):
        """
        Initialize Grok client with xAI API key

        Args:
            api_key: xAI API key (defaults to XAI_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('XAI_API_KEY')
        if not self.api_key:
            raise ValueError("XAI_API_KEY not provided and not found in environment")

        # Initialize OpenAI client with xAI endpoint
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1"
        )

    def chat(self, prompt: str, model: str = "grok-2-1212", temperature: float = 0.2, max_tokens: int = 16384):
        """
        Send a chat completion request to Grok

        Args:
            prompt: The user prompt/question
            model: Grok model name (default: grok-2-1212)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            str: Grok's response text
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"Error calling Grok API: {e}", file=sys.stderr)
            raise

    def analyze_document(self, document_path: str, analysis_prompt: str, model: str = "grok-2-1212"):
        """
        Analyze a document using Grok

        Args:
            document_path: Path to document file
            analysis_prompt: Analysis instructions
            model: Grok model name

        Returns:
            str: Grok's analysis
        """
        with open(document_path, 'r', encoding='utf-8') as f:
            document_content = f.read()

        combined_prompt = f"{analysis_prompt}\n\n---\n\nDOCUMENT CONTENT:\n\n{document_content}"

        return self.chat(combined_prompt, model=model)


def main():
    """CLI interface for Grok client"""
    import argparse

    parser = argparse.ArgumentParser(description='Grok API Client')
    parser.add_argument('--model', default='grok-2-1212', help='Grok model to use')
    parser.add_argument('--temperature', type=float, default=0.2, help='Sampling temperature')
    parser.add_argument('--max-tokens', type=int, default=16384, help='Maximum output tokens')
    parser.add_argument('--file', help='Analyze a file with Grok')
    parser.add_argument('prompt', nargs='?', help='Direct prompt (or analysis instructions for --file)')

    args = parser.parse_args()

    # Get API key from environment
    api_key = os.environ.get('XAI_API_KEY')
    if not api_key:
        print("Error: XAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    client = GrokClient(api_key=api_key)

    try:
        if args.file:
            # File analysis mode
            if not args.prompt:
                print("Error: Analysis prompt required when using --file", file=sys.stderr)
                sys.exit(1)
            result = client.analyze_document(args.file, args.prompt, model=args.model)
        else:
            # Direct chat mode
            if not args.prompt:
                print("Error: Prompt required", file=sys.stderr)
                sys.exit(1)
            result = client.chat(args.prompt, model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)

        print(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
