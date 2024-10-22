from aiogram.filters.callback_data import CallbackData


class MyCallback(CallbackData, prefix="group_send"):
    group_id: int
