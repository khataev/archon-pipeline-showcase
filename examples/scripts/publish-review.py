"""Публикует реализацию и отчёт Verify перед ответом человека."""

import json
import os
from pathlib import Path
import re
import sys
import tempfile

from workflow_io import open_pr, replace_section, run


def main():
    change = os.environ["INPUTS_CHANGE_NAME"]
    feature_id = os.environ["INPUTS_FEATURE_ID"]
    result = json.loads(os.environ["INPUTS_RESULT"])
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", change) or not feature_id.isdigit():
        raise ValueError("Некорректное имя change или FEATURE-ID")
    pr = open_pr(os.environ["INPUTS_PR_URL"])
    review = Path("openspec/changes") / change / "review.md"
    if result["status"] == "completed":
        verification = json.loads(os.environ["INPUTS_VERIFICATION"])
        if not review.is_file() or not review.read_text().strip():
            raise ValueError("Verify не сохранил review.md")
        # Проверяет, что агент закоммитил код, и публикация не захватит чужие файлы.
        tracked = run("git", "diff", "--name-only", "--no-renames", "-z", "HEAD")
        # Учитывает новый review.md и незакоммиченные новые файлы реализации.
        untracked = run("git", "ls-files", "--others", "--exclude-standard", "-z")
        # Не допускает попадания чужого staged-изменения даже при восстановленном рабочем файле.
        staged = run("git", "diff", "--cached", "--name-only", "--no-renames", "-z")
        paths = set(filter(None, tracked.split("\0") + untracked.split("\0") + staged.split("\0")))
        if paths - {str(review)}:
            raise ValueError("Apply оставил незакоммиченные изменения вне review.md")
        # Добавляет только отчёт независимой проверки.
        run("git", "add", "--", str(review))
        # Не создаёт повторный коммит, если отчёт уже опубликован.
        if run("git", "diff", "--cached", "--name-only").strip():
            # Фиксирует актуальный отчёт отдельно от исправлений Apply.
            output = run("git", "commit", "-m", f"[{feature_id}] Verify. Отчёт {change}")
            print(output, file=sys.stderr)
        content = (
            f"Реализация и отчёт готовы к ревью.\n\nОтчёт Verify: `{review}`\n"
            f"Вердикт Verify: `{verification['verdict']}`\n{verification['summary']}"
        )
    elif result["status"] == "needs_input":
        # Незавершённые локальные правки сохраняются для следующего Apply.
        content = f"Apply ожидает ответа человека. Verify в этом проходе не запускался.\n\n{result['summary']}"
    else:
        raise ValueError("Неизвестный результат Apply")

    # Публикует готовые коммиты в существующую ветку PR без force-push.
    run("git", "push", "origin", pr["headRefName"])
    body = pr["body"]
    proposal = review.with_name("proposal.md")
    if result["status"] == "completed" and proposal.is_file():
        body = replace_section(body, "proposal", proposal.read_text())
    body = replace_section(body, "result", content)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", encoding="utf-8") as body_file:
        body_file.write(body)
        body_file.flush()
        # Обновляет служебный раздел, не меняя draft и пользовательский текст.
        run("gh", "pr", "edit", pr["url"], "--body-file", body_file.name)
    # Возвращает SHA опубликованных коммитов для истории прохода.
    head_sha = run("git", "rev-parse", "HEAD").strip()
    print(json.dumps({"pr_url": pr["url"], "head_sha": head_sha}))


if __name__ == "__main__":
    main()
