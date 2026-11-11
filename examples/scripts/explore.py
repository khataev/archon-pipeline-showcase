"""explore: запускает интерактивную сессию Codex в herdr (в worktree) и пишет на карточку, куда подключаться."""

import json
import os
import re
import shlex
from pathlib import Path
import subprocess
import time
import urllib.request

CARD_ID = os.environ["INPUTS_CARD_ID"]
TICKET = os.environ["INPUTS_TICKET"]
FEATURE_ID = os.environ["INPUTS_FEATURE_ID"]
TITLE = os.environ["INPUTS_TITLE"]
DESCRIPTION = os.environ["INPUTS_DESCRIPTION"]
CWD = os.getcwd()
RUN_ID = os.environ["WORKFLOW_ID"]
RESULT_PATH = Path(CWD) / "tmp" / "archon" / RUN_ID / "explore" / "result.md"
RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
FINISH_COMMAND = shlex.join([
    "python3", str(Path(__file__).resolve().with_name("finish-explore.py")),
    "--run-id", RUN_ID, "--result", str(RESULT_PATH),
])

BASE = os.environ["PLANKA_BASE_URL"].rstrip("/")
KEY = os.environ["PLANKA_API_KEY"]


def _ssh_machine():
    return os.environ.get("SSH_MACHINE_NAME", "<ssh-target>")

# Имя агента herdr: [a-z][a-z0-9_-]{0,31}
slug = re.sub(r"[^a-z0-9_-]+", "-", TICKET.lower()).strip("-")
NAME = (f"explore-{slug}" if slug else "explore")[:31]


def sh(args):
    return subprocess.run(list(args), capture_output=True, text=True, timeout=180)


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


# 1. Создать herdr-workspace в worktree
r = sh(["herdr", "workspace", "create", "--cwd", CWD, "--label", NAME, "--no-focus"])
if r.returncode != 0:
    raise RuntimeError(f"herdr workspace create: {r.stderr}")
pane_id = json.loads(r.stdout)["result"]["root_pane"]["pane_id"]

# 2. Запустить Codex в этой панели
r = sh(["herdr", "agent", "start", NAME, "--kind", "codex", "--pane", pane_id, "--", "--approve-for-me", "--model", os.environ["EXPLORE_MODEL"], "-c", 'model_reasoning_effort="low"'])
if r.returncode != 0:
    raise RuntimeError(f"herdr agent start: {r.stderr}")

# 3. Собрать промпт из commands/explore.md и отправить (не ждём завершения — сессия интерактивная)
explore_md = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "commands", "explore.md")
with open(explore_md, encoding="utf-8") as f:
    prompt = f.read()
prompt = (
    prompt.replace("$brief.output.ticket", TICKET)
    .replace("$brief.output.feature_id", FEATURE_ID)
    .replace("$brief.output.title", TITLE)
    .replace("$brief.output.description", DESCRIPTION)
    .replace("$EXPLORE_RESULT_PATH", str(RESULT_PATH))
    .replace("$EXPLORE_FINISH_COMMAND", FINISH_COMMAND)
)
# agent start отдаёт «idle» по хуку раньше, чем TUI агента готов принять вставку,
# поэтому даём ему докатиться до строки ввода и отправляем с верификацией приёма.
time.sleep(3)
for attempt in range(3):
    r = sh(["herdr", "agent", "prompt", NAME, prompt, "--wait", "--until", "working", "--until", "blocked", "--timeout", "15000"])
    if r.returncode == 0:
        break
    time.sleep(2)
else:
    raise RuntimeError(f"herdr agent prompt: {r.stderr}")

# 4. Сообщить на карточку, куда подключаться
machine = _ssh_machine()
connection = (
    f"🔎 Explore запущен в herdr: агент `{NAME}` (pane `{pane_id}`).\n\n"
    f"Подключение к панели агента (с локалки):\n```bash\nssh -t {machine} herdr agent attach {NAME}\n```\n"
)
api("POST", f"/api/cards/{CARD_ID}/comments", {"text": connection})

print(json.dumps({"agent": NAME, "pane": pane_id, "result_path": str(RESULT_PATH)}))
