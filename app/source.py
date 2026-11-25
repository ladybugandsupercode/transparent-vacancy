import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class SourceError(RuntimeError):
    pass


def http_get_json(url, params=None, timeout=30):
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "TransparentVacancy/1.0 (educational hackathon MVP)",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise SourceError(f"API вернул HTTP {response.status}")
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        raise SourceError(f"HTTP ошибка API: {exc.code}") from exc
    except URLError as exc:
        raise SourceError(f"Не удалось подключиться к API: {exc.reason}") from exc
    except TimeoutError as exc:
        raise SourceError("Истекло время ожидания ответа API") from exc

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SourceError("API вернул ответ, который не является корректным JSON") from exc

    status = str(data.get("status", "200"))
    if status != "200":
        detail = (data.get("meta") or {}).get("error", "неизвестная ошибка")
        raise SourceError(f"API сообщил status={status}: {detail}")
    return data


def extract_vacancies(payload):
    """Поддерживает официальный формат results.vacancies и тестовые массивы."""
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        results = payload.get("results", payload)
        if isinstance(results, dict):
            items = results.get("vacancies", results.get("items", []))
        elif isinstance(results, list):
            items = results
        else:
            items = []
    else:
        items = []

    vacancies = []
    for item in items or []:
        if isinstance(item, dict) and isinstance(item.get("vacancy"), dict):
            vacancies.append(item["vacancy"])
        elif isinstance(item, dict):
            vacancies.append(item)
    return vacancies


def fetch_region(settings, pages=None, limit=None):
    pages = pages or settings.max_pages
    limit = limit or settings.page_size
    if not 1 <= limit <= 100:
        raise ValueError("Параметр limit должен быть от 1 до 100")
    if pages < 1:
        raise ValueError("Число страниц должно быть не меньше 1")

    all_vacancies = {}
    for page in range(pages):
        offset = page * limit
        logging.info("Загрузка страницы %s (offset=%s, limit=%s)", page + 1, offset, limit)
        payload = http_get_json(
            settings.api_url,
            params={"offset": offset, "limit": limit},
            timeout=settings.timeout_seconds,
        )
        page_vacancies = extract_vacancies(payload)
        if not page_vacancies:
            break

        for vacancy in page_vacancies:
            vacancy_id = str(vacancy.get("id") or vacancy.get("vacancy_id") or "").strip()
            if not vacancy_id:
                # Не объединяем разные записи с пустым ID: сохраняем стабильный fallback.
                import hashlib
                raw = json.dumps(vacancy, ensure_ascii=False, sort_keys=True)
                vacancy_id = "no-id-" + hashlib.sha256(raw.encode()).hexdigest()[:12]
            all_vacancies[vacancy_id] = vacancy

        total = (payload.get("meta") or {}).get("total")
        try:
            if total is not None and offset + limit >= int(total):
                break
        except (TypeError, ValueError):
            pass
        if len(page_vacancies) < limit:
            break
        if page + 1 < pages:
            time.sleep(settings.request_pause_seconds)

    if not all_vacancies:
        raise SourceError("API не вернул вакансий: отчёт не перезаписан")
    return list(all_vacancies.values())
