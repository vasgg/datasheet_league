from sqlalchemy import Result, desc, func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Bet, Event, GroupTable
from enums import BetStatus


async def has_group_with_name(group_name: str, user_id: int, db_session: AsyncSession) -> bool:
    query = select(GroupTable).filter(GroupTable.group_name == group_name).filter(
        GroupTable.user_telegram_id == user_id)
    result: Result = await db_session.execute(query)
    return result.scalar() is not None


async def get_groups_for_user(user_id: int, db_session: AsyncSession) -> list[GroupTable]:
    query = select(GroupTable).filter(GroupTable.user_telegram_id == user_id)
    result: Result = await db_session.execute(query)
    return list(result.scalars().all())


async def delete_group_by_name(group_name: str, user_id: int, db_session: AsyncSession) -> bool:
    query = delete(GroupTable).filter(GroupTable.group_name == group_name).filter(
        GroupTable.user_telegram_id == user_id)
    result = await db_session.execute(query)
    return result.rowcount > 0


async def get_group_by_id(group_id: int, db_session: AsyncSession) -> GroupTable:
    query = select(GroupTable).filter(GroupTable.id == group_id)
    result: Result = await db_session.execute(query)
    return result.scalar_one()


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
