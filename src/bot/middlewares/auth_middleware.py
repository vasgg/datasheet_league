import asyncio
import contextlib
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
import gspread

from bot.internal.gsheets import add_summ_balance_formula, create_new_player_sheet
from config import settings
from database.crud.user import add_user_to_db, get_user_from_db_by_tg_id


class AuthMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        db_session = data['db_session']
        gspread_client = data['gspread_client']
        user = await get_user_from_db_by_tg_id(event.from_user.id, db_session)
        if not user:
            user = await add_user_to_db(event.from_user, db_session)
            if event.from_user.id not in [settings.OWNER, *settings.BET_ADMINS]:
                with contextlib.suppress(gspread.exceptions.APIError):
                    sheet_name = f'{user.fullname} bets'
                    add_player_sheet_task = asyncio.create_task(create_new_player_sheet(sheet_name, gspread_client))
                    add_balance_sheet_task = asyncio.create_task(add_summ_balance_formula(gspread_client))
        data['user'] = user
        return await handler(event, data)
