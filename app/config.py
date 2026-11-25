import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    api_url: str = "https://opendata.trudvsem.ru/api/v1/vacancies/region/39"
    region_code: str = "39"
    page_size: int = 100
    max_pages: int = 2
    timeout_seconds: int = 30
    request_pause_seconds: float = 0.4
    report_path: Path = Path("reports/report.json")
    backup_path: Path = Path("reports/last_successful_report.json")
    ollama_url: str = "http://localhost:11434/api/chat"
    ollama_model: str = "qwen2.5:3b"
    ai_enabled: bool = True

    @classmethod
    def from_env(cls):
        return cls(
            api_url=os.getenv(
                "TRUDVSEM_API_URL",
                "https://opendata.trudvsem.ru/api/v1/vacancies/region/39",
            ),
            region_code=os.getenv("REGION_CODE", "39"),
            page_size=int(os.getenv("PAGE_SIZE", "100")),
            max_pages=int(os.getenv("MAX_PAGES", "2")),
            timeout_seconds=int(os.getenv("HTTP_TIMEOUT", "30")),
            request_pause_seconds=float(os.getenv("REQUEST_PAUSE", "0.4")),
            report_path=Path(os.getenv("REPORT_PATH", "reports/report.json")),
            backup_path=Path(os.getenv("BACKUP_PATH", "reports/last_successful_report.json")),
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
            ai_enabled=os.getenv("AI_ENABLED", "true").lower() in {"1", "true", "yes"},
        )
