from sqlalchemy import Result, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Bet


async def get_bet_by_id(event_id: int, telegram_id: int, db_session: AsyncSession) -> Bet | None:
    query = select(Bet).filter(Bet.event_id == event_id, Bet.user_telegram_id == telegram_id)
    result: Result = await db_session.execute(query)
    return result.scalar()
