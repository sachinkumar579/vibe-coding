"""
test_connection.py — Azure OpenAI Connection Test
--------------------------------------------------
Run this before the agent to verify your Azure OpenAI
credentials and deployment are working correctly.

Usage:
    export AZURE_OPENAI_KEY=your-azure-key-here
    export AZURE_ENDPOINT=your-endpoint-here
    python test_connection.py
"""

import os
import sys
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# ─── Same config as agent.py ──────────────────────────────────────────────────

AZURE_ENDPOINT    =  os.environ.get("AZURE_ENDPOINT")
AZURE_DEPLOYMENT  = "gpt-4o-mini"
AZURE_API_VERSION = "2024-12-01-preview"

# ─── Checks ───────────────────────────────────────────────────────────────────

def check_api_key() -> str:
    print("─" * 50)
    print("1️⃣  Checking AZURE_OPENAI_KEY env variable...")
    key =  os.environ.get("AZURE_OPENAI_KEY")
    if not key:
        print("   ❌ AZURE_OPENAI_KEY is not set.")
        print("      Run: export AZURE_OPENAI_KEY=your-key-here")
        sys.exit(1)
    masked = key[:6] + "*" * (len(key) - 6)
    print(f"   ✅ Found key: {masked}")
    return key


def check_simple_call(client: AzureOpenAI):
    print("─" * 50)
    print("2️⃣  Sending a simple test prompt...")
    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[{"role": "user", "content": "Reply with exactly: CONNECTION OK"}],
        temperature=0,
        max_tokens=10,
    )
    reply = response.choices[0].message.content.strip()
    print(f"   ✅ Response  : {reply}")
    print(f"   ✅ Model     : {response.model}")
    print(f"   ✅ Finish    : {response.choices[0].finish_reason}")


def check_token_usage(client: AzureOpenAI):
    print("─" * 50)
    print("3️⃣  Checking token usage reporting...")
    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[{"role": "user", "content": "Say hello in one word."}],
        temperature=0,
        max_tokens=10,
    )
    u = response.usage
    print(f"   ✅ Prompt tokens     : {u.prompt_tokens}")
    print(f"   ✅ Completion tokens : {u.completion_tokens}")
    print(f"   ✅ Total tokens      : {u.total_tokens}")


def check_json_mode(client: AzureOpenAI):
    print("─" * 50)
    print("4️⃣  Checking JSON response mode (used by agent)...")
    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[{
            "role": "user",
            "content": 'Return a JSON object with keys "status" and "message".'
        }],
        temperature=0,
        max_tokens=50,
        response_format={"type": "json_object"},
    )
    import json
    parsed = json.loads(response.choices[0].message.content)
    print(f"   ✅ Parsed JSON : {parsed}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n🔧 Azure OpenAI Connection Test")
    print(f"   Endpoint   : {AZURE_ENDPOINT}")
    print(f"   Deployment : {AZURE_DEPLOYMENT}")
    print(f"   API Version: {AZURE_API_VERSION}\n")

    key = check_api_key()

    client = AzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=key,
        api_version=AZURE_API_VERSION,
    )

    try:
        check_simple_call(client)
        check_token_usage(client)
        check_json_mode(client)
    except Exception as e:
        print(f"\n   ❌ Test failed: {e}")
        sys.exit(1)

    print("─" * 50)
    print("\n✅ All checks passed — agent.py is ready to run!\n")


if __name__ == "__main__":
    main()