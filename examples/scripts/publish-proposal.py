# /// script
# dependencies = ["pyyaml>=6,<7"]
# ///
"""Публикует артефакты proposal и возвращает ссылку на draft PR для ревью."""

import json
import os
from pathlib import Path
import re
import sys
import tempfile

import yaml

from workflow_io import replace_section, run


def main():
    change_name = os.environ["INPUTS_CHANGE_NAME"]
    feature_id = os.environ["INPUTS_FEATURE_ID"]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", change_name):
        raise ValueError("Некорректное имя change")
    if not re.fullmatch(r"\d+", feature_id):
        raise ValueError("Карточка должна содержать FEATURE-ID")

    change = Path("openspec/changes") / change_name
    proposal = (change / "proposal.md").read_text()
    for name in ("design.md", "tasks.md"):
        if not (change / name).is_file():
            raise ValueError(f"Отсутствует артефакт {name}")
    if not list((change / "specs").glob("*/spec.md")):
        raise ValueError("Отсутствуют delta specs")

    config = yaml.safe_load(Path(".archon/config.yaml").read_text())
    base = config["worktree"]["baseBranch"]
    # Получает имя текущей ветки worktree.
    branch = run("git", "symbolic-ref", "--quiet", "--short", "HEAD").strip()
    if branch == base:
        raise ValueError("Публикация требует отдельной ветки worktree")
    # Получает список файлов, уже добавленных в индекс Git.
    staged = run("git", "diff", "--cached", "--name-only").splitlines()
    if any(not path.startswith(f"{change}/") for path in staged):
        raise ValueError("В индексе есть изменения вне текущего change")

    title = re.sub(r"^\s*\[[A-Z]+-\d+\]\s*", "", os.environ["INPUTS_TITLE"]).strip()
    title = f"[{feature_id}] {title}"
    # Ищет открытые PR текущей ветки и получает их URL, базовую ветку и признак draft.
    prs = json.loads(run("gh", "pr", "list", "--head", branch, "--state", "open",
                         "--json", "url,baseRefName,isDraft,body"))
    if prs and (len(prs) != 1 or prs[0]["baseRefName"] != base or not prs[0]["isDraft"]):
        raise ValueError("Существующий PR должен быть draft и иметь ожидаемую базовую ветку")

    # Добавляет в индекс изменения только из каталога текущего change.
    run("git", "add", "--", str(change))
    # Проверяет наличие изменений в индексе перед созданием коммита.
    if run("git", "diff", "--cached", "--name-only"):
        # Создаёт локальный коммит с артефактами proposal.
        output = run("git", "commit", "-m", f"[{feature_id}] Propose. Артефакты {change_name}")
        print(output, file=sys.stderr)
    # Публикует текущую ветку в origin и настраивает отслеживание удалённой ветки.
    run("git", "push", "--set-upstream", "origin", branch)

    initial = f"Артефакты OpenSpec для ревью перед реализацией.\n\nChange: `{change}`"
    body = replace_section(prs[0]["body"] if prs else initial, "proposal", proposal)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", encoding="utf-8") as body_file:
        body_file.write(body)
        body_file.flush()
        if prs:
            url = prs[0]["url"]
            # Обновляет актуальный proposal, сохраняя пользовательский текст описания.
            run("gh", "pr", "edit", url, "--body-file", body_file.name)
        else:
            # Создаёт draft PR с заданной базовой веткой и описанием из файла, возвращает его URL.
            url = run("gh", "pr", "create", "--draft", "--base", base, "--head", branch,
                      "--title", title, "--body-file", body_file.name).strip()
    print(json.dumps({"pr_url": url,
                      "github_cli": str(Path(__file__).with_name("workflow_io.py").resolve())},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
