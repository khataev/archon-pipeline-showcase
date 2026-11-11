#!/usr/bin/env python3
"""Учебный stateless poller; переменные и binding задаются владельцем стенда."""
import base64
import json
import os
import subprocess
import tempfile
from urllib.parse import quote
from urllib.request import Request, urlopen


def main():
    base = os.environ["PLANKA_BASE_URL"].rstrip("/")
    list_id = quote(os.environ["PLANKA_LIST_ID"], safe="")
    user_id = quote(os.environ["PLANKA_BOT_USER_ID"], safe="")
    binding = os.environ["ARCHON_TRIGGER_CONFIG"]
    host = os.environ["ARCHON_HOST"]
    req = Request(f"{base}/api/lists/{list_id}/cards?userIds={user_id}",
                  headers={"X-Api-Key": os.environ["PLANKA_API_KEY"]})
    with urlopen(req, timeout=30) as response:
        cards = json.load(response).get("items", [])
    for card in cards:
        version = card.get("listChangedAt") or card.get("updatedAt") or "0"
        key = json.dumps([card["id"], version], separators=(",", ":")).encode()
        delivery_id = base64.b64encode(key).decode()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as inputs:
            json.dump({"card_id": card["id"]}, inputs)
            inputs.flush()
            subprocess.run(["archon", "trigger", "fire", "--config", binding,
                            "--delivery-id", delivery_id, "--inputs", inputs.name],
                           check=True, timeout=180)
    subprocess.run(["archon", "trigger", "drain", "--host", host], check=True, timeout=180)


if __name__ == "__main__":
    main()
