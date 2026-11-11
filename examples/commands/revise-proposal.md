---
description: Доработать существующие OpenSpec-артефакты по замечаниям человека и PR
---

# Доработка Propose: `$propose.output.change_name`

Ты — агент конвейера `showcase-dev` в неинтерактивной стадии доработки плана.

- Change: `$propose.output.change_name`
- Тикет: `$brief.output.ticket`
- FEATURE-ID: `$brief.output.feature_id`
- PR: $publish-proposal.output.pr_url
- Замечания человека: $INPUTS.feedback

1. Сам прочитай актуальные обсуждения этого PR через gh: общие комментарии,
   reviews с `changes requested` и inline-треды со всеми ответами, включая
   устаревшие строки. Учитывай пагинацию. GitHub-команды выполняй через
   `python3 "$publish-proposal.output.github_cli" gh ...`.

2. Доработай существующий change по тексту человека и актуальным замечаниям.
   Не создавай и не переименовывай change. Используй процедуру
   `.agents/skills/openspec-update-change/SKILL.md` для согласованного обновления
   proposal/specs/design/tasks. Входные замечания — явное разрешение внести
   указанные правки в неинтерактивном режиме; результат человек проверит
   на следующей паузе. Новые неоднозначности верни в `open_questions`.
   Сохраняй уже выполненные отметки задач, если задача остаётся выполненной,
   и первую строку proposal: `Тикет: $brief.output.ticket`.

3. Исправления отдельных комментариев PR коммить по одному:
   `[$brief.output.feature_id] Propose. Review <описание на русском>`.
   Ответь в соответствующие треды, указывая коммиты или причину возражения.
   Тексты передавай через `--body-file` или JSON-файл `--input`.
   Push и обновление описания PR выполняет следующий узел workflow.

Не ожидай интерактивных ответов внутри стадии. Верни JSON:

```json
{"change_name": "$propose.output.change_name", "open_questions": [], "risk": "low"}
```

`risk` — `low`, `medium` или `high`; `open_questions` — актуальные вопросы человеку.
