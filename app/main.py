from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import settings
from app.db import create_snowpark_session, init_snowflake, seed_data
from app.routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.testing:
        sf = create_snowpark_session(settings)

        app.state.sf = sf
        app.state.env = settings.env

        init_snowflake(sf, settings)
        seed_data(sf, settings.env)

    yield

    sf = getattr(app.state, "sf", None)
    if sf:
        sf.close()


app = FastAPI(title="Snowflake Clinic API", lifespan=lifespan)
app.include_router(router)