import re
from html import unescape


def clean(value):
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(filter(None, (clean(x) for x in value)))
    if isinstance(value, dict):
        # Не превращаем сложные объекты в бессмысленный Python repr.
        preferred = ("name", "title", "value", "text", "description")
        parts = [clean(value[k]) for k in preferred if k in value]
        return "; ".join(x for x in parts if x) or ""
    text = unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


FIELD_ALIASES = {
    "position": ("job-name", "job_name", "position", "profession"),
    "duties": ("duty", "duties", "responsibilities"),
    "requirements": ("requirement", "requirements", "qualification"),
    "salary_min": ("salary_min", "salary-min", "min_salary"),
    "salary_max": ("salary_max", "salary-max", "max_salary"),
    "salary": ("salary", "salary_text"),
    "schedule": ("schedule", "work_schedule"),
    "employment": ("employment", "employment_type", "type_of_employment"),
    "workplace": ("work-places", "work_places", "workplace", "address"),
    "region": ("region",),
}


def first_value(vacancy, aliases):
    for key in aliases:
        if key in vacancy:
            value = clean(vacancy[key])
            if value:
                return value
    return ""


def normalize_vacancy(vacancy):
    result = {name: first_value(vacancy, aliases) for name, aliases in FIELD_ALIASES.items()}
    result["id"] = clean(vacancy.get("id") or vacancy.get("vacancy_id"))
    result["url"] = clean(vacancy.get("vac_url") or vacancy.get("url"))
    result["employer"] = clean(vacancy.get("company") or vacancy.get("employer"))
    # Nested API objects can carry useful names.
    if isinstance(vacancy.get("region"), dict):
        result["region"] = clean(vacancy["region"].get("name"))
    if isinstance(vacancy.get("company"), dict):
        result["employer"] = clean(vacancy["company"].get("name"))
    result["raw"] = vacancy
    return result
