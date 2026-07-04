"""List models your GEMINI_API_KEY can use with the Live API.

A model works with Gemini Live only if it supports the `bidiGenerateContent`
action. Run this if the worker fails with "model ... is not found / not supported
for bidiGenerateContent" and set GEMINI_MODEL in .env to one of the printed IDs.

    uv run python list_models.py
"""

from __future__ import annotations

from google import genai

from config import config


def main() -> None:
    if not config.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY is not set (source your .env first)")

    client = genai.Client(
        api_key=config.gemini_api_key,
    )

    print("Models supporting the Live API (bidiGenerateContent):")
    found = False
    for model in client.models.list():
        actions = getattr(model, "supported_actions", None) or []
        if "bidiGenerateContent" in actions:
            found = True
            print(f"  {model.name}")
    if not found:
        print("  (none found for this API version - try GEMINI_API_VERSION=v1beta)")


if __name__ == "__main__":
    main()
