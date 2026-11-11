"""Общий доступ к Git и GitHub для детерминированных стадий workflow."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys


def github_environment():
    env = os.environ.copy()
    return env


def run(*args, input=None):
    # Сохраняет вывод без удаления разделителей NUL в списках путей Git.
    return subprocess.run(
        args, input=input, check=True, text=True, stdout=subprocess.PIPE,
        env=github_environment() if args[0] == "gh" else None,
    ).stdout


def open_pr(pr_url):
    # Определяет текущую ветку worktree.
    branch = run("git", "symbolic-ref", "--quiet", "--short", "HEAD").strip()
    # Проверяет, что публикация и обсуждение относятся к открытому PR этой ветки.
    pr = json.loads(run(
        "gh", "pr", "view", pr_url, "--json",
        "url,number,state,headRefName,headRefOid,baseRefName,body",
    ))
    if pr["state"] != "OPEN" or pr["headRefName"] != branch or branch == pr["baseRefName"]:
        raise ValueError("Ожидается открытый PR текущей отдельной ветки")
    return pr


def replace_section(body, name, content):
    start, end = f"<!-- showcase-dev:{name} -->", f"<!-- /showcase-dev:{name} -->"
    section = f"{start}\n{content.rstrip()}\n{end}"
    if start not in body and end not in body:
        return body.rstrip() + "\n\n" + section + "\n"
    if body.count(start) != 1 or body.count(end) != 1 or body.index(end) < body.index(start):
        raise ValueError(f"Повреждены границы служебного раздела PR: {name}")
    return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: section, body, flags=re.DOTALL)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "gh":
        raise SystemExit("Использование: python3 workflow_io.py gh <аргументы>")
    # Даёт агентам ту же авторизацию gh, что и скриптам публикации.
    sys.stdout.write(run(*sys.argv[1:]))
