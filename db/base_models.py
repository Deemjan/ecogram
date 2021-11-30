import inspect
from typing import Optional, NamedTuple, Type, List
from datetime import datetime, date
from phonenumbers import (
    NumberParseException,
    PhoneNumberFormat,
    PhoneNumberType,
    format_number,
    is_valid_number,
    number_type,
    parse as parse_phone_number,
)

from fastapi import Form
from sqlmodel import SQLModel
from pydantic import validator, ValidationError
from pydantic.fields import ModelField
import pytz

from src.views.security import get_password_hash

utc = pytz.UTC


def as_form(cls: Type[SQLModel]):
    new_parameters = []

    for field_name, model_field in cls.__fields__.items():
        model_field: ModelField  # type: ignore

        if not model_field.required:
            new_parameters.append(
                inspect.Parameter(
                    model_field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=Form(model_field.default),
                    annotation=model_field.outer_type_,
                )
            )
        else:
            new_parameters.append(
                inspect.Parameter(
                    model_field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=Form(...),
                    annotation=model_field.outer_type_,
                )
            )

    async def as_form_func(**data):
        return cls(**data)

    sig = inspect.signature(as_form_func)
    sig = sig.replace(parameters=new_parameters)
    as_form_func.__signature__ = sig  # type: ignore
    setattr(cls, 'as_form', as_form_func)
    return cls


class Point(NamedTuple):
    x: float
    y: float


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    phone: Optional[str] = None
    expires: Optional[datetime] = None


class AchievementBase(SQLModel):
    title: str
    description: Optional[str] = None


class AchievementCreate(AchievementBase):
    pass


class AchievementDelete(SQLModel):
    id: Optional[int] = None
    title: Optional[str] = None


class AchievementUpdate(SQLModel):
    id: Optional[int] = None
    old_title: Optional[str] = None
    new_title: Optional[str] = None
    description: Optional[str] = None


class RoleBase(SQLModel):
    name: str


class RoleCreate(RoleBase):
    pass


class RoleUpdate(SQLModel):
    old_id: Optional[int] = None
    old_name: Optional[str] = None
    new_name: str

    @validator("new_name")
    def role_update_validator(cls, new_name: str, values):
        old_id = values.get("old_id")
        old_name = values.get("old_name")
        if not old_id and not old_name:
            raise ValidationError
        return new_name


class RoleDelete(SQLModel):
    id: Optional[int] = None
    name: Optional[str] = None

    @validator("name")
    def role_delete_validator(cls, name: str, values):
        id = values.get("id")
        if not id and not name:
            raise ValidationError
        return name


class UserAchievementUpdate(SQLModel):
    user_id: int
    achievement_id: int
    unlocked: bool = False
    unlock_date: datetime

    @validator("unlock_date")
    def unlock_date_validator(cls, date: datetime, values):
        if values.get("unlocked"):
            return date
        raise ValidationError


class PersonBase(SQLModel):
    phone_number: str
    username: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    birthday: Optional[date] = None

    @validator("phone_number")
    def check_phone_number(cls, v):
        if v is None:
            return v
        try:
            n = parse_phone_number(v, 'RU')
        except NumberParseException as e:
            raise ValidationError('Please provide a valid mobile phone number') from e

        return format_number(n, PhoneNumberFormat.NATIONAL if n.country_code == 7 else PhoneNumberFormat.INTERNATIONAL)


class UserBase(PersonBase):
    pass


@as_form
class UserCreate(PersonBase):
    password: str


class PersonGet(SQLModel):
    id_filter: Optional[int] = None
    phone_filter: Optional[str] = None
    username_filter: Optional[str] = None
    name_filter: Optional[str] = None
    last_name_filter: Optional[str] = None


class UserGet(PersonGet):
    birthday_filter_from: Optional[date] = None
    birthday_filter_to: Optional[date] = None
    role_filter: Optional[str] = None


class UserDelete(SQLModel):
    id: Optional[int] = None
    phone: Optional[str] = None
    username: Optional[str] = None


class UserUpdate(PersonBase):
    id: Optional[int] = None
    phone_number_old: Optional[str] = None
    phone_number_new: Optional[str] = None
    username_new: Optional[str] = None
    role: Optional[str] = None


class UserOut(UserBase):
    achievements: Optional[AchievementBase] = []
    role: Optional[RoleBase] = "basic_user"


class ThrashTypeBase(SQLModel):
    thrash_type: str


class ThrashTypeCreate(ThrashTypeBase):
    pass


class ThrashTypeUpdate(SQLModel):
    old_id: Optional[int] = None
    old_thrash_type: Optional[str] = None
    new_thrash_type: str

    @validator("new_thrash_type")
    def thrash_type_update_validator(cls, new_thrash_type: str, values):
        old_id = values.get("old_id")
        old_thrash_type = values.get("old_thrash_type")
        if not old_id and not old_thrash_type:
            raise ValidationError
        return new_thrash_type


class ThrashTypeDelete(SQLModel):
    id: Optional[int] = None
    thrash_type: Optional[str] = None

    @validator("thrash_type")
    def thrash_type_delete_validator(cls, thrash_type: str, values):
        id = values.get("id")
        if not id and not thrash_type:
            raise ValidationError
        return thrash_type


class StatusBase(SQLModel):
    status_name: str


class StatusCreate(StatusBase):
    pass


class StatusUpdate(SQLModel):
    old_id: Optional[int] = None
    old_status: Optional[str] = None
    new_status: str

    @validator("new_status")
    def status_update_validator(cls, new_status: str, values):
        old_id = values.get("old_id")
        old_status = values.get("old_status")
        if not old_id and not old_status:
            raise ValidationError
        return new_status


class StatusDelete(SQLModel):
    id: Optional[int] = None
    status_name: Optional[str] = None

    @validator("status_name")
    def status_delete_validator(cls, status_name: str, values):
        id = values.get("id")
        if not id and not status_name:
            raise ValidationError
        return status_name


class CourierBase(PersonBase):
    delivery_count: Optional[int] = None
    salary: Optional[float] = None


class CourierCreate(CourierBase):
    phone_number: str
    password: str

    @validator("password")
    def hash_password(cls, password):
        if not password:
            raise ValidationError
        return get_password_hash(password)


class CourierGet(PersonGet):
    delivery_count_from: Optional[int] = None
    delivery_count_to: Optional[int] = None

    salary_from: Optional[float] = None
    salary_to: Optional[float] = None

    birthday_from: Optional[date] = None
    birthday_to: Optional[date] = None


class CourierUpdate(CourierBase):
    phone_number: Optional[str] = None


class CourierDelete(SQLModel):
    id: Optional[int] = None
    phone: Optional[str] = None


class DeliveryRequestBase(SQLModel):
    address: str
    create_date: datetime


class DeliveryRequestCreate(SQLModel):
    courier_phone: str
    user_phone: str
    address: str
    create_date: datetime


class DeliveryRequestGet(SQLModel):
    id_filter: Optional[int] = None
    address_filter: Optional[str] = None
    create_date_from: Optional[datetime] = None
    create_date_to: Optional[datetime] = None
    thrash_type_filter: Optional[str] = None
    status_filter: Optional[str] = None
    courier_name_filter: Optional[str] = None
    courier_surname_filter: Optional[str] = None
    courier_phone_number_filter: Optional[str] = None
    user_phone_number_filter: Optional[str] = None
    user_surname_filter: Optional[str] = None
    user_name_filter: Optional[str] = None
    user_username_filter: Optional[str] = None


class DeliveryRequestUpdate(SQLModel):
    id_req: Optional[int] = None
    address: Optional[str] = None
    create_date: Optional[datetime] = None
    thrash_type_filter: Optional[List[str]] = None
    status: Optional[str] = None
    courier_phone: Optional[str] = None
    user_phone: Optional[str] = None


class DeliveryRequestDelete(SQLModel):
    req_id: int


class MapBase(SQLModel):
    city: str


class MapCreate(MapBase):
    pass


class MapUpdate(SQLModel):
    old_id: Optional[int] = None
    old_city: Optional[str] = None
    new_city: str

    @validator("new_city")
    def map_update_validator(cls, new_city: str, values):
        old_id = values.get("old_id")
        old_city = values.get("old_city")
        if not old_id and not old_city:
            raise ValidationError
        return new_city


class MapDelete(SQLModel):
    id: Optional[int] = None
    city: Optional[str] = None

    @validator("city")
    def map_delete_validator(cls, city: str, values):
        id = values.get("id")
        if not id and not city:
            raise ValidationError
        return city


class MapPointBase(SQLModel):
    title: str
    address: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    coordinates: Point


class MapPointGet(SQLModel):
    id_filter: Optional[int] = None
    title_filter: Optional[str] = None
    address_filter: Optional[str] = None
    phone_filter: Optional[str] = None
    email_filter: Optional[str] = None
    website_filter: Optional[str] = None
    coordinates_filter: Optional[Point] = None
    city_map_filter: Optional[str] = None
    # accepted_thrash_filter: Optional[List[str]] = None


class MapPointCreate(MapPointBase):
    city: Optional[str] = None
    accepted_thrash: List[str] = None


class MapPointDelete(SQLModel):
    id: int


class MapPointUpdate(MapPointBase):
    id: int
    title: Optional[str] = None
    address: Optional[str] = None
    coordinates: Optional[Point] = None
    city: Optional[str] = None
    accepted_thrash: List[str] = None


# class DeliveryRequestOut(DeliveryRequestBase):
#     address: str
#     create_date: datetime
#     status: StatusBase
#     courier = UserOut
#     user = UserOut
#     materials = List[ThrashTypeBase]

class PointThrashGet(SQLModel):
    point_id_filter: Optional[int] = None
    thrash_type_filter: Optional[str] = None
    title_filter: Optional[str] = None
    city_filter: Optional[str] = None
    email_filter: Optional[str] = None
    address_filter: Optional[str] = None
    phone_number_filter: Optional[str] = None
    website_filter: Optional[str] = None
    coordinates_filter: Point = None
