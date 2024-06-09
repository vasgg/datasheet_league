from sqlalchemy import Result, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Bet
from enums import BetStatus


async def get_user_bets_by_event_id(event_id: int, telegram_id: int, db_session: AsyncSession) -> list[Bet]:
    query = select(Bet).filter(Bet.event_id == event_id,
                               Bet.user_telegram_id == telegram_id)
    result: Result = await db_session.execute(query)
    return list(result.scalars().all())


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


async def get_last_bet_by_user_id(telegram_id: int, db_session: AsyncSession) -> Bet:
    query = select(Bet).filter(Bet.user_telegram_id == telegram_id,
                               Bet.status == BetStatus.FILLED).order_by(desc(Bet.created_at)).limit(1)
    result: Result = await db_session.execute(query)
    return result.scalar()


async def withdraw_bet(bet_id: int, db_session: AsyncSession) -> None:
    query = update(Bet).filter(Bet.id == bet_id).values(status=BetStatus.INVITED)
    await db_session.execute(query)
    await db_session.flush()


def calculate_weighted_odds(bets: list[Bet]):
    decimal_odds = []
    weights = []
    for bet in bets:
        decimal_odds.append(american_to_decimal(bet.odds))
        weights.append(bet.risk_amount)

    weighted_decimal_odds = sum(odds * weight for odds, weight in zip(decimal_odds, weights)) / sum(weights)
    weighted_american_odds = decimal_to_american(weighted_decimal_odds)
    return weighted_american_odds


def american_to_decimal(odds):
    if odds > 0:
        return 1 + odds / 100
    else:
        return 1 - 100 / odds


def decimal_to_american(odds):
    if odds >= 2:
        return (odds - 1) * 100
    else:
        return -100 / (odds - 1)
