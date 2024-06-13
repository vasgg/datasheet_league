import pytest

from calc.average_weighted_odds import average_weighted_odds
from database.crud.bet import get_bets_by_event_id
from database.crud.event import get_all_event_ids
from database.database_connector import DatabaseConnector


@pytest.fixture()
async def db():
    test_database = DatabaseConnector(url="sqlite+aiosqlite:///prod.db", echo=True)

    yield test_database

    await test_database.engine.dispose()


async def get_tgt_by_event_id(event_id: int, db_session) -> float:
    bets = await get_bets_by_event_id(event_id, db_session)
    print(bets)
    average_odds = average_weighted_odds(bets)
    return average_odds


@pytest.mark.asyncio
async def test_prod_data(db: 'DatabaseConnector'):
    async with db.session_factory.begin() as session:
        # assert 105.15 == await get_tgt_by_event_id(123, session)
        # assert -101.24 == await get_tgt_by_event_id(113, session)
        # assert 101 == await get_tgt_by_event_id(136, session)
        await get_tgt_by_event_id(31, session)


@pytest.mark.asyncio
async def test_prod_data_len(db: 'DatabaseConnector'):
    async with db.session_factory.begin() as session:
        data = await get_all_event_ids(session)
        assert len(data) == 172
