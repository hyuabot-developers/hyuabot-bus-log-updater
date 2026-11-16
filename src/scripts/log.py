import asyncio
from datetime import datetime

from aiohttp import ClientError, ClientSession, ClientTimeout
from sqlalchemy import delete, and_, insert
from sqlalchemy.orm import Session

from models import BusDepartureLog

BASE_URL = "https://api.gbis.go.kr/ws/rest/pastarrivalservice/json"
REQUEST_TIMEOUT = ClientTimeout(total=15.0)
MAX_ATTEMPTS = 4
RETRY_BACKOFF_SECONDS = 1.5


async def fetch_log_items(
    http_session: ClientSession,
    stop_id: int,
    route_id: int,
    seq: int,
    search_date: str,
) -> list[dict] | None:
    """Fetch departure logs. Returns None when every attempt failed."""
    params = {
        "serviceKey": "1234567890",
        "stationId": stop_id,
        "routeId": route_id,
        "staOrder": seq,
        "sDay": search_date,
    }
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            async with http_session.get(BASE_URL, params=params) as response:
                response.raise_for_status()
                response_json = await response.json(content_type=None)
            msg_body = (response_json or {}).get("response", {}).get("msgBody") or {}
            arrival_list = msg_body.get("pastArrivalList") or []
            if isinstance(arrival_list, dict):
                arrival_list = [arrival_list]
            return _parse_items(arrival_list, stop_id, route_id)
        except (asyncio.TimeoutError, ClientError, ValueError, AttributeError) as e:
            if attempt == MAX_ATTEMPTS:
                print(f"Fetch failed stop={stop_id} route={route_id} "
                      f"date={search_date}: {type(e).__name__} {e}")
                return None
            await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
    return None


def _parse_items(arrival_list: list[dict], stop_id: int, route_id: int) -> list[dict]:
    log_items: dict[str, dict] = {}
    for arrival in arrival_list:
        departure_datetime_str = arrival.get("depatureDate") or arrival.get("arrivalDate")
        if not departure_datetime_str:
            continue
        departure_datetime = datetime.strptime(departure_datetime_str, "%Y-%m-%d %H:%M")
        departure_time = f'{departure_datetime.time().strftime("%H:%M")} +09:00'
        # Primary key is (route, stop, date, time): drop duplicates in one response.
        log_items[f"{departure_datetime.date()} {departure_time}"] = {
            "stop_id": stop_id,
            "route_id": route_id,
            "departure_date": departure_datetime.date(),
            "departure_time": departure_time,
            "vehicle_id": arrival["vehId"],
        }
    return list(log_items.values())


def save_log_items(
    db_session: Session,
    stop_id: int,
    route_id: int,
    search_date: str,
    log_items: list[dict],
) -> None:
    if not log_items:
        return
    try:
        db_session.execute(delete(BusDepartureLog).where(and_(
            BusDepartureLog.stop_id == stop_id,
            BusDepartureLog.route_id == route_id,
            BusDepartureLog.departure_date == search_date,
        )))
        db_session.execute(insert(BusDepartureLog), log_items)
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
