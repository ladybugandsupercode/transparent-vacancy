import json
import logging
from pathlib import Path

from app.ai_analyzer import analyze, AIAnalysisError
from app.report import build_entry, build_report, save_success
from app.source import fetch_region, extract_vacancies


def _analyze_all(vacancies, settings):
    entries = []
    for index, vacancy in enumerate(vacancies, start=1):
        vacancy_id = vacancy.get("id", "без ID")
        logging.info("ИИ-анализ вакансии %s/%s (ID=%s)", index, len(vacancies), vacancy_id)
        remarks = analyze(vacancy, settings)
        entries.append(build_entry(vacancy, remarks))
    return entries


def run_live(settings, output, pages, limit):
    # До завершения всех стадий файлы отчёта не изменяются.
    vacancies = fetch_region(settings, pages=pages, limit=limit)
    entries = _analyze_all(vacancies, settings)
    report = build_report(
        entries,
        mode="live",
        source=settings.api_url,
        region_code=settings.region_code,
    )
    save_success(report, output, settings.backup_path)
    logging.info("Готово: %s вакансий; отчёт: %s", len(entries), output)
    return report


def run_verify(settings, input_path, output):
    with Path(input_path).open("r", encoding="utf-8") as file:
        payload = json.load(file)
    vacancies = extract_vacancies(payload)
    if not vacancies:
        raise ValueError("В файле не найден список вакансий. Ожидается results.vacancies или массив вакансий.")
    entries = _analyze_all(vacancies, settings)
    report = build_report(
        entries,
        mode="verify",
        source=str(input_path),
        region_code=settings.region_code,
    )
    # Проверочный режим пишет только указанный output и не меняет live backup.
    from app.report import atomic_write_json
    atomic_write_json(output, report)
    logging.info("Проверка завершена: %s вакансий; отчёт: %s", len(entries), output)
    return report
