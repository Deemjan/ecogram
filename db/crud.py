import logging
from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from db.base_models import UserAchievementUpdate, RoleUpdate, RoleDelete, RoleCreate, ThrashTypeCreate, \
    ThrashTypeUpdate, ThrashTypeDelete, StatusCreate, StatusUpdate, StatusDelete, MapCreate, MapUpdate, MapDelete, \
    CourierCreate, UserCreate, UserGet, UserDelete, UserUpdate, CourierGet, CourierUpdate, CourierDelete, \
    MapPointCreate, MapPointGet, MapPointUpdate, MapPointDelete, AchievementCreate, AchievementUpdate, \
    AchievementDelete, PointThrashGet, DeliveryRequestGet, DeliveryRequestUpdate, DeliveryRequestDelete, \
    DeliveryRequestCreate
from db.sql_models import User, Achievement, Role, UserAchievementLink, ThrashType, Status, Map, Courier, MapPoint, \
    PointThrashLink, DeliveryRequest, DeliveryThrashLink

logger = logging.getLogger(__name__)


async def get_users(session: AsyncSession, filters: UserGet):
    try:
        sql = select(User.id, User.phone_number, User.username, User.name, User.surname, User.birthday,
                     Role.name.label("role")).outerjoin(Role)
        if filters.id_filter or filters.username_filter or filters.phone_filter:
            return await get_user(session, filters.id_filter, filters.username_filter, filters.phone_filter)
        if filters.name_filter:
            sql = sql.where(User.name == filters.name_filter)
        if filters.last_name_filter:
            sql = sql.where(User.surname == filters.last_name_filter)
        if filters.birthday_filter_from:
            sql = sql.where(User.birthday >= filters.birthday_filter_from)
        if filters.birthday_filter_to:
            sql = sql.where(User.birthday >= filters.birthday_filter_to)
        if filters.role_filter:
            role = await get_role(session, role_name_filter=filters.role_filter)
            sql = sql.where(User.role == role[0])
        res = await session.exec(sql)
        return res.all()
    except Exception as e:
        logger.error(f"get_users exception {e}")
        await session.rollback()
        return None


async def update_user(session: AsyncSession, users: List[UserUpdate]):
    updated_users = []
    for user in users:
        try:
            if user.phone_number_old:
                user_to_update = await get_user(session, phone=user.phone_number_old)
            elif user.id:
                user_to_update = await get_user(session, user_id=user.id)
            elif user.username:
                user_to_update = await get_user(session, username=user.username)
            else:
                continue
            if user.phone_number_old and user.phone_number_new:
                user_to_update.phone_number = user.phone_number_new
            if user.username and user.username_new:
                user_to_update.username = user.username_new
            if user.name:
                user_to_update.name = user.name
            if user.surname:
                user_to_update.surname = user.surname
            if user.birthday:
                user_to_update.birthday = user.birthday
            if user.role:
                role = await get_role(session, role_name_filter=user.role)
                if role:
                    user_to_update.role = role[0]
            session.add(user_to_update)
            updated_users.append(user_to_update)
        except Exception as e:
            logger.error(f"update_users exception {e}")
            await session.rollback()
            return
    await session.commit()
    return updated_users


async def delete_user(session: AsyncSession, users: List[UserDelete]):
    deleted_users = []
    for user in users:
        try:
            if not user.id and not user.username and not user.phone:
                return None
            user_to_delete = await get_user(session, user.id, user.username, user.phone)
            await session.delete(user_to_delete)
            deleted_users.append(user_to_delete)
        except Exception as e:
            logger.error(f"delete_map exception {e}")
            await session.rollback()
    await session.commit()
    return deleted_users


async def get_user(session: AsyncSession, user_id: int = None, username: str = None, phone: str = None) -> User:
    try:
        sql = select(User)
        if user_id:
            sql = sql.where(User.id == user_id)
        elif username:
            sql = sql.where(User.username == username)
        elif phone:
            sql = sql.where(User.phone_number == phone)
        else:
            return None
        res = await session.exec(sql)
        return res.one_or_none()
    except Exception as e:
        logger.error(f'get_user exception {e}')
        await session.rollback()
        return None


async def create_user_achievements(session: AsyncSession, phone_number):
    all_achievements = await get_achievements(session)
    user = await get_user(session, phone=phone_number)
    if not user:
        raise Exception
    for achievement in all_achievements:
        table = UserAchievementLink(user_id=user.id, achievement_id=achievement.id)
        session.add(table)
    await session.commit()
    await session.refresh(user)


async def get_users_achievements(session: AsyncSession, user_id: int = None):
    try:
        if not user_id:
            return
        sql = select(Achievement.id, Achievement.title, Achievement.description, UserAchievementLink.unlock_date,
                     UserAchievementLink.unlocked) \
            .join(Achievement, UserAchievementLink.achievement_id == Achievement.id) \
            .where(UserAchievementLink.user_id == user_id)
        res = await session.exec(sql)
        return res.all()
    except Exception as e:
        logger.error(f'get_users_achievements exception {e}')
        await session.rollback()
        return


async def sync_users_achievements(session: AsyncSession, user_id: int):
    synced = []
    try:
        user_ach = await get_users_achievements(session, user_id)
        all_ach = await get_achievements(session)
        logger.debug(f"sync user_ach: {user_ach}")
        ids = set([ach[0] for ach in user_ach])
        ach_ids = set([ach.id for ach in all_ach])
        missing_ids = ach_ids.difference(ids)
        if not missing_ids:
            return None
        for i in missing_ids:
            table = UserAchievementLink(user_id=user_id, achievement_id=i)
            synced.append(i)
            session.add(table)
        await session.commit()
        return f"for user with id: {user_id} updated achievements with ids: {synced}"
    except Exception as e:
        logger.debug(f"sync_users_achievements exception {e}")
        await session.rollback()


async def update_users_achievements(session: AsyncSession, update_data: List[UserAchievementUpdate]):
    updated = []
    try:
        for item in update_data:
            logger.debug(f"date passed: {item.unlock_date} {type(item.unlock_date)}")
            sql = select(UserAchievementLink).where(UserAchievementLink.user_id == item.user_id,
                                                    UserAchievementLink.achievement_id == item.achievement_id)
            res = await session.exec(sql)
            res = res.one_or_none()
            if not res:
                continue
            res.unlocked = item.unlocked
            res.unlock_date = item.unlock_date
            session.add(res)
            updated.append(res)
        await session.commit()
        return updated
    except Exception as e:
        await session.rollback()
        logger.debug(f"updating achievements exception {e}")


async def create_user(session: AsyncSession, user_data: UserCreate):
    logger.debug(f"user_data {user_data}")
    user_data = user_data.dict(exclude_unset=True, exclude_none=True)
    logger.debug(f"user_data {user_data}")
    try:
        user = User()
        if user_data.get("role"):
            role = await get_role(session, role_name_filter=user_data["role"])
            user.role = role[0]
        else:
            role = await get_role(session, role_name_filter="basic_user")
            role = role[0]
            user.role = role
        for key, value in user_data.items():
            setattr(user, key, value)

        session.add(user)
        await session.commit()
        await session.refresh(user)
        await create_user_achievements(session, user.phone_number)
        return user
    except Exception as e:
        logger.debug(f"create_user exception {e}")
        await session.rollback()
        return None


async def get_role(session: AsyncSession, role_id_filter: Optional[int] = None, role_name_filter: Optional[str] = None):
    try:
        role_select = select(Role)
        if role_name_filter:
            role_select = role_select.where(Role.name == role_name_filter)
        elif role_id_filter:
            role_select = role_select.where(Role.id == role_id_filter)
        roles = await session.exec(role_select)
        return roles.all()
    except Exception as e:
        logger.debug(f"get_role exception {e}")
        await session.rollback()
        return None


async def create_role(session: AsyncSession, roles: List[RoleCreate]):
    created_roles = []
    logger.debug(f"roles passed: {roles}")
    for role in roles:
        try:
            if await get_role(session, role_name_filter=role.name):
                return HTTPException(status_code=400, detail=f"{role.name} already exists")
            db_role = Role(name=role.name)
            session.add(db_role)
            created_roles.append(db_role)
        except Exception as e:
            logger.error(f"create_role exception {e}")
            await session.rollback()
            return
    await session.commit()
    return created_roles


async def update_role(session: AsyncSession, roles: List[RoleUpdate]):
    updated_roles = []
    for role in roles:
        try:
            selection = Role.name == role.old_name if role.old_name else Role.id == role.old_id
            role_to_update = select(Role).where(selection)
            res = await session.exec(role_to_update)
            res = res.one()
            res.name = role.new_name
            session.add(res)
            updated_roles.append(res)
        except Exception as e:
            logger.error(f"update_role exception {e}")
            await session.rollback()
            return
    await session.commit()
    return updated_roles


async def delete_role(session: AsyncSession, roles: List[RoleDelete]):
    deleted_roles = []
    for role in roles:
        try:
            if not role.name and not role.id:
                return None
            selection = Role.name == role.name if role.name else Role.id == role.id
            role_to_delete = select(Role).where(selection)
            res = await session.exec(role_to_delete)
            res = res.one()
            await session.delete(res)
            deleted_roles.append(res)
        except Exception as e:
            logger.error(f"delete_role exception {e}")
            await session.rollback()
            return
    await session.commit()
    return deleted_roles


async def get_thrash_type(session: AsyncSession,
                          thrash_type_id_filter: Optional[int] = None, thrash_type_name_filter: Optional[str] = None):
    try:
        thrash_type_select = select(ThrashType)
        if thrash_type_name_filter:
            thrash_type_select = thrash_type_select.where(ThrashType.thrash_type == thrash_type_name_filter)
        elif thrash_type_id_filter:
            thrash_type_select = thrash_type_select.where(ThrashType.id == thrash_type_id_filter)
        types = await session.exec(thrash_type_select)
        return types.all()
    except Exception as e:
        logger.debug(f"get_thrash_type exception {e}")
        await session.rollback()
        return None


async def create_thrash_type(session: AsyncSession, thrash_types: List[ThrashTypeCreate]):
    created_types = []
    logger.debug(f"thrash_types passed: {thrash_types}")
    for thrash_type in thrash_types:
        try:
            if await get_thrash_type(session, thrash_type_name_filter=thrash_type.thrash_type):
                return HTTPException(status_code=400, detail=f"{thrash_type.thrash_type} already exists")
            db_thrash_type = ThrashType(thrash_type=thrash_type.thrash_type)
            session.add(db_thrash_type)
            created_types.append(db_thrash_type)
        except Exception as e:
            logger.error(f"create_thrash_type exception {e}")
            await session.rollback()
            return
    await session.commit()
    return created_types


async def update_thrash_type(session: AsyncSession, types: List[ThrashTypeUpdate]):
    updated_types = []
    for thrash_type in types:
        try:
            selection = ThrashType.thrash_type == thrash_type.old_thrash_type \
                if thrash_type.old_thrash_type else ThrashType.id == thrash_type.old_id
            thrash_type_to_update = select(ThrashType).where(selection)
            res = await session.exec(thrash_type_to_update)
            res = res.one()
            res.thrash_type = thrash_type.new_thrash_type
            session.add(res)
            updated_types.append(res)
        except Exception as e:
            logger.error(f"update_thrash_type exception {e}")
            await session.rollback()
            return
    await session.commit()
    return updated_types


async def delete_thrash_type(session: AsyncSession, types: List[ThrashTypeDelete]):
    deleted_thrash_types = []
    for thrash_type in types:
        try:
            if not thrash_type.thrash_type and not thrash_type.id:
                return None
            selection = ThrashType.thrash_type == thrash_type.thrash_type \
                if thrash_type.thrash_type else ThrashType.id == thrash_type.id
            thrash_type_to_delete = select(ThrashType).where(selection)
            res = await session.exec(thrash_type_to_delete)
            res = res.one()
            await session.delete(res)
            deleted_thrash_types.append(res)
        except Exception as e:
            logger.error(f"delete_thrash_type exception {e}")
            await session.rollback()
            return
    await session.commit()
    return deleted_thrash_types


async def get_status(session: AsyncSession,
                     status_id_filter: Optional[int] = None, status_name_filter: Optional[str] = None):
    try:
        status_select = select(Status)
        if status_name_filter:
            status_select = status_select.where(Status.status_name == status_name_filter)
        elif status_id_filter:
            status_select = status_select.where(Status.id == status_id_filter)
        statuses = await session.exec(status_select)
        return statuses.all()
    except Exception as e:
        logger.debug(f"get_status exception {e}")
        await session.rollback()
        return None


async def create_status(session: AsyncSession, statuses: List[StatusCreate]):
    created_statuses = []
    logger.debug(f"statuses passed: {statuses}")
    for status in statuses:
        try:
            if await get_status(session, status_name_filter=status.status_name):
                return HTTPException(status_code=400, detail=f"{status.status_name} already exists")
            db_status = Status(status_name=status.status_name)
            session.add(db_status)
            created_statuses.append(db_status)
        except Exception as e:
            logger.error(f"create_status exception {e}")
            await session.rollback()
            return
    await session.commit()
    return created_statuses


async def update_status(session: AsyncSession, statuses: List[StatusUpdate]):
    updated_statuses = []
    for status in statuses:
        try:
            selection = Status.status_name == status.old_status \
                if status.old_status else Status.id == status.old_id
            status_to_update = select(Status).where(selection)
            res = await session.exec(status_to_update)
            res = res.one()
            res.status_name = status.new_status
            session.add(res)
            updated_statuses.append(res)
        except Exception as e:
            logger.error(f"update_status exception {e}")
            await session.rollback()
            return
    await session.commit()
    return updated_statuses


async def delete_status(session: AsyncSession, statuses: List[StatusDelete]):
    deleted_statuses = []
    for status in statuses:
        try:
            if not status.status_name and not status.id:
                return None
            selection = Status.status_name == status.status_name \
                if status.status_name else Status.id == status.id
            status_to_delete = select(Status).where(selection)
            res = await session.exec(status_to_delete)
            res = res.one()
            await session.delete(res)
            deleted_statuses.append(res)
        except Exception as e:
            logger.error(f"delete_status exception {e}")
            await session.rollback()
            return
    await session.commit()
    return deleted_statuses


async def get_map(session: AsyncSession,
                  map_id_filter: Optional[int] = None, map_city_filter: Optional[str] = None):
    try:
        map_select = select(Map)
        if map_city_filter:
            map_select = map_select.where(Map.city == map_city_filter)
        elif map_id_filter:
            map_select = map_select.where(Map.id == map_id_filter)
        maps = await session.exec(map_select)
        return maps.one_or_none()
    except Exception as e:
        logger.debug(f"get_map exception {e}")
        await session.rollback()
        return None


async def create_map(session: AsyncSession, maps: List[MapCreate]):
    created_maps = []
    logger.debug(f"maps passed: {maps}")
    for map in maps:
        try:
            if await get_map(session, map_city_filter=map.city):
                return HTTPException(status_code=400, detail=f"{map.city} already exists")
            db_map = Map(city=map.city)
            session.add(db_map)
            created_maps.append(db_map)
        except Exception as e:
            logger.error(f"create_map exception {e}")
            await session.rollback()
            return
    await session.commit()
    return created_maps


async def update_map(session: AsyncSession, maps: List[MapUpdate]):
    updated_maps = []
    for map in maps:
        try:
            selection = Map.city == map.old_city \
                if map.old_city else Map.id == map.old_id
            map_to_update = select(Map).where(selection)
            res = await session.exec(map_to_update)
            res = res.one()
            res.city = map.new_city
            session.add(res)
            updated_maps.append(res)
        except Exception as e:
            logger.error(f"update_map exception {e}")
            await session.rollback()
            return
    await session.commit()
    return updated_maps


async def delete_map(session: AsyncSession, maps: List[MapDelete]):
    deleted_maps = []
    for map in maps:
        try:
            if not map.city and not map.id:
                return None
            selection = Map.city == map.city \
                if map.city else Map.id == map.id
            map_to_delete = select(Map).where(selection)
            res = await session.exec(map_to_delete)
            res = res.one()
            await session.delete(res)
            deleted_maps.append(res)
        except Exception as e:
            logger.error(f"delete_map exception {e}")
            await session.rollback()
            return
    await session.commit()
    return deleted_maps


async def get_courier(session: AsyncSession, user_id: int = None, username: str = None, phone: str = None) -> Courier:
    try:
        sql = select(Courier)
        if user_id:
            sql = sql.where(Courier.id == user_id)
        elif username:
            sql = sql.where(Courier.username == username)
        elif phone:
            sql = sql.where(Courier.phone_number == phone)
        else:
            return None
        res = await session.exec(sql)
        return res.one_or_none()
    except Exception as e:
        logger.error(f"get_courier exception {e}")
        await session.rollback()
        return None


async def create_courier(session: AsyncSession, data: CourierCreate):
    data = data.dict(exclude_unset=True)
    logger.debug(f"data {data}")
    try:
        courier = Courier()
        for key, value in data.items():
            setattr(courier, key, value)
        session.add(courier)
        await session.commit()
        await session.refresh(courier)
        return courier
    except Exception as e:
        await session.rollback()
        logger.debug(f"create_courier exception {e}")
        return None


async def get_couriers(session: AsyncSession, filters: CourierGet):
    try:
        sql = select(Courier)
        if filters.id_filter or filters.username_filter or filters.phone_filter:
            return await get_courier(session, filters.id_filter, filters.username_filter, filters.phone_filter)
        if filters.name_filter:
            sql = sql.where(Courier.name == filters.name_filter)
        if filters.last_name_filter:
            sql = sql.where(Courier.surname == filters.last_name_filter)
        if filters.delivery_count_from:
            sql = sql.where(Courier.delivery_count >= filters.delivery_count_from)
        if filters.delivery_count_to:
            sql = sql.where(Courier.delivery_count >= filters.delivery_count_to)
        if filters.salary_from:
            sql = sql.where(Courier.salary >= filters.salary_from)
        if filters.salary_to:
            sql = sql.where(Courier.salary <= filters.salary_to)
        if filters.birthday_from:
            sql = sql.where(Courier.birthday >= filters.birthday_from)
        if filters.birthday_to:
            sql = sql.where(Courier.birthday <= filters.birthday_to)
        res = await session.exec(sql)
        return res.all()
    except Exception as e:
        logger.error(f"get_couriers exception {e}")
        await session.rollback()
        return None


async def update_couriers(session: AsyncSession, couriers: List[CourierUpdate]):
    updated_couriers = []
    for courier in couriers:
        try:
            if not courier.phone_number and not courier.username:
                continue
            courier_to_update = await get_courier(session, phone=courier.phone_number)
            if not courier_to_update:
                courier_to_update = await get_courier(session, username=courier.username)
                if not courier_to_update:
                    continue
            if courier.phone_number:
                courier_to_update.phone_number = courier.phone_number
            if courier.username:
                courier_to_update.username = courier.username
            if courier.name:
                courier_to_update.name = courier.name
            if courier.surname:
                courier_to_update.surname = courier.surname
            if courier.birthday:
                courier_to_update.birthday = courier.birthday
            if courier.salary:
                courier_to_update.salary = courier.salary
            if courier.delivery_count:
                courier_to_update.delivery_count = courier.delivery_count
            session.add(courier_to_update)
            updated_couriers.append(courier_to_update)
        except Exception as e:
            logger.error(f"update_couriers exception {e}")
            await session.rollback()
            return
    await session.commit()
    return updated_couriers


async def delete_courier(session: AsyncSession, couriers: List[CourierDelete]):
    deleted_couriers = []
    for courier in couriers:
        try:
            if not courier.id and not courier.phone:
                return None
            courier_to_delete = await get_courier(session, user_id=courier.id, phone=courier.phone)
            await session.delete(courier_to_delete)
            deleted_couriers.append(courier_to_delete)
        except Exception as e:
            logger.error(f"delete_courier exception {e}")
            await session.rollback()
            return
    await session.commit()
    return deleted_couriers


async def get_map_point(session: AsyncSession, point_id: int = None) -> MapPoint:
    try:
        sql = select(MapPoint)
        if point_id:
            sql = sql.where(MapPoint.id == point_id)
        else:
            return None
        res = await session.exec(sql)
        return res.one_or_none()
    except Exception as e:
        logger.error(f"get_map_point exception {e}")
        await session.rollback()


async def create_map_point(session: AsyncSession, data: MapPointCreate):
    data = data.dict(exclude_unset=True, exclude_none=True)
    logger.debug(f"data {data}")
    try:
        map_point = MapPoint()
        for key, value in data.items():
            if key == "city":
                city_map = await get_map(session, map_city_filter=value)
                if city_map:
                    map_point.map = city_map
                continue
            if key == "accepted_thrash":
                thrash_list = []
                for item in value:
                    thrash = await get_thrash_type(session, thrash_type_name_filter=item)
                    if thrash:
                        thrash_list.append(thrash[0])
                map_point.accepted_thrash = thrash_list
                continue

            setattr(map_point, key, value)
        session.add(map_point)
        await session.commit()
        await session.refresh(map_point)
        return map_point
    except Exception as e:
        await session.rollback()
        logger.debug(f"create_map_point exception {e}")
        return None


async def get_map_points(session: AsyncSession, filters: MapPointGet):
    try:
        sql = select(MapPoint)
        if filters.id_filter:
            sql = sql.where(MapPoint.id == filters.id_filter)
            res = await session.exec(sql)
            return res.one_or_none()
        if filters.phone_filter:
            sql = sql.where(MapPoint.phone_number == filters.phone_filter)
        if filters.email_filter:
            sql = sql.where(MapPoint.email == filters.email_filter)
        if filters.title_filter:
            sql = sql.where(MapPoint.title == filters.title_filter)
        if filters.website_filter:
            sql = sql.where(MapPoint.website == filters.website_filter)
        if filters.address_filter:
            sql = sql.where(MapPoint.address == filters.address_filter)
        if filters.coordinates_filter:
            sql = sql.where(MapPoint.coordinates == filters.coordinates_filter)
        if filters.city_map_filter:
            city_map = await get_map(session, map_city_filter=filters.city_map_filter)
            if city_map:
                sql = sql.where(MapPoint.map == city_map)
        res = await session.exec(sql)
        return res.all()
    except Exception as e:
        await session.rollback()
        logger.error(f"get_map_points exception {e}")
        return None


async def update_map_points(session: AsyncSession, map_points: List[MapPointUpdate]):
    updated_points = []
    for map_point in map_points:
        try:
            if not map_point.id:
                continue
            point_to_update = await get_map_point(session, map_point.id)
            if not point_to_update:
                continue
            if map_point.phone_number:
                point_to_update.phone_number = map_point.phone_number
            if map_point.title:
                point_to_update.title = map_point.title
            if map_point.description:
                point_to_update.description = map_point.description
            if map_point.address:
                point_to_update.address = map_point.address
            if map_point.website:
                point_to_update.website = map_point.website
            if map_point.email:
                point_to_update.email = map_point.email
            if map_point.coordinates:
                point_to_update.coordinates = map_point.coordinates
            if map_point.city:
                map = await get_map(session, map_city_filter=map_point.city)
                if map:
                    point_to_update.map = map
            if map_point.accepted_thrash:
                thrash_list = []
                for item in map_point.accepted_thrash:
                    thrash = await get_thrash_type(session, thrash_type_name_filter=item)
                    if thrash:
                        thrash_list.append(thrash[0])
                map_point.accepted_thrash = thrash_list
            session.add(point_to_update)
            updated_points.append(point_to_update)
        except Exception as e:
            await session.rollback()
            logger.error(f"update_map_points exception {e}")
            return
    await session.commit()
    return updated_points


async def delete_map_points(session: AsyncSession, map_points: List[MapPointDelete]):
    deleted_points = []
    for map_point in map_points:
        try:
            if not map_point.id:
                return None
            point_to_delete = await get_map_point(session, point_id=map_point.id)
            await session.delete(point_to_delete)
            deleted_points.append(point_to_delete)
        except Exception as e:
            await session.rollback()
            logger.error(f"delete_map_points exception {e}")
            return
    await session.commit()
    return deleted_points


async def get_achievements(session: AsyncSession,
                           id_filter: Optional[int] = None, title_filter: Optional[str] = None):
    try:
        sql = select(Achievement)
        if id_filter:
            sql = sql.where(Achievement.id == id_filter)
        elif title_filter:
            sql = sql.where(Achievement.title == title_filter)

        achievements = await session.exec(sql)
        return achievements.all()
    except Exception as e:
        await session.rollback()
        logger.debug(f"get_achievement exception {e}")
        return


async def create_achievements(session: AsyncSession, achievements: List[AchievementCreate]):
    created = []
    for achievement in achievements:
        try:
            ach_exists = await get_achievements(session, title_filter=achievement.title)
            if ach_exists is not None and len(ach_exists) > 0:
                return HTTPException(status_code=400, detail=f"{achievement.title} already exists")
            achievement_to_create = Achievement()
            achievement_to_create.title = achievement.title
            achievement_to_create.description = achievement.description
            session.add(achievement_to_create)
            created.append(achievement_to_create)
        except Exception as e:
            await session.rollback()
            logger.error(f"create_achievement exception {e}")
    await session.commit()
    try:
        users = await get_users(session, filters=UserGet())
        for user in users:
            await sync_users_achievements(session, user_id=user.id)
    except Exception as e:
        await session.rollback()
        logger.debug(f"error when updating users achievements {e}")
        return
    return created


async def update_achievements(session: AsyncSession, achievements: List[AchievementUpdate]):
    updated = []
    for achievement in achievements:
        try:
            selection = Achievement.title == achievement.old_title \
                if achievement.old_title else Achievement.id == achievement.id
            map_to_update = select(Achievement).where(selection)
            res = await session.exec(map_to_update)
            res = res.one_or_none()
            if not res:
                continue
            if achievement.new_title:
                res.title = achievement.new_title
            res.description = achievement.description
            session.add(res)
            updated.append(res)
        except Exception as e:
            logger.error(f"update_achievement exception {e}")
            await session.rollback()
            continue
    await session.commit()
    return updated


async def delete_achievements(session: AsyncSession, achievements: List[AchievementDelete]):
    deleted_achievements = []
    for achievement in achievements:
        try:
            if not achievement.title and not achievement.id:
                continue
            selection = Achievement.title == achievement.title \
                if achievement.title else Achievement.id == achievement.id
            map_to_delete = select(Achievement).where(selection)
            res = await session.exec(map_to_delete)
            res = res.one_or_none()
            if not res:
                continue
            await session.delete(res)
            deleted_achievements.append(res)
        except Exception as e:
            logger.error(f"delete_achievement exception {e}")
    await session.commit()
    return deleted_achievements


async def get_point_thrash(session: AsyncSession, filters: PointThrashGet):
    try:
        sql = select(ThrashType.thrash_type, MapPoint.title, Map.city, MapPoint.email,
                     MapPoint.address, MapPoint.phone_number, MapPoint.website, MapPoint.description,
                     MapPoint.coordinates) \
            .outerjoin_from(MapPoint, PointThrashLink).outerjoin(ThrashType).outerjoin(Map)

        if filters.point_id_filter:
            sql = sql.where(MapPoint.id == filters.point_id_filter)
        if filters.thrash_type_filter:
            sql = sql.where(ThrashType.thrash_type == filters.thrash_type_filter)
        if filters.title_filter:
            sql = sql.where(MapPoint.title == filters.title_filter)
        if filters.phone_number_filter:
            sql = sql.where(MapPoint.phone_number == filters.phone_number_filter)
        if filters.email_filter:
            sql = sql.where(MapPoint.email == filters.email_filter)
        if filters.address_filter:
            sql = sql.where(MapPoint.address == filters.address_filter)
        if filters.coordinates_filter:
            sql = sql.where(MapPoint.coordinates == filters.coordinates_filter)
        if filters.website_filter:
            sql = sql.where(MapPoint.website == filters.website_filter)
        if filters.city_filter:
            sql = sql.where(Map.city == filters.city_filter)

        res = await session.exec(sql)
        return res.all()
    except Exception as e:
        await session.rollback()
        logger.error(f"get_point_thrash exception {e}")


async def get_delivery_requests(session: AsyncSession, filters: DeliveryRequestGet):
    try:
        sql = select(DeliveryRequest.id,
                     DeliveryRequest.address.label("delivery_address"),
                     DeliveryRequest.create_date,
                     DeliveryRequest.price,

                     ThrashType.thrash_type,

                     Status.status_name.label("status"),

                     Courier.name.label("courier_name"),
                     Courier.surname.label("courier_surname"),
                     Courier.phone_number.label("courier_phone_number"),

                     User.name.label("user_name"),
                     User.surname.label("user_surname"),
                     User.phone_number.label("user_phone_number"),
                     User.username.label("user_username")) \
            .outerjoin_from(DeliveryRequest, DeliveryThrashLink) \
            .outerjoin(ThrashType).outerjoin(Courier).outerjoin(Status).outerjoin(User)

        if filters.id_filter:
            sql = sql.where(DeliveryRequest.id == filters.id_filter)
        if filters.create_date_from:
            sql = sql.where(DeliveryRequest.create_date >= filters.create_date_from)
        if filters.create_date_to:
            sql = sql.where(DeliveryRequest.create_date <= filters.create_date_to)

        if filters.thrash_type_filter:
            sql = sql.where(ThrashType.thrash_type == filters.thrash_type_filter)
        if filters.status_filter:
            sql = sql.where(Status.status_name == filters.status_filter)

        if filters.courier_name_filter:
            sql = sql.where(Courier.name == filters.courier_name_filter)
        if filters.courier_surname_filter:
            sql = sql.where(Courier.surname == filters.courier_surname_filter)
        if filters.courier_phone_number_filter:
            sql = sql.where(Courier.phone_number == filters.courier_phone_number_filter)

        if filters.user_name_filter:
            sql = sql.where(User.name == filters.user_name_filter)
        if filters.user_surname_filter:
            sql = sql.where(User.surname == filters.user_surname_filter)
        if filters.user_username_filter:
            sql = sql.where(User.username == filters.user_username_filter)
        if filters.user_phone_number_filter:
            sql = sql.where(User.phone_number == filters.user_phone_number_filter)

        res = await session.exec(sql)
        return res.all()
    except Exception as e:
        await session.rollback()
        logger.error(f"get_delivery_request exception {e}")


async def update_delivery_requests(session: AsyncSession, del_requests: List[DeliveryRequestUpdate]):
    updated_requests = []
    for req in del_requests:
        try:
            if not req.id_req:
                continue
            req_to_update = select(DeliveryRequest).where(DeliveryRequest.id == req.id_req)
            req_to_update = await session.exec(req_to_update)
            req_to_update = req_to_update.one()
            if not req_to_update:
                continue
            if req.address:
                req_to_update.address = req.address
            if req.create_date:
                req_to_update.create_date = req.create_date
            if req.status:
                status = await get_status(session, status_name_filter=req.status)
                if status:
                    req_to_update.status = status[0]
            if req.courier_phone:
                courier = await get_courier(session, phone=req.courier_phone)
                if courier:
                    req_to_update.req_courier = courier
            if req.user_phone:
                user = await get_user(session, phone=req.user_phone)
                if user:
                    req_to_update.req_user = user
            if req.price is not None:
                req_to_update.price = req.price

            session.add(req_to_update)
            updated_requests.append(req_to_update)
        except Exception as e:
            await session.rollback()
            logger.error(f"update_delivery_requests exception {e}")
            return
    await session.commit()
    return updated_requests


async def delete_delivery_requests(session: AsyncSession, requests: List[DeliveryRequestDelete]):
    deleted_requests = []
    for req in requests:
        try:
            if not req.req_id:
                continue
            sql = select(DeliveryRequest).where(DeliveryRequest.id == req.req_id)
            res = await session.exec(sql)
            res = res.one_or_none()
            if not res:
                continue
            await session.delete(res)
            deleted_requests.append(res)
        except Exception as e:
            await session.rollback()
            logger.error(f"delete_delivery_requests exception {e}")
    await session.commit()
    return deleted_requests


async def create_delivery_request(session: AsyncSession, request: DeliveryRequestCreate):
    try:
        user = await get_user(session, phone=request.user_phone)
        courier = await get_courier(session, phone=request.courier_phone)
        if not user and not courier:
            return None
        request_to_create = DeliveryRequest()
        request_to_create.req_user = user
        request_to_create.req_courier = courier
        request_to_create.create_date = request.create_date
        request_to_create.address = request.address
        request_to_create.price = request.price
        request_status = await get_status(session, status_name_filter="в ожидании")
        if request_status is not None:
            request_to_create.status = request_status[0]
        for thrash_type in request.thrash_types:
            thrash_obj = await get_thrash_type(session, thrash_type_name_filter=thrash_type)
            if thrash_obj is not None:
                request_to_create.thrash_types.append(thrash_obj[0])
        session.add(request_to_create)
        await session.commit()
        await session.refresh(request_to_create)
        return request_to_create
    except Exception as e:
        await session.rollback()
        logger.error(f"create_delivery_request exception {e}")
