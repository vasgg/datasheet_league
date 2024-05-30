from datetime import datetime, timezone

from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram_dialog import DialogManager
from gspread import Client
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.users_dialog import start_dialog_handler
from bot.internal.gsheets import get_user_balance, post_to_player_sheet, update_master_list_values
from config import settings
from database.crud.bet import count_bets_from_user, get_bet_by_id
from database.crud.event import get_active_events, get_event_by_id
from database.models import Bet, Event, User
from enums import BetStatus

router = Router()


@router.message(CommandStart())
async def start_message(message: types.Message, user: User) -> None:
    await message.answer(text=f'Hello, {user.fullname}.')


@router.message(Command('balance'))
async def balance_message(message: types.Message, gspread_client: Client) -> None:
    if message.from_user.id in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer(text='Balance command disabled for owner and bet admins.')
        return
    user_balance = await get_user_balance(message.from_user.full_name, gspread_client)
    await message.answer(text=f'Balance: {user_balance}')


@router.message(Command('settle'))
async def settle_message(message: types.Message) -> None:
    if message.from_user.id in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer(text='Settle command disabled for owner and bet admins.')
        return
    name = '@' + message.from_user.username + ' ' + message.from_user.full_name if message.from_user.username else message.from_user.full_name
    await message.answer(text='Notification sended to owner.')
    await message.bot.send_message(settings.OWNER, text=f'Settle command called by {name}.')


@router.message(Command('show_active'))
async def support_message(message: types.Message, db_session: AsyncSession) -> None:
    if message.from_user.id in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer(text='Show_active command disabled for owner and bet admins.')
        return
    active_events = await get_active_events(message.from_user.id, db_session)
    text = '\n'.join([f'{event.id} ({event.league}, {event.bet_name}, {event.worst_odds})' for event in active_events])
    await message.answer(text=text if text else 'No active events')


@router.message(Command('new'))
async def new_game_message(message: types.Message, db_session: AsyncSession, dialog_manager: DialogManager) -> None:
    if message.from_user.id not in [settings.OWNER, *settings.BET_ADMINS]:
        return
    try:
        league = message.text.split(',')[0].split()[1]
        bet_name = message.text.split(',')[1].strip()
        worst_odds = int(message.text.split(',')[2].strip())
    except ValueError:
        await message.answer(text='please provide correct values')
        return
    new_event = Event(
        league=league,
        bet_name=bet_name,
        worst_odds=worst_odds,
    )
    db_session.add(new_event)
    await db_session.flush()
    text = f'Event {new_event.id}, {new_event.league}, {new_event.bet_name}, worst odds {new_event.worst_odds} added'

    await message.answer(text=text)
    await start_dialog_handler(message, dialog_manager)


@router.message(Command('fill'))
async def new_game_message(message: types.Message, db_session: AsyncSession, gspread_client: Client) -> None:
    if message.from_user.id in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer(text='Fill command disabled for owner and bet admins.')
        return
    if message.text == '/fill':
        await message.answer(text='use /fill event_id, risk_amount, odds\n'
                                  f'or /show_active to find active events')

        return
    try:
        event_id = int(message.text.split()[1].strip(','))
        risk_amount = int(message.text.split(',')[1].strip())
        odds = int(message.text.split(',')[2].strip())
    except ValueError:
        await message.answer(text='please provide correct values')
        return
    event = await get_event_by_id(event_id, db_session)
    bet: Bet = await get_bet_by_id(event_id, message.from_user.id, db_session)
    if not bet:
        await message.answer(text=f'don\'t have access to event {event_id}\n'
                                  f'use /show_active to find active events')
        return
    if odds < event.worst_odds:
        await message.answer(text=f'odds less than {event.worst_odds} are not accepted.')
        return
    bet.risk_amount = risk_amount
    bet.odds = odds
    bet.status = BetStatus.FILLED
    bet.created_at = datetime.now(timezone.utc)
    await message.answer(text=f'Event {event_id}, {event.league}, {event.bet_name}:\n'
                              f'Bet {bet.risk_amount}, Odds {bet.odds} filled.')
    db_session.add(bet)
    await db_session.commit()
    data = [[
        datetime.now().strftime("%-m/%-d/%Y"),
        event.league,
        event.bet_name,
        bet.risk_amount,
        bet.odds,
    ]]
    line = await count_bets_from_user(message.from_user.id, db_session) + 1
    await post_to_player_sheet(f'{message.from_user.full_name} bets', data, line, gspread_client)
    await update_master_list_values(event_id, line, gspread_client, db_session)
