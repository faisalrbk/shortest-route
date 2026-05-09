import re
from pathlib import Path
import searoute as sr


# ── Port loading ───────────────────────────────────────────────────────────────


def load_ports():
    sql = (Path(__file__).parent / "static" / "data" / "ports_1000.sql").read_text(
        encoding="utf-8"
    )
    pattern = r"\((\d+),\s*'(.+?)',\s*'(.+?)',\s*([\d\.\-]+),\s*([\d\.\-]+)"
    matches = re.findall(pattern, sql)

    ports = []
    for m in matches:
        pid, name, country, lat, lon = m
        ports.append(
            {
                "id": int(pid),
                "name": name,
                "country": country,
                "lat": float(lat),
                "lon": float(lon),
            }
        )
    return ports


PORTS = load_ports()

# id → port dict for O(1) lookup
_PORTS_BY_ID: dict[int, dict] = {p["id"]: p for p in PORTS}


# ── Route calculation ──────────────────────────────────────────────────────────


class RouteError(ValueError):
    """Raised when a route cannot be calculated."""


def _knots_to_display(nm: float, speed_knot: float) -> dict:
    """Return human-readable transit times at given speed."""
    hours = nm / speed_knot
    return {
        "hours": round(hours, 2),
        "days": round(hours / 24, 2),
    }


def calculate_route(origin_id: int, destination_id: int) -> dict:
    """
    Calculate shortest sea route between two ports.

    searoute expects coordinates as [lon, lat].

    Returns a dict ready to be serialised as JSON:
    {
        "origin":      { id, name, country, lat, lon },
        "destination": { id, name, country, lat, lon },
        "distance": {
            "km":   float,
            "nm":   float,      # nautical miles
            "mi":   float,
            "m":    float,
        },
        "duration": {
            "hours": float,
            "days":  float,
        },
        "speed_knot": float,    # knots used for duration estimate (default 24)
        "geojson": { ... }      # GeoJSON LineString Feature — coordinates [lon, lat]
                                # pass this straight to the frontend map
    }
    """
    origin_port = _PORTS_BY_ID.get(origin_id)
    dest_port = _PORTS_BY_ID.get(destination_id)

    if origin_port is None:
        raise RouteError(f"Origin port id={origin_id} not found.")
    if dest_port is None:
        raise RouteError(f"Destination port id={destination_id} not found.")
    if origin_id == destination_id:
        raise RouteError("Origin and destination must be different ports.")

    # searoute wants [lon, lat]
    origin_coords = [origin_port["lon"], origin_port["lat"]]
    dest_coords = [dest_port["lon"], dest_port["lat"]]

    speed_knot = 24  # default vessel speed

    # Run once in km (base), once in nautical miles
    route_km = sr.searoute(
        origin_coords,
        dest_coords,
        units="km",
        speed_knot=speed_knot,
        append_orig_dest=True,  # include port dots in the line
    )
    route_naut = sr.searoute(
        origin_coords,
        dest_coords,
        units="naut",
        speed_knot=speed_knot,
    )
    route_mi = sr.searoute(
        origin_coords,
        dest_coords,
        units="mi",
        speed_knot=speed_knot,
    )

    km = round(route_km.properties["length"], 2)
    nm = round(route_naut.properties["length"], 2)
    mi = round(route_mi.properties["length"], 2)
    m = round(km * 1000, 2)

    # duration_hours is already in the properties when speed_knot is passed
    duration_hours = route_km.properties.get("duration_hours") or (nm / speed_knot)

    return {
        "origin": origin_port,
        "destination": dest_port,
        "distance": {
            "km": km,
            "nm": nm,
            "mi": mi,
            "m": m,
        },
        "duration": {
            "hours": round(duration_hours, 2),
            "days": round(duration_hours / 24, 2),
        },
        "speed_knot": speed_knot,
        # GeoJSON Feature with LineString geometry — ready for ArcGIS
        "geojson": {
            "type": "Feature",
            "geometry": route_km.geometry,  # { type: "LineString", coordinates: [[lon,lat], ...] }
            "properties": {},
        },
    }
