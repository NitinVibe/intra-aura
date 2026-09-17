import json
from pathlib import Path
from threading import Lock

from sqlalchemy.orm import Session

from app.models.site_content import SiteContent

CONTENT_PATH = Path(__file__).resolve().parent / "site_content.json"
_LOCK = Lock()


def _file_content():
    with _LOCK:
        try:
            return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


def load_content(db: Session | None = None):
    """Load CMS content from PostgreSQL when available, otherwise use JSON.

    Passing a DB session is preferred for admin routes. The template helper
    uses a short-lived session so public pages always see the latest CMS data.
    """
    if db is not None:
        row = db.query(SiteContent).filter(SiteContent.id == 1).first()
        if row and isinstance(row.content, dict):
            return row.content
        return _file_content()

    # Used by Jinja's site() helper. Import lazily to avoid import cycles.
    try:
        from app.config.database import SessionLocal
        session = SessionLocal()
        try:
            row = session.query(SiteContent).filter(SiteContent.id == 1).first()
            if row and isinstance(row.content, dict):
                return row.content
        finally:
            session.close()
    except Exception:
        # If the DB is temporarily unavailable, retain the existing local
        # fallback so the application can still render its bundled content.
        pass

    return _file_content()


def save_content(data, db: Session | None = None):
    """Persist CMS content to PostgreSQL and keep JSON as a local fallback."""
    if not isinstance(data, dict):
        raise ValueError("CMS content must be a JSON object")

    if db is not None:
        row = db.query(SiteContent).filter(SiteContent.id == 1).first()
        if row is None:
            row = SiteContent(id=1, content=data)
            db.add(row)
        else:
            # Assign a fresh object so SQLAlchemy's JSON type marks the
            # column dirty even when the caller mutated a nested value.
            row.content = json.loads(json.dumps(data, ensure_ascii=False))
        db.commit()
        return

    # Local fallback for tools/scripts that do not have a DB session.
    with _LOCK:
        CONTENT_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONTENT_PATH.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(CONTENT_PATH)


def ensure_seeded(db: Session):
    """Create the first DB CMS row from the bundled JSON if none exists."""
    row = db.query(SiteContent).filter(SiteContent.id == 1).first()
    if row is None:
        data = _file_content()
        row = SiteContent(id=1, content=data)
        db.add(row)
        db.commit()
    return row
