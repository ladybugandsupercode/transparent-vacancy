import argparse
import json
import logging
import os
import sys
from pathlib import Path

from app.config import Settings
from app.pipeline import run_live, run_verify


def build_parser():
    parser = argparse.ArgumentParser(
        description="Прозрачная вакансия — анализ вакансий региона 39."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    live = sub.add_parser("run", help="Загрузить вакансии из API и сформировать отчёт")
    live.add_argument("--pages", type=int, default=None, help="Число страниц API (по 100 вакансий)")
    live.add_argument("--limit", type=int, default=None, help="Число вакансий на странице (1–100)")
    live.add_argument("--output", default=None, help="Путь к JSON-отчёту")

    verify = sub.add_parser("verify", help="Проверить локальный JSON без обращения к API")
    verify.add_argument("input", help="Путь к JSON-файлу ответа API или массиву вакансий")
    verify.add_argument("--output", default=None, help="Путь к JSON-отчёту")

    return parser


def main():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    args = build_parser().parse_args()
    settings = Settings.from_env()
    try:
        if args.command == "run":
            output = Path(args.output) if args.output else settings.report_path
            run_live(
                settings,
                output=output,
                pages=args.pages or settings.max_pages,
                limit=args.limit or settings.page_size,
            )
        else:
            output = Path(args.output) if args.output else settings.report_path
            run_verify(settings, Path(args.input), output)
        return 0
    except Exception as exc:
        logging.exception("Выполнение завершилось ошибкой: %s", exc)
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
