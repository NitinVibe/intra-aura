from pathlib import Path

ROOT = Path(__file__).resolve().parent
routes = ROOT / "app" / "routes"

changed = []
for path in routes.glob("*.py"):
    text = path.read_text(encoding="utf-8")
    old = "from fastapi.templating import Jinja2Templates"
    if old in text:
        text = text.replace(old, "from app.template_config import Jinja2Templates")
        path.write_text(text, encoding="utf-8")
        changed.append(str(path))

print("Template helper installed: app/template_config.py")
if changed:
    print("Updated route files:")
    for p in changed:
        print(" -", p)
else:
    print("No standard Jinja2Templates imports were found to replace.")
print("Now restart Uvicorn and open /account/login")
