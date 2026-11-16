import asyncio
import os
import sys
from datetime import datetime, timedelta

from aiohttp import ClientSession, TCPConnector
from pytz import timezone
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from models import BusRouteStop
from scripts.log import fetch_log_items, save_log_items, REQUEST_TIMEOUT
from utils.database import get_db_engine

CONCURRENCY = int(os.getenv("CONCURRENCY", 8))


async def main() -> int:
    connection = get_db_engine()
    session = sessionmaker(bind=connection)()
    try:
        return await execute_script(session)
    finally:
        session.close()


async def execute_script(session) -> int:
    targets = session.execute(
        select(BusRouteStop.stop_id, BusRouteStop.route_id, BusRouteStop.stop_seq)
    ).all()
    days_past = int(os.getenv("DAYS_PAST", 1))
    now = datetime.now(tz=timezone('Asia/Seoul'))
    dates = [
        (now - timedelta(days=day_past + 1)).strftime("%Y-%m-%d")
        for day_past in range(days_past)
    ]
    jobs = [(s, r, q, d) for s, r, q in targets for d in dates]
    semaphore = asyncio.Semaphore(CONCURRENCY)
    failed = 0

    async def fetch(job):
        async with semaphore:
            return await fetch_log_items(http_session, *job)

    connector = TCPConnector(limit=CONCURRENCY)
    async with ClientSession(timeout=REQUEST_TIMEOUT, connector=connector) as http_session:
        tasks = [asyncio.create_task(fetch(job)) for job in jobs]
        for job, task in zip(jobs, tasks):
            stop_id, route_id, _, date = job
            items = await task
            if items is None:
                failed += 1
                continue
            try:
                save_log_items(session, stop_id, route_id, date, items)
            except Exception as e:
                failed += 1
                print(f"DB save failed stop={stop_id} route={route_id} date={date}: {e}")
    print(f"Done: {len(jobs) - failed}/{len(jobs)} succeeded")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
