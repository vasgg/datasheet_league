from datetime import datetime
import operator

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import (Dialog, DialogManager, StartMode, Window)
from aiogram_dialog.widgets.kbd import Button, Cancel, Group, Multiselect
from aiogram_dialog.widgets.text import Const, Format
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from bot.internal.gsheets import post_to_master_sheet
from database.crud.event import get_last_event
from database.crud.user import get_all_users
from database.models import Bet
from database.tables_helper import get_db


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
    users_multiselect_widget = manager.dialog().find("m_users")
    selected_users = users_multiselect_widget.get_checked(manager)
    await manager.reset_stack()
    db = get_db()
    async with db.session_factory() as db_session:
        event = await get_last_event(db_session)
        text = (f'Event {event.id}, {event.league}, {event.bet_name}, {event.worst_odds}\n'
                f'Use <code>/fill {event.id}, Risk Amount, Odds</code> to reply')
        for user in selected_users:
            new_bet = Bet(
                event_id=event.id,
                user_telegram_id=user,
            )
            db_session.add(new_bet)
            await db_session.flush()
            await callback.bot.send_message(user, text)
        await db_session.commit()
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(credentials)
    data = {
        'Notes': '',
        'Date sent': datetime.now().strftime("%-m/%-d/%Y"),
        'League': event.league,
        'Bet Name': event.bet_name,
        'Worst Odds': event.worst_odds
    }
    await post_to_master_sheet(data, client)
    await callback.message.answer(f'Invitation sent to {len(selected_users)} users!')


users_multiselect = Multiselect(
    Format("✅ {item[0]}"),
    Format("{item[0]}  "),
    id="m_users",
    item_id_getter=operator.itemgetter(1),
    items="users",
    min_selected=1,
    max_selected=20,
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
)


async def start_dialog_handler(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(DialogSG.select_users, mode=StartMode.RESET_STACK)
