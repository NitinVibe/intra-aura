"""Shared Jinja2 template configuration for Intra Aura.

All templates inherit from base.html, which uses the site() helper.  This
wrapper injects that helper into every TemplateResponse so it cannot be
missing depending on which route created the template environment.
"""
from pathlib import Path
from fastapi.templating import Jinja2Templates as _Jinja2Templates
from app.content.store import load_content

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"


class Jinja2Templates(_Jinja2Templates):
    def __init__(self, directory=None, *args, **kwargs):
        super().__init__(directory=str(directory or TEMPLATES_DIR), *args, **kwargs)
        # Keep the helper available for templates that access site() directly.
        self.env.globals["site"] = load_content

    def TemplateResponse(self, *args, **kwargs):
        # Starlette/FastAPI has changed TemplateResponse signatures across
        # versions.  Inject the helper into the context regardless of the
        # calling style used by existing routes.
        context = kwargs.get("context")
        if context is None:
            context = {}
            kwargs["context"] = context
        elif not isinstance(context, dict):
            context = dict(context)
            kwargs["context"] = context

        context.setdefault("site", load_content)
        return super().TemplateResponse(*args, **kwargs)
