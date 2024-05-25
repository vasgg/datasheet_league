from sqlalchemy.ext.asyncio import AsyncEngine

from config import settings
from database.database_connector import DatabaseConnector
from database.models import Base


async def create_or_drop_db(engine: AsyncEngine, create: bool = True):
    async with engine.begin() as conn:
        if create:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        else:
            await conn.run_sync(Base.metadata.drop_all)


def get_db() -> DatabaseConnector:
    return DatabaseConnector(url=settings.aiosqlite_db_url, echo=settings.db_echo)


if __name__ == '__main__':
    import asyncio

    db = get_db()
    asyncio.run(create_or_drop_db(db.engine))
