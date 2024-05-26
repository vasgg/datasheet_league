import asyncio
import contextlib
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
import gspread

from bot.internal.gsheets import create_new_player_sheet
from config import settings
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
            if event.from_user.id != settings.ADMIN:
                with contextlib.suppress(gspread.exceptions.APIError):
                    # noinspection PyUnusedLocal
                    # add_new_sheet_task = asyncio.create_task(create_new_sheet(sheet_name, gspread_client))
                    # Update id=117922019 is handled. Duration 2623 ms by bot id=7063890126
                    add_new_sheet_task = asyncio.create_task(create_new_player_sheet(sheet_name, gspread_client))
                    # 26.05.2024|17:34:56+0400.168|INFO|dispatcher|feed_update: Update id=117922021 is handled. Duration 304 ms by bot id=7063890126

                    # await asyncio.to_thread(await create_new_sheet(sheet_name, gspread_client))
        data['user'] = user
        return await handler(event, data)
