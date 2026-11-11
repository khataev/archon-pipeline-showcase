"""Передаёт текст финального ответа следующему агенту."""

import json
import os
from pathlib import Path


phase = os.environ["INPUTS_PHASE"]
if phase not in ("proposal", "implementation"):
    raise ValueError("Неизвестная стадия согласования")
path = Path(os.environ["ARTIFACTS_DIR"]) / f"{phase}-feedback.txt"
print(json.dumps({"text": path.read_text()}, ensure_ascii=False))
