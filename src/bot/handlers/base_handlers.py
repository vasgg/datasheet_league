import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager
from gspread import Client
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.users_dialog import start_dialog_handler, start_dialog_handler_for_group
from bot.internal.gsheets import delete_bet_from_user_sheet, get_user_balance, post_to_player_sheet, \
    update_master_list_values
from config import settings
from database.crud.bet import count_bets_from_user, withdraw_bet, get_last_bet_by_user_id, get_user_bets_by_event_id
from database.crud.event import get_active_events, get_event_by_id, get_all_event_ids, has_group_with_name, \
    get_groups_for_user, delete_group_by_name
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
    text = '\n'.join(
        [f'Event {event.id}, {event.league}, {event.bet_name}, {event.worst_odds}' for event in active_events])
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
                                  'use <code>/new League, bet_name, worst odds</code>')
        return
    await state.update_data(league=league, bet_name=bet_name, worst_odds=worst_odds)
    text = f'Creating new event: {league}, {bet_name}, worst odds {worst_odds}'
    await message.answer(text=text)
    await start_dialog_handler(message, dialog_manager)


@router.message(Command('list_groups'))
async def list_group_handler(message: types.Message, state: FSMContext,
                             db_session: AsyncSession) -> None:
    if message.from_user.id not in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer(text='list_groups command enabled only for owner and bet admins.')
        return

    groups = await get_groups_for_user(message.from_user.id, db_session)
    text = f"You have {len(groups)} groups:\n\n" if groups else "You have no groups!\n\n"
    if len(groups) == 1:
        text = text.replace('groups', 'group')
    answer_text = text + '\n'.join([grp.group_name for grp in groups])
    await message.answer(answer_text)


@router.message(Command('delete_group'))
async def delete_group_handler(message: types.Message, state: FSMContext,
                               db_session: AsyncSession) -> None:
    if message.from_user.id not in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer(text='delete_group command enabled only for owner and bet admins.')
        return

    try:
        group_name = message.text.split(' ')[1]
        await state.update_data(group_name=group_name)
    except (ValueError, IndexError):
        await message.answer(text='please provide correct values\n'
                                  'use <code>/delete_group GroupName</code>')
        return
    result = await delete_group_by_name(group_name, message.from_user.id, db_session)
    if result:
        await message.answer(
            text=f"Group '{group_name}' deleted successfully."
        )
    else:
        await message.answer(
            text=f"Group '{group_name}' not found."
        )



@router.message(Command('create_group'))
async def create_group_handler(message: types.Message, dialog_manager: DialogManager, state: FSMContext,
                               db_session: AsyncSession) -> None:
    if message.from_user.id not in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer(text='create_group command enabled only for owner and bet admins.')
        return

    try:
        group_name = message.text.split(' ')[1]
        await state.update_data(group_name=group_name)
    except (ValueError, IndexError):
        await message.answer(text='please provide correct values\n'
                                  'use <code>/create_group GroupName</code>')
        return

    has_group = await has_group_with_name(group_name, message.from_user.id, db_session)
    if has_group:
        await message.answer("Group with such name already exists")
        return

    await message.answer(text=f"Select users to add to group '{group_name}'")
    await start_dialog_handler_for_group(message, dialog_manager)


@router.message(Command('fill'))
async def new_game_message(message: types.Message, user: User, db_session: AsyncSession,
                           gspread_client: Client) -> None:
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
    if not event:
        await message.answer(text=f'don\'t have access to event {event_id}\n'
                                  f'use /show_active to find active events')
        return
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
    await message.answer("Filling...")
    db_session.add(bet)
    await db_session.flush()
    data = [[
        datetime.now().strftime("%-m/%-d/%Y %H:%M:%S"),
        event.league,
        event.bet_name,
        bet.risk_amount,
        bet.odds,
    ]]
    sheet_name = f'{user.fullname} bets'
    bets = await count_bets_from_user(message.from_user.id, db_session) - 1
    line = bets + 2
    await post_to_player_sheet(sheet_name, event_id, data, line, gspread_client)
    await update_master_list_values(event_id, gspread_client, db_session)
    await message.answer(text=f'Event {event_id}, {event.league}, {event.bet_name}:\n'
                              f'Bet {bet.risk_amount}, Odds {bet.odds} filled.')


@router.message(Command('cancel'))
async def cancel_bet_command(message: types.Message, user: User, db_session: AsyncSession,
                             gspread_client: Client) -> None:
    if message.from_user.id in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer(text='Cancel command disabled for owner and bet admins.')
        return
    user_bets = await count_bets_from_user(user.telegram_id, db_session)
    last_bet = await get_last_bet_by_user_id(user.telegram_id, db_session)
    if not last_bet:
        await message.answer(text='No bets to cancel.')
        return
    await message.answer("Canceling...")
    await delete_bet_from_user_sheet(user, user_bets, gspread_client)
    await withdraw_bet(last_bet.id, db_session)
    await update_master_list_values(last_bet.event_id, gspread_client, db_session)
    await message.answer(text='Last bet canceled.')


@router.message(Command('recount'))
async def recount_command(message: types.Message, db_session: AsyncSession, gspread_client: Client) -> None:
    if message.from_user.id not in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer(text='Recount command disabled for users.')
        return
    try:
        event_id = int(message.text.split()[1])
    except (ValueError, IndexError):
        await message.answer(text='please provide correct event id')
        return
    event = await get_event_by_id(event_id, db_session)
    if not event:
        await message.answer(text=f'can\'t find event {event_id}')
        return
    await message.answer(text='Recounting values in master list...')
    await update_master_list_values(event_id, gspread_client, db_session)


@router.message(Command('recount_all'))
async def recount_command(message: types.Message, db_session: AsyncSession, gspread_client: Client) -> None:
    if message.from_user.id not in [settings.OWNER, *settings.BET_ADMINS]:
        await message.answer('Recount command disabled for users.')
        return

    events = await get_all_event_ids(db_session)
    await message.answer('Starting recounting...')
    for event_id in events:
        logging.info(f"Updating {event_id=}")
        await update_master_list_values(event_id, gspread_client, db_session)
        await asyncio.sleep(3)
    await message.answer("Recounting done")
