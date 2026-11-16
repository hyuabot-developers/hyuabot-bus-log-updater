import asyncio
from datetime import date, time

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from models import BaseModel, BusDepartureLog
from main import execute_script
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
        await execute_script(session)

        # Check if the data is inserted
        logs = session.query(BusDepartureLog).all()
        for log_item in logs:  # type: BusDepartureLog
            assert isinstance(log_item.route_id, int)
            assert isinstance(log_item.stop_id, int)
            assert isinstance(log_item.departure_date, date)
            assert isinstance(log_item.departure_time, time)
            assert isinstance(log_item.vehicle_id, str)
