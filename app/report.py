import json
import os
import tempfile
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from app.normalizer import normalize_vacancy


def build_entry(vacancy, remarks):
    item = normalize_vacancy(vacancy)
    vacancy_id = item["id"]
    if not vacancy_id:
        raw = json.dumps(vacancy, ensure_ascii=False, sort_keys=True)
        vacancy_id = "no-id-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return {
        "id": vacancy_id,
        "url": item["url"],
        "remarks": remarks,
    }


def build_report(entries, mode, source, region_code):
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "source": source,
        "region_code": str(region_code),
        "vacancies_count": len(entries),
        "vacancies": entries,
    }


def atomic_write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def save_success(report, output_path, backup_path):
    # Обе копии создаются только после успешной загрузки и анализа всего набора.
    atomic_write_json(output_path, report)
    if Path(backup_path) != Path(output_path):
        atomic_write_json(backup_path, report)
