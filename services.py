import re
from pathlib import Path


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
