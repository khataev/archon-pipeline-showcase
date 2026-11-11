"""Сохраняет полный текст итогов Explore в output узла для истории и Propose."""

import json
import os
from pathlib import Path


def main():
    if os.environ["INPUTS_WAIT_STATUS"] != "satisfied":
        raise RuntimeError("Истёк срок ожидания Explore; Propose не запущен")
    notes = Path(os.environ["INPUTS_RESULT_PATH"]).read_text(encoding="utf-8")
    if not notes.strip():
        raise ValueError("Итоги Explore пусты; Propose не запущен")
    print(json.dumps({"notes": notes}, ensure_ascii=False))


if __name__ == "__main__":
    main()
