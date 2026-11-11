"""Формирует вопрос человеку по результату планирования или реализации."""

import json
import os


def main():
    phase = os.environ["INPUTS_PHASE"]
    change = os.environ["INPUTS_CHANGE_NAME"]
    pr_url = os.environ["INPUTS_PR_URL"]
    if phase == "proposal":
        proposal = json.loads(os.environ["INPUTS_REVISED"] or os.environ["INPUTS_PROPOSAL"])
        if proposal["change_name"] != change:
            raise ValueError("Доработка должна сохранять имя существующего change")
        attention = (
            f"Принимаешь план изменения {change}?\nDraft PR: {pr_url}\n"
            f"Риск: {proposal['risk']}\nОткрытые вопросы: {proposal['open_questions']}\n"
            "Approve — перейти к Apply. Reject — доработать этот же change и спросить снова.\n"
            "При отказе опиши замечания или укажи, что оставил комментарии в PR."
        )
        print(json.dumps({"attention": attention}, ensure_ascii=False))
        return
    elif phase == "implementation":
        verdict = ""
        result = json.loads(os.environ["INPUTS_RESULT"])
        if result["status"] == "completed":
            verification = json.loads(os.environ["INPUTS_VERIFICATION"])
            verdict = verification["verdict"]
            attention = (
                f"Нужны ли доработки изменения {change}?\nDraft PR: {pr_url}\n"
                f"Verify: {verdict}. {verification['summary']}\n"
                f"Отчёт опубликован: openspec/changes/{change}/review.md\n"
                "Замечания и разрешённые исключения оставляй в PR, в том числе на строках review.md.\n"
                "Текст ответа будет передан следующей стадии. Архивация запрашивается отдельно."
            )
            options = [{"id": "accept", "label": "Доработок не требуется"},
                       {"id": "rework", "label": "Доработки нужны"}]
        elif result["status"] == "needs_input":
            attention = (
                f"Apply ожидает ответа: {result['summary']}\nDraft PR: {pr_url}\n"
                "Verify в этом проходе не запускался. Ответь текстом здесь или в PR "
                "и выбери продолжение Apply."
            )
            options = [{"id": "continue", "label": "Передать ответ и продолжить Apply"}]
        else:
            raise ValueError("Неизвестный результат Apply")
    else:
        raise ValueError("Неизвестная стадия согласования")
    print(json.dumps({"attention": attention, "options": options, "verdict": verdict}, ensure_ascii=False))


if __name__ == "__main__":
    main()
