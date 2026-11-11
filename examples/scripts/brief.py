"""brief: читает карточку Planka, пишет stage=running + run_id, отдаёт JSON-бриф."""

import json
import os
import re
import urllib.request

BASE = os.environ["PLANKA_BASE_URL"].rstrip("/")
KEY = os.environ["PLANKA_API_KEY"]
CARD_ID = os.environ["INPUTS_CARD_ID"]
RUN_ID = os.environ.get("WORKFLOW_ID", "")

GROUP = os.environ["PLANKA_FIELD_GROUP_ID"]
F_STAGE = os.environ["PLANKA_STAGE_FIELD_ID"]
F_RUN = os.environ["PLANKA_RUN_FIELD_ID"]
SKIP_EXPLORE_LABEL = os.environ["PLANKA_SKIP_EXPLORE_LABEL_ID"]


def api(method, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=body,
        method=method,
        headers={"X-Api-Key": KEY, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def set_field(field_id, value):
    api(
        "PATCH",
        f"/api/cards/{CARD_ID}/custom-field-values/customFieldGroupId:{GROUP}:customFieldId:{field_id}",
        {"content": value},
    )


data = api("GET", f"/api/cards/{CARD_ID}")
item = data.get("item") or data
name = item.get("name") or ""
match = re.search(r"\[([A-Z]+-\d+)\]", name)
ticket = match.group(1) if match else ""
feature_id = re.sub(r"\D", "", ticket) if ticket else ""

included = data.get("included") or {}
label_ids = {cl.get("labelId") for cl in (included.get("cardLabels") or [])}
skip_explore = SKIP_EXPLORE_LABEL in label_ids

set_field(F_STAGE, "running")
set_field(F_RUN, RUN_ID)

print(
    json.dumps(
        {
            "card_id": item.get("id"),
            "ticket": ticket,
            "feature_id": feature_id,
            "title": name,
            "description": item.get("description") or "",
            "skip_explore": skip_explore,
        },
        ensure_ascii=False,
    )
)
