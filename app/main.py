import uvicorn
from fastapi import FastAPI
from src.views.views import router
from src.views.auth_views import auth_router
from db.dispatcher import database
app = FastAPI()

app.include_router(router)
app.include_router(auth_router)


# @app.on_event("startup")
# async def on_startup():
#     if not database.is_connected:
#         await database.connect()
#
#
# @app.on_event("shutdown")
# async def on_startup():
#     if database.is_connected:
#         await database.disconnect()

if __name__ == "__main__":
    uvicorn.run(app)
