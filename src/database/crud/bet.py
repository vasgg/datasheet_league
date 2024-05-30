from sqlalchemy import Result, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Bet
from enums import BetStatus


async def get_bet_by_id(event_id: int, telegram_id: int, db_session: AsyncSession) -> Bet | None:
    query = select(Bet).filter(Bet.event_id == event_id,
                               Bet.user_telegram_id == telegram_id)
    result: Result = await db_session.execute(query)
    return result.scalar()


async def count_bets_from_user(telegram_id: int, db_session: AsyncSession) -> int:
    query = select(func.count(Bet.id)).filter(Bet.user_telegram_id == telegram_id,
                                              Bet.status == BetStatus.FILLED)
    result: Result = await db_session.execute(query)
    return result.scalar()


async def get_bets_by_event_id(event_id: int, db_session: AsyncSession) -> list[Bet]:
    query = select(Bet).filter(Bet.event_id == event_id,
                               Bet.status == BetStatus.FILLED)
    result: Result = await db_session.execute(query)
    return list(result.scalars().all())
