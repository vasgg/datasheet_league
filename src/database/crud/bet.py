from sqlalchemy import Result, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import Bet


async def get_bet_by_id(bet_id: int, db_session: AsyncSession) -> Bet | None:
    query = select(Bet).filter(Bet.id == bet_id)
    result: Result = await db_session.execute(query)
    return result.scalar()
