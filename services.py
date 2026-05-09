from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
import re
from typing import Any

import searoute as sr


BASE_DIR = Path(__file__).resolve().parent
PORTS_SQL_PATH = BASE_DIR / "static" / "data" / "ports _1000.sql"


@dataclass(frozen=True)
class PortRecord:
	id: int
	name: str
	country: str
	lat: float
	lon: float
	region: str | None


@dataclass(frozen=True)
class ResolvedLocation:
	label: str
	kind: str
	coordinates: list[float]
	latitude: float
	longitude: float
	port: dict[str, Any] | None = None


_PORT_LINE_PATTERN = re.compile(
	r"^\((?P<id>\d+),\s*'(?P<name>(?:[^'\\]|\\.)*)',\s*'(?P<country>(?:[^'\\]|\\.)*)',\s*(?P<lat>-?\d+(?:\.\d+)?),\s*(?P<lon>-?\d+(?:\.\d+)?),\s*(?P<region>NULL|'(?:[^'\\]|\\.)*')\),?$"
)
_COORDINATE_PATTERN = re.compile(
	r"^\s*(?P<lat>-?\d+(?:\.\d+)?)\s*[,\s]+\s*(?P<lon>-?\d+(?:\.\d+)?)\s*$"
)


def _unescape_sql_text(value: str) -> str:
	return value.replace(r"\\'", "'").replace(r"\\\\", "\\")


def _normalize_text(value: str) -> str:
	return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


@lru_cache(maxsize=1)
def load_ports() -> list[PortRecord]:
	ports: list[PortRecord] = []
	for line in PORTS_SQL_PATH.read_text(encoding="utf-8").splitlines():
		match = _PORT_LINE_PATTERN.match(line.strip())
		if not match:
			continue

		region_raw = match.group("region")
		region = None if region_raw == "NULL" else _unescape_sql_text(region_raw[1:-1])
		ports.append(
			PortRecord(
				id=int(match.group("id")),
				name=_unescape_sql_text(match.group("name")),
				country=_unescape_sql_text(match.group("country")),
				lat=float(match.group("lat")),
				lon=float(match.group("lon")),
				region=region,
			)
		)

	return ports


@lru_cache(maxsize=1)
def _port_alias_index() -> dict[str, list[PortRecord]]:
	index: dict[str, list[PortRecord]] = defaultdict(list)
	for port in load_ports():
		aliases = (
			port.name,
			f"{port.name} {port.country}",
			f"{port.name}, {port.country}",
		)
		for alias in aliases:
			normalized = _normalize_text(alias)
			if port not in index[normalized]:
				index[normalized].append(port)
	return index


def _port_to_dict(port: PortRecord) -> dict[str, Any]:
	return asdict(port)


def _suggestions(matches: list[PortRecord], limit: int = 5) -> str:
	unique_matches: list[PortRecord] = []
	seen_ids: set[int] = set()
	for match in matches:
		if match.id in seen_ids:
			continue
		seen_ids.add(match.id)
		unique_matches.append(match)

	return ", ".join(f"{port.name} ({port.country})" for port in unique_matches[:limit])


def resolve_port(name: str) -> PortRecord:
	query = _normalize_text(name)
	if not query:
		raise ValueError("Location cannot be empty.")

	exact_matches = _port_alias_index().get(query, [])
	if len(exact_matches) == 1:
		return exact_matches[0]
	if len(exact_matches) > 1:
		raise ValueError(
			f"Port name is ambiguous. Try one of: {_suggestions(exact_matches)}"
		)

	partial_matches: list[PortRecord] = []
	for alias, ports in _port_alias_index().items():
		if query in alias:
			partial_matches.extend(ports)

	if len(partial_matches) == 1:
		return partial_matches[0]
	if len(partial_matches) > 1:
		raise ValueError(
			f"Port name is ambiguous. Try one of: {_suggestions(partial_matches)}"
		)

	raise ValueError(f"Unknown port name: {name}")


def resolve_location(value: str) -> ResolvedLocation:
	text = value.strip()
	if not text:
		raise ValueError("Location cannot be empty.")

	coordinate_match = _COORDINATE_PATTERN.match(text)
	if coordinate_match:
		latitude = float(coordinate_match.group("lat"))
		longitude = float(coordinate_match.group("lon"))
		if not (-90 <= latitude <= 90):
			raise ValueError("Latitude must be between -90 and 90.")
		if not (-180 <= longitude <= 180):
			raise ValueError("Longitude must be between -180 and 180.")

		return ResolvedLocation(
			label=text,
			kind="coordinates",
			coordinates=[longitude, latitude],
			latitude=latitude,
			longitude=longitude,
		)

	port = resolve_port(text)
	return ResolvedLocation(
		label=f"{port.name}, {port.country}",
		kind="port",
		coordinates=[port.lon, port.lat],
		latitude=port.lat,
		longitude=port.lon,
		port=_port_to_dict(port),
	)


def calculate_route(origin: str, destination: str, units: str = "naut") -> dict[str, Any]:
	origin_location = resolve_location(origin)
	destination_location = resolve_location(destination)

	normalized_units = units if units in {"km", "m", "mi", "ft", "in", "deg", "cen", "rad", "naut", "yd"} else "naut"
	route = sr.searoute(origin_location.coordinates, destination_location.coordinates, units=normalized_units)
	route_geojson = route.__geo_interface__
	properties = route_geojson.get("properties", {})

	return {
		"origin": {
			"label": origin_location.label,
			"kind": origin_location.kind,
			"latitude": origin_location.latitude,
			"longitude": origin_location.longitude,
			"coordinates": origin_location.coordinates,
			"port": origin_location.port,
		},
		"destination": {
			"label": destination_location.label,
			"kind": destination_location.kind,
			"latitude": destination_location.latitude,
			"longitude": destination_location.longitude,
			"coordinates": destination_location.coordinates,
			"port": destination_location.port,
		},
		"distance": properties.get("length"),
		"units": properties.get("units", normalized_units),
		"duration_hours": properties.get("duration_hours"),
		"route": route_geojson,
	}
