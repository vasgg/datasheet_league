import logging

import gspread
from aiogram import types
from aiogram.exceptions import TelegramForbiddenError

from bot.internal.gsheets import post_to_master_sheet
from database.crud.user import get_all_users_ids, get_user_from_db_by_tg_id
from database.models import Event, Bet


async def process_new_bet(league, bet_name, worst_odds,
                          db_session, selected_users: list[str],
                          callback: types.CallbackQuery,
                          google_client: gspread.Client,
                          from_group: bool = False
                          ):
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
        if str(user_id) in selected_users:
            new_bet = Bet(
                event_id=event.id,
                user_telegram_id=user_id,
            )
            db_session.add(new_bet)
            try:
                await callback.bot.send_message(user_id, text)
            except TelegramForbiddenError:
                logging.debug(f"TelegramForbiddenError skipped for {user_id=}")

    if not from_group:
        user = await get_user_from_db_by_tg_id(callback.from_user.id, db_session)
        user.selected = ';'.join(selected_users)

    await callback.message.answer(f'Invitation sent to {len(selected_users)} user(s).')
    await post_to_master_sheet(event, db_session, google_client)
