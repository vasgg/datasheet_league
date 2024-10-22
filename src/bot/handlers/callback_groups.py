

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.internal.callback_data_classe import MyCallback
from bot.internal.helpers import process_new_bet
from database.crud.event import get_group_by_id

router = Router()


@router.callback_query(MyCallback.filter())
async def send_with_selected_group(callback: types.CallbackQuery,
                                   callback_data: MyCallback,
                                   state: FSMContext, db_session: AsyncSession, gspread_client) -> None:
    await callback.answer()
    await callback.message.delete()

    data = await state.get_data()
    league = data.get('league')
    bet_name = data.get('bet_name')
    worst_odds = data.get('worst_odds')

    group_id = callback_data.group_id
    group = await get_group_by_id(group_id, db_session)

    await process_new_bet(league, bet_name, worst_odds, db_session, group.selected.split(';'), callback, gspread_client,
                          from_group=True)

