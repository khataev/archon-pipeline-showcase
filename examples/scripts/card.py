"""Записывает итог автоматического запуска и переносит карточку в «Тест»."""

import json
import os
import urllib.request

BASE = os.environ["PLANKA_BASE_URL"].rstrip("/")
KEY = os.environ["PLANKA_API_KEY"]
CARD_ID = os.environ["INPUTS_CARD_ID"]
CHANGE_NAME = os.environ["INPUTS_CHANGE_NAME"]
VERDICT = os.environ["INPUTS_VERDICT"]
ARCHIVE_PATH = os.environ["INPUTS_ARCHIVE_PATH"]
PR_URL = os.environ["INPUTS_PR_URL"]

TEST_LIST = os.environ["PLANKA_TEST_LIST_ID"]
GROUP = os.environ["PLANKA_FIELD_GROUP_ID"]
F_STAGE = os.environ["PLANKA_STAGE_FIELD_ID"]
F_CHANGE = os.environ["PLANKA_CHANGE_FIELD_ID"]
F_VERDICT = os.environ["PLANKA_VERDICT_FIELD_ID"]


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


set_field(F_STAGE, "done")
set_field(F_CHANGE, CHANGE_NAME)
set_field(F_VERDICT, VERDICT)

verdict_ru = "готово" if VERDICT == "ready" else "нужны правки"
api(
    "POST",
    f"/api/cards/{CARD_ID}/comments",
    {"text": f"showcase-dev завершён: change `{CHANGE_NAME}` архивирован в `{ARCHIVE_PATH}`, вердикт {VERDICT} ({verdict_ru}). PR обновлён: {PR_URL}"},
)

cards = api("GET", f"/api/lists/{TEST_LIST}/cards").get("items", [])
positions = [c.get("position", 0) for c in cards]
# Ставим карточку в конец списка.
position = max(positions) + 8192 if positions else 32768
api("PATCH", f"/api/cards/{CARD_ID}", {"listId": TEST_LIST, "position": position})

print(json.dumps({"updated": True, "moved_to_test": True}))
