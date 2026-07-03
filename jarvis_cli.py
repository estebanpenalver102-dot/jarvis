#!/usr/bin/env python3
"""
JARVIS terminal client — talk to your JARVIS instance directly from the shell.

Usage:
    python3 jarvis_cli.py                    # connects to http://localhost:8000
    python3 jarvis_cli.py --url https://jarvis-api-fufo.onrender.com
    JARVIS_URL=https://your-instance python3 jarvis_cli.py

Works against any running JARVIS API — your own `docker compose up` instance,
or a deployed one (Render, etc). No extra dependencies beyond `requests`
(already in any JARVIS-adjacent Python env; `pip install requests` otherwise).
"""
import argparse
import os
import sys
import uuid

import requests


def main():
    parser = argparse.ArgumentParser(description="JARVIS terminal client")
    parser.add_argument(
        "--url",
        default=os.environ.get("JARVIS_URL", "http://localhost:8000"),
        help="Base URL of the JARVIS API (default: $JARVIS_URL or http://localhost:8000)",
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Route messages through the multi-agent orchestrator instead of plain chat",
    )
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    session_id = str(uuid.uuid4())
    mode = "agent" if args.agent else "text"

    print(f"JARVIS terminal — connected to {base_url} (mode: {mode})")
    print("Type 'exit' or Ctrl+C to quit.\n")

    while True:
        try:
            message = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            break
        if not message:
            continue
        if message.lower() in ("exit", "quit"):
            print("bye.")
            break

        try:
            resp = requests.post(
                f"{base_url}/chat",
                json={"message": message, "session_id": session_id, "mode": mode},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"[connection error: {e}]")
            continue

        agent_tag = f" [{data['agent_used']}]" if data.get("agent_used") else ""
        print(f"jarvis{agent_tag}> {data.get('response', '(no response)')}\n")


if __name__ == "__main__":
    sys.exit(main() or 0)
