import asyncio
import logging
import operator
from typing import Any

from aiogram.exceptions import TelegramForbiddenError
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import (Dialog, DialogManager, StartMode, Window)
from aiogram_dialog.widgets.kbd import Button, Cancel, Group, Multiselect
from aiogram_dialog.widgets.text import Const, Format
from sqlalchemy.ext.asyncio import AsyncSession

from bot.internal.gsheets import post_to_master_sheet
from database.crud.user import get_all_users, get_all_users_ids, get_last_time_checked_users_ids, get_user_from_db_by_tg_id
from database.models import Bet, Event


class DialogSG(StatesGroup):
    select_users = State()
    send_message = State()


async def get_users_data(dialog_manager: DialogManager, db_session: AsyncSession, **kwargs):
    users = await get_all_users(db_session)
    user_items = [(user.fullname, user.telegram_id) for user in users]
    return {
        "users": user_items,
    }


async def on_user_selected(callback: CallbackQuery, button: Button, manager: DialogManager, **kwargs):
    await callback.answer()
    await callback.message.delete()

    state = manager.middleware_data['state']
    db_session = manager.middleware_data['db_session']
    client = manager.middleware_data["gspread_client"]
    data = await state.get_data()
    league = data.get('league')
    bet_name = data.get('bet_name')
    worst_odds = data.get('worst_odds')

    users_multiselect_widget = manager.dialog().find("m_users")
    selected_users = users_multiselect_widget.get_checked(manager)
    await manager.reset_stack()
    event = Event(
        league=league,
        bet_name=bet_name,
        worst_odds=worst_odds,
    )
    db_session.add(event)
    await db_session.flush()
    text = (f'Event {event.id}, {event.league}, {event.bet_name}, {event.worst_odds}\n'
            f'Use <code>/fill {event.id}, Risk Amount, Odds</code> to reply')
    all_users = await get_all_users_ids(db_session)
    for user_id in all_users:
        user = await get_user_from_db_by_tg_id(user_id, db_session)
        if str(user_id) in selected_users:
            user.last_time_checked = True
            new_bet = Bet(
                event_id=event.id,
                user_telegram_id=user_id,
            )
            db_session.add(new_bet)
            try:
                await callback.bot.send_message(user_id, text)
            except TelegramForbiddenError:
                logging.debug(f"TelegramForbiddenError skipped for {user_id=}")
        else:
            user.last_time_checked = False
        db_session.add(user)
    await callback.message.answer(f'Invitation sent to {len(selected_users)} user(s).')
    await post_to_master_sheet(event, db_session, client)


async def on_dialog_start(start_data: Any, manager: DialogManager):
    db_session = manager.middleware_data['db_session']
    last_time_checked_users_ids = await get_last_time_checked_users_ids(db_session)
    for user_id in last_time_checked_users_ids:
        await users_multiselect.set_checked(manager.event, user_id, True, manager)


users_multiselect = Multiselect(
    Format("✅ {item[0]}"),
    Format("{item[0]}  "),
    id="m_users",
    item_id_getter=operator.itemgetter(1),
    items="users",
    max_selected=100,
)

grouped_multiselect = Group(users_multiselect, width=3)

select_users_dialog = Dialog(
    Window(
        Const("Select users to invite:\n"),
        grouped_multiselect,
        Button(Const("Confirm Selection"), id="confirm", on_click=on_user_selected),
        Cancel(),
        state=DialogSG.select_users,
        getter=get_users_data,
    ),
    on_start=on_dialog_start,
)


async def start_dialog_handler(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(DialogSG.select_users, mode=StartMode.RESET_STACK)
