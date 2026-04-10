import datetime

from sqlalchemy import String, Time, PrimaryKeyConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class BaseModel(DeclarativeBase):
    pass


class BusRoute(BaseModel):
    __tablename__ = "bus_route"
    route_id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(nullable=False)
    company_name: Mapped[str] = mapped_column(String(30), nullable=False)
    company_telephone: Mapped[str] = mapped_column(String(15), nullable=False)
    district_code: Mapped[int] = mapped_column(nullable=False)
    up_first_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    up_last_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    down_first_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    down_last_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    start_stop_id: Mapped[int] = mapped_column(nullable=False)
    end_stop_id: Mapped[int] = mapped_column(nullable=False)
    route_name: Mapped[str] = mapped_column(String(30), nullable=False)
    route_type_code: Mapped[str] = mapped_column(String(10), nullable=False)
    route_type_name: Mapped[str] = mapped_column(String(10), nullable=False)


class BusStop(BaseModel):
    __tablename__ = "bus_stop"
    stop_id: Mapped[int] = mapped_column(primary_key=True)
    stop_name: Mapped[str] = mapped_column(String(30), nullable=False)
    district_code: Mapped[int] = mapped_column(nullable=False)
    mobile_number: Mapped[str] = mapped_column(String(15), nullable=False)
    region_name: Mapped[str] = mapped_column(String(10), nullable=False)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)


class BusRouteStop(BaseModel):
    __tablename__ = "bus_route_stop"
    __table_args__ = (PrimaryKeyConstraint("route_id", "stop_id", name="pk_bus_route_stop"),)
    route_id: Mapped[int] = mapped_column(ForeignKey("bus_route.route_id"), nullable=False)
    stop_id: Mapped[int] = mapped_column(ForeignKey("bus_stop.stop_id"), nullable=False)
    start_stop_id: Mapped[int] = mapped_column(ForeignKey("bus_stop.stop_id"), nullable=False)
    stop_seq: Mapped[int] = mapped_column(nullable=False)


class BusDepartureLog(BaseModel):
    __tablename__ = "bus_departure_log"
    __table_args__ = (PrimaryKeyConstraint(
        "route_id",
        "stop_id",
        "departure_date",
        "departure_time",
        name="pk_bus_departure_log"),)
    stop_id: Mapped[int] = mapped_column(ForeignKey("bus_stop.stop_id"), nullable=False)
    route_id: Mapped[int] = mapped_column(ForeignKey("bus_route.route_id"), nullable=False)
    departure_date: Mapped[datetime.date] = mapped_column(nullable=False)
    departure_time: Mapped[datetime.time] = mapped_column(nullable=False)
    vehicle_id: Mapped[str] = mapped_column(String(20), nullable=False)
