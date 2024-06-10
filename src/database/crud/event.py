from sqlalchemy import Result, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from calc.odds_convertor import convert_us_to_dec, convert_dec_to_us
from database.crud.bet import get_bets_by_event_id
from database.models import Bet, Event
from enums import BetStatus


async def get_event_by_id(event_id: int, db_session: AsyncSession) -> Event:
    query = select(Event).filter(Event.id == event_id)
    result: Result = await db_session.execute(query)
    return result.scalar()


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


async def get_average_weighted_odds_by_event_id(event_id: int, db_session: AsyncSession) -> float:
    event = await get_event_by_id(event_id, db_session)
    bets = await get_bets_by_event_id(event_id, db_session)
    summ = 0
    total_risk = 0

    for bet in bets:
        summ += convert_us_to_dec([bet.odds])[0] * bet.risk_amount
        total_risk += bet.risk_amount
    average_weighted_odds = summ / total_risk if total_risk != 0 else 0
    return convert_dec_to_us([average_weighted_odds])[0]


async def count_events(db_session: AsyncSession) -> int:
    query = select(func.count(Event.id))
    result: Result = await db_session.execute(query)
    return result.scalar()
