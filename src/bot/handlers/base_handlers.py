from datetime import datetime, timezone

from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram_dialog import DialogManager
from gspread import Client
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.users_dialog import start_dialog_handler
from config import settings
from database.crud.bet import get_bet_by_id
from database.crud.event import get_active_events, get_event_by_id
from database.models import Bet, Event, User
from enums import BetStatus

router = Router()


@router.message(CommandStart())
async def start_message(message: types.Message, user: User) -> None:
    await message.answer(text=f'Hello, {user.fullname}.')


@router.message(Command('balance'))
async def support_message(message: types.Message, db_session: AsyncSession) -> None:
    await message.answer(text='balance command')


@router.message(Command('show_active'))
async def support_message(message: types.Message, db_session: AsyncSession) -> None:
    active_events = await get_active_events(message.from_user.id, db_session)
    text = '\n'.join([f'{event.id} ({event.league}, {event.bet_name}, {event.worst_odds})' for event in active_events])
    await message.answer(text=text if text else 'No active events')


@router.message(Command('new'))
async def new_game_message(message: types.Message, db_session: AsyncSession, dialog_manager: DialogManager) -> None:
    if message.from_user.id != settings.ADMIN:
        return
    new_event = Event(
        league=message.text.split(',')[0].split()[1],
        bet_name=message.text.split(',')[1].strip(),
        worst_odds=int(message.text.split(',')[2].strip()),
    )
    db_session.add(new_event)
    await db_session.flush()
    text = f'Event {new_event.id} created.'
    await message.answer(text=text)
    await start_dialog_handler(message, dialog_manager)


@router.message(Command('fill'))
async def new_game_message(message: types.Message, db_session: AsyncSession, gspread_client: Client) -> None:
    if message.from_user.id == settings.ADMIN:
        await message.answer(text='this command is disabled for admins')
        return
    if message.text == '/fill':
        await message.answer(text='use /fill event_id, risk_amount, odds\n'
                                  f'or /show_active to find active events')

        return
    event_id = int(message.text.split()[1].strip(','))
    event = await get_event_by_id(event_id, db_session)
    bet: Bet = await get_bet_by_id(event_id, db_session)
    if not bet:
        await message.answer(text=f'don\'t have access to event {event_id}\n'
                                  f'use /show_active to find active events')
        return
    risk_amount = int(message.text.split(',')[1].strip())
    odds = int(message.text.split(',')[2].strip())
    if odds < event.worst_odds:
        await message.answer(text=f'odds less than {event.worst_odds} are not accepted.')
        return
    bet.risk_amount = risk_amount
    bet.odds = odds
    bet.status = BetStatus.PENDING
    bet.created_at = datetime.now(timezone.utc)
    db_session.add(bet)
    await db_session.commit()
    await message.answer(text=f'Event {event_id}, {event.league}, {event.bet_name}:\n'
                              f'Bet {bet.risk_amount}, Odds {bet.odds} filled.')
