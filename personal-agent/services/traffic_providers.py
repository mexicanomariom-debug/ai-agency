"""Traffic providers: Google (worldwide), Yandex & 2GIS (Russia)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

from config import settings

if TYPE_CHECKING:
    from database.models import User

logger = logging.getLogger(__name__)

RU_TIMEZONES = {
    "Europe/Kaliningrad",
    "Europe/Moscow",
    "Europe/Samara",
    "Europe/Volgograd",
    "Europe/Ulyanovsk",
    "Europe/Astrakhan",
    "Europe/Saratov",
    "Europe/Kirov",
    "Asia/Yekaterinburg",
    "Asia/Omsk",
    "Asia/Novosibirsk",
    "Asia/Barnaul",
    "Asia/Tomsk",
    "Asia/Novokuznetsk",
    "Asia/Krasnoyarsk",
    "Asia/Irkutsk",
    "Asia/Chita",
    "Asia/Yakutsk",
    "Asia/Khandyga",
    "Asia/Vladivostok",
    "Asia/Ust-Nera",
    "Asia/Magadan",
    "Asia/Sakhalin",
    "Asia/Srednekolymsk",
    "Asia/Kamchatka",
    "Asia/Anadyr",
}

RU_ADDRESS_HINTS = (
    "россия",
    "russia",
    "москва",
    "moscow",
    "спб",
    "питер",
    "санкт-петербург",
    "екатеринбург",
    "новосибирск",
    "казань",
    "краснодар",
    "сочи",
    "ростов",
    "нижний",
    "воронеж",
    "самара",
    "уфа",
    "красноярск",
    "пермь",
    "волгоград",
)

PROVIDER_LABELS = {
    "auto": "Авто",
    "google": "Google Maps",
    "yandex": "Яндекс Карты",
    "dgis": "2ГИС",
}


@dataclass
class TrafficResult:
    origin: str
    destination: str
    duration_min: int
    duration_in_traffic_min: int
    delay_min: int
    distance_km: float
    summary: str
    provider: str = "google"

    @property
    def is_congested(self) -> bool:
        return self.delay_min > 0


def is_russia_context(user: "User", origin: str | None = None, destination: str | None = None) -> bool:
    if (user.timezone or "") in RU_TIMEZONES:
        return True
    blob = f"{origin or ''} {destination or ''} {getattr(user, 'traffic_origin', '') or ''} {getattr(user, 'traffic_destination', '') or ''}".lower()
    return any(hint in blob for hint in RU_ADDRESS_HINTS)


def resolve_provider(user: "User", origin: str, destination: str) -> str:
    explicit = getattr(user, "traffic_provider", None) or "auto"
    if explicit in ("google", "yandex", "dgis"):
        return explicit
    if is_russia_context(user, origin, destination):
        if settings.yandex_maps_api_key:
            return "yandex"
        if settings.dgis_api_key:
            return "dgis"
    return "google"


async def fetch_traffic_for_user(user: "User", origin: str, destination: str) -> TrafficResult | None:
    provider = resolve_provider(user, origin, destination)
    fetchers = {
        "google": fetch_google_traffic,
        "yandex": fetch_yandex_traffic,
        "dgis": fetch_dgis_traffic,
    }
    result = await fetchers[provider](origin, destination)
    if result:
        result.provider = provider
        return result

    if provider != "google" and settings.google_maps_api_key:
        fallback = await fetch_google_traffic(origin, destination)
        if fallback:
            fallback.provider = "google"
        return fallback
    return None


async def fetch_google_traffic(origin: str, destination: str) -> TrafficResult | None:
    api_key = settings.google_maps_api_key
    if not api_key:
        return None

    params = {
        "origin": origin,
        "destination": destination,
        "departure_time": "now",
        "traffic_model": "best_guess",
        "language": "ru",
        "key": api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get("https://maps.googleapis.com/maps/api/directions/json", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.exception("Google Directions error")
        return None

    if data.get("status") != "OK" or not data.get("routes"):
        logger.warning("Google Directions status: %s", data.get("status"))
        return None

    leg = data["routes"][0]["legs"][0]
    duration_sec = leg["duration"]["value"]
    traffic_sec = leg.get("duration_in_traffic", leg["duration"])["value"]
    distance_m = leg.get("distance", {}).get("value", 0)
    duration_min = max(1, duration_sec // 60)
    traffic_min = max(1, traffic_sec // 60)

    return TrafficResult(
        origin=origin,
        destination=destination,
        duration_min=duration_min,
        duration_in_traffic_min=traffic_min,
        delay_min=max(0, traffic_min - duration_min),
        distance_km=round(distance_m / 1000, 1),
        summary=data["routes"][0].get("summary", ""),
        provider="google",
    )


async def _yandex_geocode(address: str) -> tuple[float, float] | None:
    api_key = settings.yandex_maps_api_key
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://geocode-maps.yandex.ru/1.x/",
                params={
                    "apikey": api_key,
                    "geocode": address,
                    "format": "json",
                    "lang": "ru_RU",
                    "results": 1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        members = data.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
        if not members:
            return None
        pos = members[0]["GeoObject"]["Point"]["pos"]
        lon_str, lat_str = pos.split()
        return float(lat_str), float(lon_str)
    except Exception:
        logger.exception("Yandex geocode failed for %s", address)
        return None


async def _yandex_route_seconds(points: list[tuple[float, float]], *, traffic_enabled: bool) -> int | None:
    api_key = settings.yandex_maps_api_key
    if not api_key or len(points) < 2:
        return None

    waypoints = "|".join(f"{lat},{lon}" for lat, lon in points)
    params = {
        "apikey": api_key,
        "waypoints": waypoints,
        "mode": "driving",
    }
    if not traffic_enabled:
        params["traffic"] = "disabled"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get("https://api.routing.yandex.net/v2/route", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.exception("Yandex route failed")
        return None

    route = data.get("route") or data.get("routes", [{}])[0]
    legs = route.get("legs") or []
    total = 0.0
    for leg in legs:
        for step in leg.get("steps", []):
            total += float(step.get("duration", 0))
    if total <= 0:
        total = float(route.get("duration", 0) or 0)
    return int(total) if total > 0 else None


async def fetch_yandex_traffic(origin: str, destination: str) -> TrafficResult | None:
    if not settings.yandex_maps_api_key:
        return None

    origin_pt = await _yandex_geocode(origin)
    dest_pt = await _yandex_geocode(destination)
    if not origin_pt or not dest_pt:
        return None

    points = [origin_pt, dest_pt]
    with_traffic = await _yandex_route_seconds(points, traffic_enabled=True)
    without_traffic = await _yandex_route_seconds(points, traffic_enabled=False)
    if not with_traffic:
        return None

    duration_min = max(1, (without_traffic or with_traffic) // 60)
    traffic_min = max(1, with_traffic // 60)
    delay_min = max(0, traffic_min - duration_min)

    return TrafficResult(
        origin=origin,
        destination=destination,
        duration_min=duration_min,
        duration_in_traffic_min=traffic_min,
        delay_min=delay_min,
        distance_km=0.0,
        summary="Яндекс Карты",
        provider="yandex",
    )


async def _dgis_geocode(address: str) -> tuple[float, float] | None:
    api_key = settings.dgis_api_key
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://catalog.api.2gis.com/3.0/items/geocode",
                params={"q": address, "key": api_key, "fields": "items.point"},
            )
            resp.raise_for_status()
            data = resp.json()
        items = data.get("result", {}).get("items") or data.get("items") or []
        if not items:
            return None
        point = items[0].get("point") or items[0].get("geometry", {}).get("centroid")
        if not point:
            return None
        return float(point["lat"]), float(point["lon"])
    except Exception:
        logger.exception("2GIS geocode failed for %s", address)
        return None


async def _dgis_route_seconds(
    points: list[tuple[float, float]],
    *,
    traffic_mode: str,
) -> int | None:
    api_key = settings.dgis_api_key
    if not api_key or len(points) < 2:
        return None

    body = {
        "points": [{"type": "stop", "lon": lon, "lat": lat} for lat, lon in points],
        "transport": "driving",
        "route_mode": "fastest",
        "traffic_mode": traffic_mode,
        "locale": "ru",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://routing.api.2gis.com/routing/7.0.0/global",
                params={"key": api_key},
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.exception("2GIS route failed")
        return None

    result = data.get("result") or data
    routes = result.get("routes") or []
    if not routes:
        return None
    duration = routes[0].get("total_duration") or routes[0].get("duration")
    return int(duration) if duration else None


async def fetch_dgis_traffic(origin: str, destination: str) -> TrafficResult | None:
    if not settings.dgis_api_key:
        return None

    origin_pt = await _dgis_geocode(origin)
    dest_pt = await _dgis_geocode(destination)
    if not origin_pt or not dest_pt:
        return None

    points = [origin_pt, dest_pt]
    with_traffic = await _dgis_route_seconds(points, traffic_mode="jam")
    without_traffic = await _dgis_route_seconds(points, traffic_mode="statistics")
    if not with_traffic:
        return None

    duration_min = max(1, (without_traffic or with_traffic) // 60)
    traffic_min = max(1, with_traffic // 60)

    return TrafficResult(
        origin=origin,
        destination=destination,
        duration_min=duration_min,
        duration_in_traffic_min=traffic_min,
        delay_min=max(0, traffic_min - duration_min),
        distance_km=0.0,
        summary="2ГИС",
        provider="dgis",
    )
