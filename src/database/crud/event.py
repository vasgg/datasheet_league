from sqlalchemy import Result, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Bet, Event
from enums import BetStatus


async def get_event_by_id(event_id: int, db_session: AsyncSession) -> Event:
    query = select(Event).filter(Event.id == event_id)
    result: Result = await db_session.execute(query)
    return result.scalar()


async def get_all_event_ids(db_session: AsyncSession) -> list[int]:
    query = select(Event.id)
    result: Result = await db_session.execute(query)
    return list(result.scalars().all())


async def get_last_event(db_session: AsyncSession) -> Event:
    query = select(Event).order_by(desc(Event.created_at)).limit(1)
    result: Result = await db_session.execute(query)
    return result.scalar()


async def get_active_events(telegram_id: int, db_session: AsyncSession) -> list[Event]:
    query = select(Bet.event_id).filter(Bet.user_telegram_id == telegram_id)
    result: Result = await db_session.execute(query)
    event_ids = result.scalars().all()
    query = select(Event).filter(Event.id.in_(event_ids))
    result: Result = await db_session.execute(query)
    return list(result.scalars().all())


async def get_total_risk_by_event_id(event_id: int, db_session: AsyncSession) -> int:
    query = select(Bet.risk_amount).filter(Bet.event_id == event_id,
                                           Bet.status == BetStatus.FILLED)
    result: Result = await db_session.execute(query)
    return sum(list(result.scalars().all()))


async def count_events(db_session: AsyncSession) -> int:
    query = select(func.count(Event.id))
    result: Result = await db_session.execute(query)
    return result.scalar()
