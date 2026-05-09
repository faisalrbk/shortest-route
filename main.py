from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
from services import PORTS
app = FastAPI()

app.mount(
    "/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static"
)


def render(template_name: str, **kwargs) -> str:
    path = Path(__file__).parent / "templates" / template_name
    html = path.read_text(encoding="utf-8")
    for key, val in kwargs.items():
        html = html.replace(f"{{{{{key}}}}}", str(val))
    return html


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return render("index.html", title="Shortest Route")

@app.get("/api/ports")
async def get_ports():
    return PORTS

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
