"""Передаёт событие завершения Explore после записи итогов пользователем и агентом."""

import argparse
import json
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()
    if not args.result.read_text(encoding="utf-8").strip():
        raise ValueError("Итоги Explore пусты; событие не отправлено")

    # Explore может закончиться раньше, чем запуск успеет перейти к ожиданию.
    for attempt in range(30):
        # Читает состояние именно того запуска, который создал сессию Explore.
        response = subprocess.run(
            ["archon", "workflow", "get", args.run_id, "--json"],
            check=True, capture_output=True, text=True, timeout=30,
        )
        run = json.loads(response.stdout)
        wait = run.get("metadata", {}).get("wait", {})
        if run["status"] == "paused" and wait.get("nodeId") == "explore-gate" and wait.get("kind") == "event":
            # Сигналит конкретное ожидание и продолжает workflow до следующей паузы.
            subprocess.run(
                ["archon", "workflow", "signal", args.run_id,
                 "--event", "explore.completed", "--occurrence", wait["pauseId"], "--json"],
                check=True,
            )
            return
        if run["status"] != "running":
            raise RuntimeError("Запуск не ожидает завершения Explore; событие не отправлено")
        time.sleep(2)
    raise TimeoutError("Ожидание Explore ещё не открыто. Повторите команду после проверки запуска")


if __name__ == "__main__":
    main()
