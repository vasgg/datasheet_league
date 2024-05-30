import asyncio
import logging.config
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog.setup import setup_dialogs

from bot.handlers.base_handlers import router as base_router
from bot.internal.commands import set_bot_commands
from bot.handlers.users_dialog import select_users_dialog
from bot.middlewares.auth_middleware import AuthMiddleware
from bot.middlewares.session_middlewares import DBSessionMiddleware, GSpreadSessionMiddleware
from bot.middlewares.updates_dumper_middleware import UpdatesDumperMiddleware
from config import get_logging_config, settings
from database.tables_helper import create_or_drop_db, get_db


async def main():
    logs_directory = Path("logs")
    logs_directory.mkdir(parents=True, exist_ok=True)
    logging_config = get_logging_config(__name__)
    logging.config.dictConfig(logging_config)

    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logging.info("bot started")
    storage = MemoryStorage()

    db = get_db()
    await create_or_drop_db(db.engine)

    dispatcher = Dispatcher(storage=storage)
    db_session_middleware = DBSessionMiddleware(db)
    dispatcher.message.middleware(db_session_middleware)
    dispatcher.callback_query.middleware(db_session_middleware)
    dispatcher.message.middleware(GSpreadSessionMiddleware())
    dispatcher.callback_query.middleware(GSpreadSessionMiddleware())
    dispatcher.message.middleware(AuthMiddleware())
    dispatcher.callback_query.middleware(AuthMiddleware())
    dispatcher.update.outer_middleware(UpdatesDumperMiddleware())
    dispatcher.startup.register(set_bot_commands)
    dispatcher.include_routers(base_router, select_users_dialog)

    setup_dialogs(dispatcher)
    await dispatcher.start_polling(bot)


def run_main():
    asyncio.run(main())


if __name__ == '__main__':
    run_main()
