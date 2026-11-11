---
description: Создать OpenSpec-изменение (proposal + specs + design + tasks) из брифа карточки
---

# Propose: изменение из карточки

Ты — агент конвейера `showcase-dev` в неинтерактивной стадии Propose.
Создай OpenSpec-изменение по брифу карточки.

- Тикет: `$brief.output.ticket`
- FEATURE-ID: `$brief.output.feature_id`
- Заголовок: $brief.output.title
- Описание:
  $brief.output.description
- Итоги Explore (уже принятые решения/выводы; пусто — если Explore пропущен):
  $INPUTS.explore_notes

## Порядок действий

1. Выведи kebab-case имя изменения из заголовка карточки — без `[PROJECT-123]`-префикса
   и без номера тикета. Пример: «Улучшить авторизацию API» → `improve-api-authorization`.

2. Действуй по процедуре из `.agents/skills/openspec-propose/SKILL.md` (прочитай этот файл в
   worktree и следуй ему), передав в качестве запроса заголовок и описание карточки.
   Всё, что зафиксировано в «Итогах Explore» выше, считай уже согласованными
   решениями — не переспрашивай и не оспаривай их, используй как основу для
   proposal/design/specs/tasks. Создай все артефакты схемы: `proposal.md`,
   delta-спек(и), `design.md`, `tasks.md`.

3. Соблюдай конвенции проекта (AGENTS.md):
   - первой строкой `proposal.md` запиши `Тикет: $brief.output.ticket`;
   - `tasks.md` — конкретные подзадачи с галочками `- [ ]` (не «разобраться»,
     а измеримые шаги).

4. **Не задавай вопросы интерактивно.** Неоднозначности, влияющие на scope/поведение,
   фиксируй как разумные допущения в `proposal.md` и перечисли в `open_questions`
   ответа. Решение по ним примет человек на гейте.

5. Верни JSON-объект ровно такого вида (без лишнего текста):

   ```json
   {"change_name": "<kebab-case>", "open_questions": [], "risk": "low"}
   ```

   - `change_name` — имя реально созданного change;
   - `open_questions` — список вопросов (пустой массив, если их нет);
   - `risk` — одно из: `low`, `medium`, `high`.
