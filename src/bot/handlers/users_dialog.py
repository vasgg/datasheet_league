import operator

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram_dialog import (Dialog, DialogManager, StartMode, Window)
from aiogram_dialog.widgets.kbd import Button, Cancel, Group, Multiselect
from aiogram_dialog.widgets.text import Const, Format
from sqlalchemy.ext.asyncio import AsyncSession

from bot.internal.callback_data_classe import MyCallback
from bot.internal.helpers import process_new_bet
from database.crud.event import get_groups_for_user
from database.crud.user import get_all_users, get_last_time_checked_users_ids_for_one
from database.models import GroupTable


class DialogSG(StatesGroup):
    select_users = State()
    send_message = State()


class DialogSGGroup(StatesGroup):
    select_users_for_group = State()


async def get_users_data(dialog_manager: DialogManager, db_session: AsyncSession, **kwargs):
    users = await get_all_users(db_session)
    user_items = [(user.fullname, user.telegram_id) for user in users]
    return {
        "users": user_items,
    }


async def on_send_to_group(callback: CallbackQuery, button: Button, manager: DialogManager, **kwargs):
    await callback.answer()
    await callback.message.delete()

    db_session = manager.middleware_data['db_session']
    groups = await get_groups_for_user(callback.from_user.id, db_session)
    if not groups:
        await callback.message.answer(f'No groups were created yet')
        return

    await manager.reset_stack()

    btn_list = []
    for group in groups:
        btn = InlineKeyboardButton(
            text=group.group_name, callback_data=MyCallback(group_id=group.id).pack())
        btn_list.append([btn])

    kbd = InlineKeyboardMarkup(inline_keyboard=btn_list)

    await callback.message.answer(
        f'Select group to send and event to:\n',
        reply_markup=kbd)


async def on_user_group_selected(callback: CallbackQuery, button: Button, manager: DialogManager, **kwargs):
    await callback.answer()
    await callback.message.delete()

    state = manager.middleware_data['state']
    db_session = manager.middleware_data['db_session']
    data = await state.get_data()
    group_name = data.get('group_name')

    users_multiselect_widget = manager.dialog().find("m_users")
    selected_users = users_multiselect_widget.get_checked(manager)
    await manager.reset_stack()
    group = GroupTable(group_name=group_name,
                       user_telegram_id=callback.from_user.id,
                       selected=';'.join(selected_users))
    db_session.add(group)
    await db_session.flush()
    await callback.message.answer(f'Group added')


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

    await process_new_bet(league, bet_name, worst_odds, db_session, selected_users, callback, client)


async def on_dialog_start(start_data: int, manager: DialogManager):
    db_session = manager.middleware_data['db_session']
    last_time_checked_users_ids = await get_last_time_checked_users_ids_for_one(start_data, db_session)
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
        Button(Const("Send using group"), id='group_send', on_click=on_send_to_group),
        Cancel(),
        state=DialogSG.select_users,
        getter=get_users_data,
    ),
    on_start=on_dialog_start,
)

select_users_for_group_dialog = Dialog(
    Window(
        Const("Select users to add to group:\n"),
        grouped_multiselect,
        Button(Const("Confirm Selection"), id="confirm", on_click=on_user_group_selected),
        Cancel(),
        state=DialogSGGroup.select_users_for_group,
        getter=get_users_data,
    )
)


async def start_dialog_handler(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(DialogSG.select_users,
                               data=message.from_user.id,
                               mode=StartMode.RESET_STACK)


async def start_dialog_handler_for_group(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(DialogSGGroup.select_users_for_group,
                               mode=StartMode.RESET_STACK)
