"""Traffic providers: Google (worldwide), Yandex & 2GIS (Russia)."""

from __future__ import annotations

import asyncio
import logging
import math
import time
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

_google_last_error: str | None = None
_dgis_last_error: str | None = None
_yandex_last_error: str | None = None


def consume_google_last_error() -> str | None:
    global _google_last_error
    err = _google_last_error
    _google_last_error = None
    return err


def consume_provider_last_error(provider: str) -> str | None:
    global _dgis_last_error, _yandex_last_error
    if provider == "dgis":
        err = _dgis_last_error
        _dgis_last_error = None
        return err
    if provider == "yandex":
        err = _yandex_last_error
        _yandex_last_error = None
        return err
    return consume_google_last_error()


def _set_google_error(status: str | None, error_message: str | None = None, *, context: str = "") -> None:
    global _google_last_error
    parts = [p for p in (status, error_message, context) if p]
    if parts:
        _google_last_error = ": ".join(parts)


def _set_provider_error(provider: str, message: str) -> None:
    global _dgis_last_error, _yandex_last_error
    if provider == "dgis":
        _dgis_last_error = message
    elif provider == "yandex":
        _yandex_last_error = message


def _parse_2gis_meta(data: dict) -> str | None:
    meta = data.get("meta") or {}
    code = meta.get("code")
    if code and code != 200:
        err = meta.get("error") or {}
        return f"2ГИС {code}: {err.get('message') or err.get('type') or 'ошибка API'}"
    return None


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
    monitor_mode: str = "route"
    area_detail: str | None = None

    @property
    def is_congested(self) -> bool:
        return self.delay_min > 0


def is_russia_context(user: "User", origin: str | None = None, destination: str | None = None) -> bool:
    """Detect Russia/CIS from the monitored addresses, not the user's timezone."""
    blob = f"{origin or ''} {destination or ''}".lower()
    if any(hint in blob for hint in RU_ADDRESS_HINTS):
        return True
    latam_hints = (
        "mexico",
        "мексика",
        "playa del carmen",
        "playa",
        "cancun",
        "канкун",
        "quintana roo",
        "tulum",
        "merida",
        "usa",
        "сша",
        "new york",
        "miami",
        "london",
        "paris",
    )
    if any(hint in blob for hint in latam_hints):
        return False
    if not origin and not destination:
        return (user.timezone or "") in RU_TIMEZONES
    return False


def resolve_provider(
    user: "User",
    origin: str,
    destination: str,
    *,
    override: str | None = None,
) -> str:
    if override in ("google", "yandex", "dgis"):
        return override

    stored = getattr(user, "traffic_provider", None) or "auto"
    if stored in ("google", "yandex", "dgis"):
        return stored

    if is_russia_context(user, origin, destination):
        if settings.yandex_maps_api_key:
            return "yandex"
        if settings.dgis_api_key:
            return "dgis"
    return "google"


async def fetch_traffic_for_user(
    user: "User",
    origin: str,
    destination: str,
    *,
    provider_override: str | None = None,
) -> TrafficResult | None:
    provider = resolve_provider(user, origin, destination, override=provider_override)
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


async def fetch_area_traffic_for_user(
    user: "User",
    location: str,
    *,
    provider_override: str | None = None,
) -> TrafficResult | None:
    """Probe traffic around a city, district or street."""
    provider = resolve_provider(user, location, location, override=provider_override)
    center = await _geocode(provider, location)
    if not center and provider != "google":
        center = await _geocode("google", location)
        if center:
            provider = "google"
    if not center:
        return None

    probes = _probe_points(center[0], center[1])
    delays: list[tuple[str, int, int, int]] = []

    probe_results = await asyncio.gather(
        *[_route_delay(provider, center, (lat, lon)) for lat, lon, _direction in probes],
        return_exceptions=True,
    )
    for (lat, lon, direction), delay_info in zip(probes, probe_results, strict=True):
        if isinstance(delay_info, Exception):
            logger.warning("Area probe failed (%s): %s", direction, delay_info)
            continue
        if delay_info:
            base_min, traffic_min, delay = delay_info
            delays.append((direction, base_min, traffic_min, delay))

    if not delays:
        if provider != "google" and settings.google_maps_api_key:
            for lat, lon, direction in probes:
                delay_info = await _route_delay("google", center, (lat, lon))
                if delay_info:
                    base_min, traffic_min, delay = delay_info
                    delays.append((direction, base_min, traffic_min, delay))
            provider = "google"

    if not delays:
        return None

    avg_base = sum(d[1] for d in delays) // len(delays)
    avg_traffic = sum(d[2] for d in delays) // len(delays)
    avg_delay = sum(d[3] for d in delays) // len(delays)
    worst = max(delays, key=lambda x: x[3])
    area_detail = f"средняя +{avg_delay} мин, макс. +{worst[3]} мин ({worst[0]})"

    return TrafficResult(
        origin=location,
        destination="мониторинг района",
        duration_min=avg_base,
        duration_in_traffic_min=avg_traffic,
        delay_min=avg_delay,
        distance_km=0.0,
        summary=PROVIDER_LABELS.get(provider, provider),
        provider=provider,
        monitor_mode="area",
        area_detail=area_detail,
    )


def _probe_points(lat: float, lon: float, km: float = 2.0) -> list[tuple[float, float, str]]:
    dlat = km / 111.0
    cos_lat = math.cos(math.radians(lat)) or 0.01
    dlon = km / (111.0 * cos_lat)
    return [
        (lat + dlat, lon, "север"),
        (lat, lon + dlon, "восток"),
        (lat - dlat, lon, "юг"),
        (lat, lon - dlon, "запад"),
    ]


async def _geocode(provider: str, address: str) -> tuple[float, float] | None:
    if provider == "yandex":
        return await _yandex_geocode(address)
    if provider == "dgis":
        return await _dgis_geocode(address)
    return await _google_geocode(address)


async def _route_delay(
    provider: str,
    origin: tuple[float, float],
    dest: tuple[float, float],
) -> tuple[int, int, int] | None:
    o_str = f"{origin[0]},{origin[1]}"
    d_str = f"{dest[0]},{dest[1]}"
    if provider == "yandex":
        with_t = await _yandex_route_seconds([origin, dest], traffic_enabled=True)
        without_t = await _yandex_route_seconds([origin, dest], traffic_enabled=False)
    elif provider == "dgis":
        with_t = await _dgis_route_seconds([origin, dest], traffic_mode="jam")
        without_t = await _dgis_route_seconds([origin, dest], traffic_mode="statistic")
    else:
        result = await fetch_google_traffic(o_str, d_str)
        if not result:
            return None
        return result.duration_min, result.duration_in_traffic_min, result.delay_min

    if not with_t:
        return None
    base = max(1, (without_t or with_t) // 60)
    traffic = max(1, with_t // 60)
    return base, traffic, max(0, traffic - base)


async def _google_geocode(address: str) -> tuple[float, float] | None:
    api_key = settings.google_maps_api_key
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": api_key, "language": "ru"},
            )
            resp.raise_for_status()
            data = resp.json()
        if data.get("status") != "OK" or not data.get("results"):
            _set_google_error(
                data.get("status"),
                data.get("error_message"),
                context=f"Geocoding ({address})",
            )
            logger.warning(
                "Google geocode status: %s error: %s for %s",
                data.get("status"),
                data.get("error_message"),
                address,
            )
            return None
        loc = data["results"][0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])
    except Exception:
        logger.exception("Google geocode failed for %s", address)
        return None


async def fetch_google_traffic(origin: str, destination: str) -> TrafficResult | None:
    api_key = settings.google_maps_api_key
    if not api_key:
        return None

    params = {
        "origin": origin,
        "destination": destination,
        "departure_time": int(time.time()),
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
        _set_google_error(
            data.get("status"),
            data.get("error_message"),
            context="Directions",
        )
        logger.warning(
            "Google Directions status: %s error: %s",
            data.get("status"),
            data.get("error_message"),
        )
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
        err = _parse_2gis_meta(data)
        if err:
            _set_provider_error("dgis", err)
            logger.warning("2GIS geocode failed for %s: %s", address, err)
            return None
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

    err = _parse_2gis_meta(data)
    if err:
        _set_provider_error("dgis", err)
        logger.warning("2GIS route error: %s", err)
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
    without_traffic = await _dgis_route_seconds(points, traffic_mode="statistic")
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


async def diagnose_google_maps() -> str | None:
    """Return human-readable Google API error, or None if key works."""
    api_key = settings.google_maps_api_key
    if not api_key:
        return "GOOGLE_MAPS_API_KEY не задан в секретах деплоя."

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            geocode = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": "Playa del Carmen", "key": api_key, "language": "ru"},
            )
            geocode.raise_for_status()
            geocode_data = geocode.json()
            if geocode_data.get("status") != "OK":
                return (
                    f"Geocoding API: {geocode_data.get('status')}"
                    f" — {geocode_data.get('error_message', 'нет деталей')}"
                )

            loc = geocode_data["results"][0]["geometry"]["location"]
            origin = f"{loc['lat']},{loc['lng']}"
            dest = f"{loc['lat'] + 0.01},{loc['lng'] + 0.01}"
            directions = await client.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params={
                    "origin": origin,
                    "destination": dest,
                    "departure_time": int(time.time()),
                    "traffic_model": "best_guess",
                    "key": api_key,
                },
            )
            directions.raise_for_status()
            directions_data = directions.json()
            if directions_data.get("status") != "OK":
                return (
                    f"Directions API: {directions_data.get('status')}"
                    f" — {directions_data.get('error_message', 'нет деталей')}"
                )
    except Exception as exc:
        logger.exception("Google Maps diagnostic failed")
        return f"Сетевая ошибка при проверке Google Maps: {exc}"

    return None


async def diagnose_dgis() -> str | None:
    api_key = settings.dgis_api_key
    if not api_key:
        return "DGIS_API_KEY не задан в секретах деплоя."

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            geocode = await client.get(
                "https://catalog.api.2gis.com/3.0/items/geocode",
                params={"q": "Москва, Красная площадь", "key": api_key, "fields": "items.point"},
            )
            geocode.raise_for_status()
            geocode_data = geocode.json()
            err = _parse_2gis_meta(geocode_data)
            if err:
                return f"Geocoder: {err}"
            items = geocode_data.get("result", {}).get("items") or geocode_data.get("items") or []
            if not items:
                return "Geocoder: пустой ответ (проверьте API Геокодера в кабинете 2ГИС)"

            point = items[0].get("point") or items[0].get("geometry", {}).get("centroid")
            if not point:
                return "Geocoder: нет координат в ответе"

            route = await client.post(
                "https://routing.api.2gis.com/routing/7.0.0/global",
                params={"key": api_key},
                json={
                    "points": [
                        {"type": "stop", "lon": point["lon"], "lat": point["lat"]},
                        {"type": "stop", "lon": point["lon"] + 0.01, "lat": point["lat"] + 0.01},
                    ],
                    "transport": "driving",
                    "route_mode": "fastest",
                    "traffic_mode": "jam",
                    "locale": "ru",
                },
            )
            route.raise_for_status()
            route_data = route.json()
            err = _parse_2gis_meta(route_data)
            if err:
                return f"Routing: {err}"
            routes = (route_data.get("result") or route_data).get("routes") or []
            if not routes:
                return "Routing: маршрут не построен (проверьте Routing API в кабинете 2ГИС)"
    except Exception as exc:
        logger.exception("2GIS diagnostic failed")
        return f"Сетевая ошибка при проверке 2ГИС: {exc}"

    return None
