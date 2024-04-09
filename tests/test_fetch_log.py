import asyncio
import os
from datetime import timedelta, datetime, date, time

import pytest
from pytz import timezone
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from models import BaseModel, BusDepartureLog, BusRouteStop
from scripts.log import get_log_data
from tests.insert_bus_information import initialize_bus_data
from utils.database import get_db_engine


class TestFetchRealtimeData:
    connection: Engine | None = None
    session_constructor = None
    session: Session | None = None

    @classmethod
    def setup_class(cls):
        cls.connection = get_db_engine()
        cls.session_constructor = sessionmaker(bind=cls.connection)
        # Database session check
        cls.session = cls.session_constructor()
        assert cls.session is not None
        # Migration schema check
        BaseModel.metadata.create_all(cls.connection)
        # Insert initial data
        asyncio.run(initialize_bus_data(cls.session))
        cls.session.commit()
        cls.session.close()

    @pytest.mark.asyncio
    async def test_fetch_log_data(self):
        connection = get_db_engine()
        session_constructor = sessionmaker(bind=connection)
        # Database session check
        session = session_constructor()
        # Get list to fetch
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

        # Check if the data is inserted
        logs = session.query(BusDepartureLog).all()
        for log_item in logs:  # type: BusDepartureLog
            assert isinstance(log_item.route_id, int)
            assert isinstance(log_item.stop_id, int)
            assert isinstance(log_item.departure_date, date)
            assert isinstance(log_item.departure_time, time)
            assert isinstance(log_item.vehicle_id, str)
