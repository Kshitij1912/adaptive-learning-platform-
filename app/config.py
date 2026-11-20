import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'app.db'}")
    artifact_dir: Path = Path(os.getenv("ARTIFACT_DIR", str(ROOT / "artifacts")))
    auto_create_tables: bool = os.getenv("AUTO_CREATE_TABLES", "1") == "1"  # dev convenience; use Alembic in prod
    auto_seed_course: bool = os.getenv("AUTO_SEED_COURSE", "1") == "1"


settings = Settings()
