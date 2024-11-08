import asyncio
from datetime import datetime

from aiohttp import ClientTimeout, ClientSession
from pytz import timezone
from sqlalchemy import delete, and_, insert
from sqlalchemy.orm import Session

from models import BusDepartureLog


async def get_log_data(
    db_session: Session,
    stop_id: str,
    route_id: str,
    seq: int,
    search_date: str,
) -> None:
    base_url = "https://api.gbis.go.kr/ws/rest/pastarrivalservice/json"
    params = {
        "serviceKey": "1234567890",
        "stationId": stop_id,
        "routeId": route_id,
        "staOrder": seq,
        "sDay": search_date,
    }
    log_items: list[dict] = []
    timeout = ClientTimeout(total=3.0)
    try:
        async with (ClientSession(timeout=timeout) as session):
            url = f'{base_url}?{"&".join([f"{key}={value}" for key, value in params.items()])}'
            async with session.get(url) as response:
                response_json = await response.json()
                arrival_list = response_json \
                    .get("response", {}).get("msgBody", {}).get("pastArrivalList", [])
                if len(arrival_list) == 0:
                    print(url)
                for arrival in arrival_list:
                    departure_datetime_str = arrival.get("depatureDate")
                    if not departure_datetime_str:
                        departure_datetime_str = arrival.get("arrivalDate")
                    if not departure_datetime_str:
                        continue
                    departure_datetime = datetime.strptime(
                        departure_datetime_str,
                        "%Y-%m-%d %H:%M",
                    )
                    departure_datetime.replace(tzinfo=timezone('Asia/Seoul'))
                    log_items.append({
                        "stop_id": stop_id,
                        "route_id": route_id,
                        "departure_date": departure_datetime.date(),
                        "departure_time": departure_datetime.time().strftime("%H:%M"),
                        "vehicle_id": arrival["vehId"],
                    })
        if log_items:
            date_query = datetime.strptime(search_date, "%Y-%m-%d").date()
            delete_statement = delete(BusDepartureLog).where(and_(
                BusDepartureLog.stop_id == stop_id,
                BusDepartureLog.route_id == route_id,
                BusDepartureLog.departure_date == date_query,
            ))
            db_session.execute(delete_statement)
            db_session.execute(
                insert(BusDepartureLog),
                log_items,
            )
        db_session.commit()
    except asyncio.exceptions.TimeoutError:
        print("TimeoutError", url)
    except AttributeError:
        print("AttributeError", url)
