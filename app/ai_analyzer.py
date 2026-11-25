import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from app.normalizer import normalize_vacancy


SYSTEM_PROMPT = """Ты — аналитик качества текстов вакансий для сервиса прозрачности условий труда.
Анализируй только предоставленные поля. Не делай юридических выводов, не выдумывай факты.
Отмечай только конкретные пропуски, неоднозначности и противоречия, которые мешают соискателю понять условия.
Если поле пустое — это пропуск. Если поле заполнено конкретно, не называй его отсутствующим.
Отсутствие необязательной информации само по себе не является нарушением.
Верни СТРОГО JSON-массив объектов. Каждый объект:
{"topic":"...","source_field":"...","quote":"дословная цитата из данных или пустая строка","issue":"суть проблемы","recommendation":"что уточнить работодателю","kind":"missing|ambiguity|contradiction"}
Если замечаний нет, верни [].
Не создавай цитаты: quote должна быть точной подстрокой значения source_field. Не добавляй markdown."""


class AIAnalysisError(RuntimeError):
    pass


def analyze_with_ollama(vacancy, settings):
    normalized = normalize_vacancy(vacancy)
    fields = {
        key: normalized.get(key, "")
        for key in (
            "position", "duties", "requirements", "salary_min", "salary_max",
            "salary", "schedule", "employment", "workplace", "region"
        )
    }
    body = {
        "model": settings.ollama_model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(fields, ensure_ascii=False)},
        ],
        "options": {"temperature": 0},
    }
    request = Request(
        settings.ollama_url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise AIAnalysisError(
            f"Не удалось получить ответ локальной модели Ollama ({settings.ollama_model}): {exc}"
        ) from exc

    content = result.get("message", {}).get("content", "")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIAnalysisError("Модель вернула невалидный JSON") from exc

    if isinstance(parsed, dict):
        parsed = parsed.get("remarks", parsed.get("issues", []))
    if not isinstance(parsed, list):
        raise AIAnalysisError("Ожидался JSON-массив замечаний от модели")

    # Защита от неподтверждённых цитат и неверных типов.
    checked = []
    allowed_fields = set(fields)
    for item in parsed:
        if not isinstance(item, dict):
            continue
        source_field = str(item.get("source_field", "")).strip()
        quote = str(item.get("quote", "")).strip()
        if source_field not in allowed_fields:
            continue
        source_value = str(fields[source_field] or "")
        if quote and quote not in source_value:
            quote = ""
        kind = str(item.get("kind", "ambiguity")).lower()
        if kind not in {"missing", "ambiguity", "contradiction"}:
            kind = "ambiguity"
        issue = str(item.get("issue", "")).strip()
        recommendation = str(item.get("recommendation", "")).strip()
        if not issue or not recommendation:
            continue
        checked.append({
            "topic": str(item.get("topic", source_field)).strip() or source_field,
            "source_field": source_field,
            "quote": quote,
            "issue": issue,
            "recommendation": recommendation,
            "kind": kind,
        })
    return checked


def analyze(vacancy, settings):
    if not settings.ai_enabled:
        raise AIAnalysisError("ИИ отключён: базовый сценарий требует AI_ENABLED=true")
    return analyze_with_ollama(vacancy, settings)
