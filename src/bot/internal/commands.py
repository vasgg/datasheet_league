from aiogram import Bot, types

default_commands = [
    types.BotCommand(command='/start', description='start bot'),
    types.BotCommand(command='/balance', description='check balance'),
    types.BotCommand(command='/show_active', description='show active games'),
    types.BotCommand(command='/settle', description='request settle'),
]


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(default_commands)
