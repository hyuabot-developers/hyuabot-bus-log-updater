import asyncio
import os
from datetime import datetime, timedelta

from pytz import timezone
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from models import BusRouteStop
from scripts.log import get_log_data
from utils.database import get_db_engine


async def main():
    connection = get_db_engine()
    session_constructor = sessionmaker(bind=connection)
    session = session_constructor()
    if session is None:
        raise RuntimeError("Failed to get db session")
    try:
        await execute_script(session)
    except OperationalError:
        return


async def execute_script(session):
    stop_query = select(BusRouteStop.stop_id, BusRouteStop.route_id, BusRouteStop.stop_sequence)
    session.execute(stop_query)
    days_past = os.getenv("DAYS_PAST", 1)
    for stop_id, route_id, seq in session.execute(stop_query):
        now = datetime.now(tz=timezone('Asia/Seoul'))
        for day_past in range(int(days_past)):
            day_param = (now - timedelta(days=(day_past + 1))).strftime(
                "%Y-%m-%d"
            )
            await get_log_data(session, stop_id, route_id, seq, day_param)
    session.close()

if __name__ == '__main__':
    asyncio.run(main())
