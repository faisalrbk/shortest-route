from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
import os
import re

app = FastAPI()


def render_simple_template(name: str, context: dict) -> str:
    """Simple template renderer that replaces {{ key }} placeholders.

    This is a temporary workaround for a Jinja2 caching incompatibility
    that can raise `TypeError: cannot use 'tuple' as a dict key` on some
    Jinja2 versions. For full Jinja2 support, upgrade/downgrade Jinja2.
    """
    base = os.path.dirname(__file__)
    path = os.path.join(base, "templates", name)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    for key, val in context.items():
        # only substitute simple placeholders like {{ title }}
        pattern = r"\{\{\s*" + re.escape(key) + r"\s*\}\}"
        text = re.sub(pattern, str(val), text)

    return text


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    html = render_simple_template(
        "index.html",
        {
            "request": request,
            "title": "Shortest Route",
            "message": "Hello from FastAPI templates!",
        },
    )
    return HTMLResponse(html)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
