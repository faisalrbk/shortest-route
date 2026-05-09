from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

from services import PORTS, calculate_route, RouteError

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


@app.get("/api/route")
async def get_route(origin_id: int, destination_id: int):
    """
    Calculate shortest sea route between two ports.

    Query params:
        origin_id      (int) — port id from /api/ports
        destination_id (int) — port id from /api/ports

    Example:
        GET /api/route?origin_id=42&destination_id=7

    Returns:
    {
        "origin":      { id, name, country, lat, lon },
        "destination": { id, name, country, lat, lon },
        "distance": { "km": float, "nm": float, "mi": float, "m": float },
        "duration":  { "hours": float, "days": float },
        "speed_knot": float,
        "geojson": GeoJSON Feature (LineString) — draw this on the map
    }
    """
    try:
        result = calculate_route(origin_id, destination_id)
        return JSONResponse(content=result)
    except RouteError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route calculation failed: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
