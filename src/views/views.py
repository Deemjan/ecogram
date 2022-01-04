import logging
from typing import List, Optional

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

import db.crud as crud
from db.base_models import UserAchievementUpdate, RoleUpdate, RoleCreate, RoleDelete, ThrashTypeCreate, \
    ThrashTypeUpdate, ThrashTypeDelete, StatusCreate, StatusUpdate, StatusDelete, MapCreate, MapUpdate, MapDelete, \
    CourierCreate, UserGet, UserDelete, UserUpdate, CourierGet, CourierDelete, CourierUpdate, MapPointCreate, \
    MapPointGet, MapPointDelete, MapPointUpdate, AchievementCreate, AchievementUpdate, PointThrashGet, \
    DeliveryRequestGet, DeliveryRequestDelete, DeliveryRequestUpdate, DeliveryRequestCreate
from db.dispatcher import get_session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/healthcheck")
async def healthcheck(request: Request):
    logger.debug(f"request from {request.base_url}")
    return {"status": "ok"}


@router.post("/role/create")
async def create_role(roles: List[RoleCreate], db: AsyncSession = Depends(get_session)):
    roles = await crud.create_role(db, roles)
    if roles is not None:
        return {"created": roles}
    raise HTTPException(status_code=400, detail="Couldn't create role")


@router.post("/role/update")
async def update_role(roles: List[RoleUpdate], db: AsyncSession = Depends(get_session)):
    roles = await crud.update_role(db, roles)
    if roles is not None:
        return {"updated": roles}
    raise HTTPException(status_code=400, detail="Couldn't update role")


@router.post("/role/delete")
async def delete_role(roles: List[RoleDelete], db: AsyncSession = Depends(get_session)):
    roles = await crud.delete_role(db, roles)
    if roles is not None:
        return {"deleted": roles}
    raise HTTPException(status_code=400, detail="Couldn't delete role")


@router.get("/roles")
async def get_role(db: AsyncSession = Depends(get_session), role_id: Optional[int] = None,
                   role_name: Optional[str] = None):
    roles = await crud.get_role(db, role_id_filter=role_id, role_name_filter=role_name)
    if roles is not None:
        return {"roles": roles}
    raise HTTPException(status_code=400, detail="Bad request")


@router.post("/thrash_type/create")
async def create_thrash_type(thrash_types: List[ThrashTypeCreate], db: AsyncSession = Depends(get_session)):
    thrash_types = await crud.create_thrash_type(db, thrash_types)
    if thrash_types is not None:
        return {"created": thrash_types}
    raise HTTPException(status_code=400, detail="Couldn't create thrash_type")


@router.post("/thrash_type/update")
async def update_thrash_type(thrash_types: List[ThrashTypeUpdate], db: AsyncSession = Depends(get_session)):
    thrash_types = await crud.update_thrash_type(db, thrash_types)
    if thrash_types is not None:
        return {"updated": thrash_types}
    raise HTTPException(status_code=400, detail="Couldn't update thrash_type")


@router.post("/thrash_type/delete")
async def delete_thrash_type(thrash_types: List[ThrashTypeDelete], db: AsyncSession = Depends(get_session)):
    thrash_types = await crud.delete_thrash_type(db, thrash_types)
    if thrash_types is not None:
        return {"deleted": thrash_types}
    raise HTTPException(status_code=400, detail="Couldn't delete thrash_type")


@router.get("/thrash_types")
async def get_thrash_type(db: AsyncSession = Depends(get_session), thrash_type_id: Optional[int] = None,
                          thrash_type_name: Optional[str] = None):
    thrash_types = await crud.get_thrash_type(db, thrash_type_id_filter=thrash_type_id,
                                              thrash_type_name_filter=thrash_type_name)
    if thrash_types is not None:
        return {"thrash_types": thrash_types}
    raise HTTPException(status_code=400, detail="Bad request")


@router.post("/status/create")
async def create_status(statuses: List[StatusCreate], db: AsyncSession = Depends(get_session)):
    created = await crud.create_status(db, statuses)
    if created is not None:
        return {"created": created}
    raise HTTPException(status_code=400, detail="Couldn't create status")


@router.post("/status/update")
async def update_status(statuses: List[StatusUpdate], db: AsyncSession = Depends(get_session)):
    updated = await crud.update_status(db, statuses)
    if updated is not None:
        return {"updated": updated}
    raise HTTPException(status_code=400, detail="Couldn't update status")


@router.post("/status/delete")
async def delete_status(statuses: List[StatusDelete], db: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_status(db, statuses)
    if deleted is not None:
        return {"deleted": deleted}
    raise HTTPException(status_code=400, detail="Couldn't delete status")


@router.get("/statuses")
async def get_status(db: AsyncSession = Depends(get_session), status_id: Optional[int] = None,
                     status_name: Optional[str] = None):
    statuses = await crud.get_status(db, status_id_filter=status_id,
                                     status_name_filter=status_name)
    if statuses is not None:
        return {"statuses": statuses}
    raise HTTPException(status_code=400, detail="Bad request")


@router.post("/map/create")
async def create_map(maps: List[MapCreate], db: AsyncSession = Depends(get_session)):
    created = await crud.create_map(db, maps)
    if created is not None:
        return {"created": created}
    raise HTTPException(status_code=400, detail="Couldn't create map")


@router.post("/map/update")
async def update_map(maps: List[MapUpdate], db: AsyncSession = Depends(get_session)):
    updated = await crud.update_map(db, maps)
    if updated is not None:
        return {"updated": updated}
    raise HTTPException(status_code=400, detail="Couldn't update map")


@router.post("/map/delete")
async def delete_map(maps: List[MapDelete], db: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_map(db, maps)
    if deleted is not None:
        return {"deleted": deleted}
    raise HTTPException(status_code=400, detail="Couldn't delete map")


@router.get("/maps")
async def get_map(db: AsyncSession = Depends(get_session), map_id: Optional[int] = None,
                  map_city: Optional[str] = None):
    maps = await crud.get_map(db, map_id_filter=map_id,
                              map_city_filter=map_city)
    if maps is not None:
        return {"statuses": maps}
    raise HTTPException(status_code=400, detail="Bad request")


@router.get("/user/achievements/sync")
async def user_achievements_sync(user_id: int, session: AsyncSession = Depends(get_session)):
    synced = await crud.sync_users_achievements(session, user_id)
    if synced:
        return {"message": "Sync was successful"}
    return {"message": "No new achievements for that user"}


@router.get("/user/achievements")
async def user_achievements(user_id: int, session: AsyncSession = Depends(get_session)):
    query = await crud.get_users_achievements(session, user_id)
    return query


@router.post("/user/achievements/update")
async def user_achievement_update(update_data: List[UserAchievementUpdate],
                                  session: AsyncSession = Depends(get_session)):
    query = await crud.update_users_achievements(session, update_data)
    if query:
        return JSONResponse(status_code=200, content="updated")
    raise HTTPException(status_code=400, detail="something went wrong")


@router.post("/courier/create")
async def courier_create(update_data: CourierCreate,
                         session: AsyncSession = Depends(get_session)):
    query = await crud.create_courier(session, update_data)
    if query:
        return JSONResponse(status_code=201, content={"created": query})
    raise HTTPException(status_code=400, detail="something went wrong")


@router.get("/couriers")
async def couriers_get(filters: CourierGet = Depends(),
                       session: AsyncSession = Depends(get_session)):
    query = await crud.get_couriers(session, filters)
    if query is None:
        raise HTTPException(status_code=400, detail="something went wrong")
    return query


@router.post("/couriers/delete")
async def delete_couriers(couriers: List[CourierDelete], db: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_courier(db, couriers)
    if deleted is not None:
        return {"deleted": deleted}
    raise HTTPException(status_code=400, detail="Couldn't delete couriers")


@router.post("/couriers/update")
async def update_couriers(couriers: List[CourierUpdate], db: AsyncSession = Depends(get_session)):
    updated = await crud.update_couriers(db, couriers)
    if updated is not None:
        return {"updated": updated}
    raise HTTPException(status_code=400, detail="Couldn't update couriers")


@router.get("/users")
async def users_get(filters: UserGet = Depends(),
                    session: AsyncSession = Depends(get_session)):
    query = await crud.get_users(session, filters)
    if query is None:
        raise HTTPException(status_code=400, detail="something went wrong")
    return query


@router.post("/users/delete")
async def delete_users(users: List[UserDelete], db: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_user(db, users)
    if deleted is not None:
        return {"deleted": deleted}
    raise HTTPException(status_code=400, detail="Couldn't delete users")


@router.post("/users/update")
async def update_users(users: List[UserUpdate], db: AsyncSession = Depends(get_session)):
    updated = await crud.update_user(db, users)
    if updated is not None:
        return {"updated": updated}
    raise HTTPException(status_code=400, detail="Couldn't update users")


@router.post("/map/point/create")
async def map_point_create(update_data: MapPointCreate,
                           session: AsyncSession = Depends(get_session)):
    query = await crud.create_map_point(session, update_data)
    if query:
        return JSONResponse(status_code=201, content={"created": query})
    raise HTTPException(status_code=400, detail="something went wrong")


@router.post("/map/points")
async def map_points_get(filters: MapPointGet,
                         session: AsyncSession = Depends(get_session)):
    query = await crud.get_map_points(session, filters)
    if query is None:
        raise HTTPException(status_code=400, detail="something went wrong")
    return query


@router.post("/map/points/delete")
async def delete_map_points(map_points: List[MapPointDelete], db: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_map_points(db, map_points)
    if deleted is not None:
        return {"deleted": deleted}
    raise HTTPException(status_code=400, detail="Couldn't delete points")


@router.post("/map/points/update")
async def update_map_points(map_points: List[MapPointUpdate], db: AsyncSession = Depends(get_session)):
    updated = await crud.update_map_points(db, map_points)
    if updated is not None:
        return {"updated": updated}
    raise HTTPException(status_code=400, detail="Couldn't update points")


@router.get("/achievements")
async def achievements_get(session: AsyncSession = Depends(get_session), id: Optional[int] = None,
                           title: Optional[str] = None):
    query = await crud.get_achievements(session, id_filter=id, title_filter=title)
    if query is not None:
        return query
    raise HTTPException(status_code=400, detail="Bad request")


@router.post("/achievements/create")
async def achievements_create(achievements: List[AchievementCreate], session: AsyncSession = Depends(get_session)):
    created = await crud.create_achievements(session, achievements)
    if created is not None:
        return {"created": created}
    raise HTTPException(status_code=400, detail="Couldn't create achievements")


@router.post("/achievements/update")
async def achievements_update(achievements: List[AchievementUpdate], session: AsyncSession = Depends(get_session)):
    updated = await crud.update_achievements(session, achievements)
    if updated is not None:
        return {"updated": updated}
    raise HTTPException(status_code=400, detail="Couldn't update achievements")


@router.get("/achievements/delete")
async def achievements_delete(achievements: List[AchievementUpdate], session: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_achievements(session, achievements)
    if deleted is not None:
        return {"deleted": deleted}
    raise HTTPException(status_code=400, detail="Couldn't delete achievements")


@router.post("/map/points/thrash")
async def get_point_thrash(filters: PointThrashGet, session: AsyncSession = Depends(get_session)):
    sql = await crud.get_point_thrash(session, filters)
    if sql is not None:
        return sql
    raise HTTPException(status_code=400, detail="Bad request")


@router.post("/delivery/requests")
async def get_delivery_request(filters: DeliveryRequestGet, session: AsyncSession = Depends(get_session)):
    sql = await crud.get_delivery_requests(session, filters)
    if sql is not None:
        return sql
    raise HTTPException(status_code=400, detail="Bad request")


@router.post("/delivery/requests/create")
async def delivery_request_create(data: DeliveryRequestCreate,
                                  session: AsyncSession = Depends(get_session)):
    query = await crud.create_delivery_request(session, data)
    if query:
        query = query.dict()
        query['create_date'] = query['create_date'].strftime('%d-%m-%Y')
        return JSONResponse(status_code=201, content={"created": query})
    raise HTTPException(status_code=400, detail="something went wrong")


@router.post("/delivery/requests/delete")
async def delete_delivery_request(delete_data: List[DeliveryRequestDelete], db: AsyncSession = Depends(get_session)):
    deleted = await crud.delete_delivery_requests(db, delete_data)
    if deleted is not None:
        return {"deleted": deleted}
    raise HTTPException(status_code=400, detail="Couldn't delete delivery requests")


@router.post("/delivery/requests/update")
async def update_delivery_request(update_data: List[DeliveryRequestUpdate], db: AsyncSession = Depends(get_session)):
    updated = await crud.update_delivery_requests(db, update_data)
    if updated is not None:
        return {"updated": updated}
    raise HTTPException(status_code=400, detail="Couldn't update delivery requests")


# @router.get("/test")
# async def test_auth(user=Depends(get_current_user)):
#     return {"user": user}
