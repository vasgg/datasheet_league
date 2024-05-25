import asyncio
import contextlib
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
import gspread

from bot.internal.gsheets import create_new_sheet
from database.crud.user import add_user_to_db, get_user_from_db_by_tg_id


class AuthMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        session = data['db_session']
        gspread_client = data['gspread_client']
        user = await get_user_from_db_by_tg_id(event.from_user.id, session)
        if not user:
            user = await add_user_to_db(event.from_user, session)
            sheet_name = f'{user.fullname} bets'
            with contextlib.suppress(TypeError, gspread.exceptions.APIError):
                await asyncio.to_thread(await create_new_sheet(sheet_name, gspread_client))
        data['user'] = user
        return await handler(event, data)
