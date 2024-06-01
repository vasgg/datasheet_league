from datetime import datetime, timezone

from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager
from gspread import Client
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.users_dialog import start_dialog_handler
from bot.internal.gsheets import get_user_balance, post_to_player_sheet, update_master_list_values
from config import settings
from database.crud.bet import count_bets_from_user, get_user_bets_by_event_id
from database.crud.event import get_active_events, get_event_by_id
from database.models import Bet, User
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
async def new_game_message(message: types.Message, dialog_manager: DialogManager, state: FSMContext) -> None:
    if message.from_user.id not in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer(text='New command enabled only for owner and bet admins.')
        return
    try:
        league = message.text.split(',')[0].split()[1]
        bet_name = message.text.split(',')[1].strip()
        worst_odds = int(message.text.split(',')[2].strip())
    except (ValueError, IndexError):
        await message.answer(text='please provide correct values\n'
                                  'use <code>/new Legue, bet_name, worst odds</code>')
        return
    await state.update_data(league=league, bet_name=bet_name, worst_odds=worst_odds)
    text = f'Creating new event, {league}, {bet_name}, worst odds {worst_odds}...'
    await message.answer(text=text)
    await start_dialog_handler(message, dialog_manager)


@router.message(Command('fill'))
async def new_game_message(message: types.Message, db_session: AsyncSession, gspread_client: Client) -> None:
    if message.from_user.id in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer(text='Fill command disabled for owner and bet admins.')
        return
    if message.text == '/fill':
        await message.answer(text='use <code>/fill event_id, risk_amount, odds</code>\n'
                                  f'or /show_active to find active events')
        return
    try:
        event_id = int(message.text.split()[1].strip(','))
        risk_amount = int(message.text.split(',')[1].strip())
        odds = int(message.text.split(',')[2].strip())
    except (ValueError, IndexError):
        await message.answer(text='please provide correct values')
        return
    event = await get_event_by_id(event_id, db_session)
    if odds < event.worst_odds:
        await message.answer(text=f'odds less than {event.worst_odds} are not accepted.')
        return
    bets = await get_user_bets_by_event_id(event_id, message.from_user.id, db_session)
    match len(bets):
        case 0:
            await message.answer(text=f'don\'t have access to event {event_id}\n'
                                      f'use /show_active to find active events')
            return
        case 1:
            bet = bets[0]
            if bet.status == BetStatus.INVITED:
                bet.risk_amount = risk_amount
                bet.odds = odds
                bet.created_at = datetime.now(timezone.utc)
                bet.status = BetStatus.FILLED
            else:
                bet = Bet(
                    event_id=event_id,
                    user_telegram_id=message.from_user.id,
                    risk_amount=risk_amount,
                    odds=odds,
                    created_at=datetime.now(timezone.utc),
                    status=BetStatus.FILLED
                )
        case _:
            bet = Bet(
                event_id=event_id,
                user_telegram_id=message.from_user.id,
                risk_amount=risk_amount,
                odds=odds,
                created_at=datetime.now(timezone.utc),
                status=BetStatus.FILLED
            )
    await message.answer(text=f'Event {event_id}, {event.league}, {event.bet_name}:\n'
                              f'Bet {bet.risk_amount}, Odds {bet.odds} filled.')
    db_session.add(bet)
    data = [[
        datetime.now().strftime("%-m/%-d/%Y"),
        event.league,
        event.bet_name,
        bet.risk_amount,
        bet.odds,
    ]]
    sheet_name = f'{message.from_user.full_name} bets'
    bets = await count_bets_from_user(message.from_user.id, db_session)
    line = bets + 2
    await post_to_player_sheet(sheet_name, event_id, data, line, gspread_client)
    await update_master_list_values(event_id, event_id + 1, gspread_client, db_session)
