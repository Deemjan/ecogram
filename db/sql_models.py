from typing import Optional, List

from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

from db.base_models import *


class UserAchievementLink(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    achievement_id: Optional[int] = Field(default=None, foreign_key="achievement.id", primary_key=True)
    unlock_date: Optional[datetime]
    unlocked: bool = False


class DeliveryThrashLink(SQLModel, table=True):
    thrash_type_id: Optional[int] = Field(default=None, foreign_key="deliveryrequest.id", primary_key=True)
    request_id: Optional[int] = Field(default=None, foreign_key="thrashtype.id", primary_key=True)


class PointThrashLink(SQLModel, table=True):
    thrash_type_id: Optional[int] = Field(default=None, foreign_key="thrashtype.id", primary_key=True)
    map_point_id: Optional[int] = Field(default=None, foreign_key="mappoint.id", primary_key=True)


class Achievement(AchievementBase, table=True):
    __table_args__ = (UniqueConstraint("title"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    users_with_achievement: List["User"] = Relationship(back_populates='achievements', link_model=UserAchievementLink)


class Role(RoleBase, table=True):
    __table_args__ = (UniqueConstraint("name"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    users_with_role: List["User"] = Relationship(back_populates="role")


class User(UserBase, table=True):
    __table_args__ = (UniqueConstraint("phone_number"), UniqueConstraint("username"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    password: str

    role_id: Optional[int] = Field(default=None, foreign_key="role.id")
    role: Role = Relationship(back_populates="users_with_role")

    achievements: List[Achievement] = Relationship(back_populates='users_with_achievement',
                                                   link_model=UserAchievementLink,
                                                   sa_relationship_kwargs=dict(cascade="all, delete"))

    users_on_request: List["DeliveryRequest"] = Relationship(back_populates="req_user")


class Courier(CourierBase, table=True):
    __table_args__ = (UniqueConstraint("phone_number"), UniqueConstraint("username"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    role: str = "courier"

    couriers_on_request: List["DeliveryRequest"] = Relationship(back_populates="req_courier")


class ThrashType(ThrashTypeBase, table=True):
    __table_args__ = (UniqueConstraint("thrash_type"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    requests_with_thrash_type: List["DeliveryRequest"] = Relationship(back_populates='thrash_types',
                                                                      link_model=DeliveryThrashLink)

    map_points: List["MapPoint"] = Relationship(back_populates="accepted_thrash", link_model=PointThrashLink)


class Status(StatusBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_statuses: List["DeliveryRequest"] = Relationship(back_populates="status")


class DeliveryRequest(DeliveryRequestBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    id_courier: Optional[int] = Field(default=None, foreign_key="courier.id")
    req_courier: Courier = Relationship(back_populates="couriers_on_request")

    id_user: Optional[int] = Field(default=None, foreign_key="user.id")
    req_user: User = Relationship(back_populates="users_on_request")

    status_id: Optional[int] = Field(default=None, foreign_key="status.id")
    status: Status = Relationship(back_populates="request_statuses")

    thrash_types: List[ThrashType] = Relationship(back_populates='requests_with_thrash_type',
                                                  link_model=DeliveryThrashLink)


class Map(MapBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    points: List["MapPoint"] = Relationship(back_populates="map")


class MapPoint(MapPointBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    id_map: Optional[int] = Field(default=None, foreign_key="map.id")
    map: Map = Relationship(back_populates="points")

    accepted_thrash: List[ThrashType] = Relationship(back_populates="map_points", link_model=PointThrashLink)
