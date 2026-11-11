"""Коммитит результаты Archive, публикует ветку и обновляет существующий PR."""

import json
import os
from pathlib import Path
import re
import sys
import tempfile

from workflow_io import open_pr, replace_section, run


def main():
    change_name = os.environ["INPUTS_CHANGE_NAME"]
    feature_id = os.environ["INPUTS_FEATURE_ID"]
    archive_path = os.environ["INPUTS_ARCHIVE_PATH"]
    pr_url = os.environ["INPUTS_PR_URL"]
    verdict = os.environ["INPUTS_VERDICT"]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", change_name):
        raise ValueError("Некорректное имя change")
    if not re.fullmatch(r"\d+", feature_id):
        raise ValueError("Не передан корректный FEATURE-ID")
    if not re.fullmatch(r"openspec/changes/archive/\d{4}-\d{2}-\d{2}-" + re.escape(change_name), archive_path):
        raise ValueError("Архивный путь не соответствует текущему change")
    archive = Path(archive_path)
    archive.resolve().relative_to(Path("openspec/changes/archive").resolve())
    for name in ("proposal.md", "review.md"):
        if not (archive / name).is_file():
            raise ValueError(f"В архиве отсутствует {name}")
    active = Path("openspec/changes") / change_name
    if active.exists():
        raise ValueError("Change ещё находится в активном каталоге")

    pr = open_pr(pr_url)
    branch = pr["headRefName"]

    # Получает изменённые отслеживаемые файлы, включая обе стороны перемещения в архив.
    tracked = run("git", "diff", "--name-only", "--no-renames", "-z", "HEAD")
    # Получает новые файлы, включая архивированный review.md.
    untracked = run("git", "ls-files", "--others", "--exclude-standard", "-z")
    # Учитывает staged-изменения, даже если рабочий файл уже восстановлен.
    staged = run("git", "diff", "--cached", "--name-only", "--no-renames", "-z")
    paths = sorted(set(filter(None, tracked.split("\0") + untracked.split("\0") + staged.split("\0"))))
    allowed = (f"{active}/", f"{archive}/", "openspec/specs/")
    if any(not path.startswith(allowed) for path in paths):
        raise ValueError("Остались незакоммиченные изменения вне результатов Archive")
    if paths:
        # Исключает удалённые пути, которые уже отсутствуют и в рабочей копии, и в индексе.
        staged_deletions = set(filter(None, run(
            "git", "diff", "--cached", "--name-only", "--no-renames", "--diff-filter=D", "-z",
        ).split("\0")))
        to_stage = [path for path in paths if path not in staged_deletions or os.path.lexists(path)]
        # Добавляет только результаты архивации и синхронизации спецификаций.
        if to_stage:
            run("git", "add", "-A", "--", *to_stage)
        # Коммитит архив и отчёт Verify перед публикацией ветки.
        output = run("git", "commit", "-m", f"[{feature_id}] Archive. {change_name}")
        print(output, file=sys.stderr)

    # Публикует коммиты Apply и Archive в ветку существующего PR без force-push.
    run("git", "push", "origin", branch)

    body = pr["body"].replace(f"Change: `{active}`", f"Change: `{archive}`")
    body = replace_section(body, "result",
        f"Реализация опубликована, OpenSpec-изменение архивировано.\n\n"
        f"Архив: `{archive}`\nОтчёт Verify: `{archive}/review.md`\nВердикт Verify: `{verdict}`")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", encoding="utf-8") as body_file:
        body_file.write(body)
        body_file.flush()
        # Обновляет описание того же PR, сохраняя пользовательский текст вне служебного блока.
        run("gh", "pr", "edit", pr_url, "--body-file", body_file.name)
    # Возвращает опубликованный SHA для истории запуска.
    head_sha = run("git", "rev-parse", "HEAD").strip()
    print(json.dumps({"pr_url": pr["url"], "head_sha": head_sha}))


if __name__ == "__main__":
    main()
