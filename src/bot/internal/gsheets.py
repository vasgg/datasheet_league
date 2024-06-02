from datetime import datetime
import logging

import gspread
from sqlalchemy.ext.asyncio import AsyncSession

from bot.internal.lists import MASTER_HEADER, MASTER_STATS, PLAYER_HEADER, PLAYER_STATS
from config import settings
from database.crud.event import count_events, get_average_weighted_odds_by_event_id, get_total_risk_by_event_id
from database.models import Event

logger = logging.getLogger(__name__)


async def ensure_master_sheet(client: gspread.Client) -> gspread.Worksheet:
    spreadsheet = client.open(settings.TABLE_NAME)
    try:
        worksheet = spreadsheet.worksheet("master")
    except gspread.exceptions.WorksheetNotFound:
        logger.info("Creating 'master' sheet as it does not exist.")
        worksheet = spreadsheet.add_worksheet("master", 100, 24)
        worksheet.append_row(MASTER_HEADER)
    first_row = worksheet.row_values(1)
    if not first_row or first_row != MASTER_HEADER:
        logger.info("Adding headers to 'master' sheet.")
        worksheet.insert_row(MASTER_HEADER)

    current_cols = len(worksheet.row_values(1))
    target_col = 24
    if current_cols < target_col:
        cols_to_add = target_col - current_cols
        worksheet.add_cols(cols_to_add)

    worksheet.update([MASTER_STATS[0]], 'L3:R3')
    worksheet.update([MASTER_STATS[1]], 'M4:R4', raw=False)
    worksheet.update([MASTER_STATS[2]], 'L5:R5')
    worksheet.update([MASTER_STATS[3]], 'L6:R6', raw=False)
    return worksheet


async def create_new_player_sheet(name: str, client: gspread.Client):
    spreadsheet = client.open(settings.TABLE_NAME)
    new_sheet = spreadsheet.add_worksheet(name, 100, 20)
    new_sheet.append_row(PLAYER_HEADER)
    new_sheet.update([PLAYER_STATS[0]], 'K3:Q3')
    new_sheet.update([PLAYER_STATS[1]], 'K4:Q4', raw=False)
    new_sheet.update([PLAYER_STATS[2]], 'K5:Q5')
    new_sheet.update([PLAYER_STATS[3]], 'K6:Q6', raw=False)
    logger.info(f"Created new sheet '{name}'")


async def post_to_master_sheet(event: Event, db_session: AsyncSession, client: gspread.Client):
    line = await count_events(db_session) + 1
    worksheet = await ensure_master_sheet(client)
    bet = [[datetime.now().strftime("%-m/%-d/%Y"), event.league, event.bet_name, str(event.worst_odds)]]
    win = [[f'=ROUND(IF(G{line}<0,(100/-G{line})*F{line},(G{line}/100)*F{line}),0)']]
    net = [[f'=IFERROR(IFS(REGEXMATCH(I{line}, "W"), H{line},REGEXMATCH(I{line}, "L"), 0-F{line}),0)']]
    worksheet.update(bet, f'B{line}:E{line}')
    worksheet.update(win, f'H{line}', raw=False)
    worksheet.update(net, f'J{line}', raw=False)
    logger.info(f"Added row to 'master': {bet}, line {line}")


async def post_to_player_sheet(sheet_name: str, event_id: int, data: list, line: int, client: gspread.Client):
    spreadsheet = client.open(settings.TABLE_NAME)
    worksheet = spreadsheet.worksheet(sheet_name)
    users_rows = count_filled_cells_in_notes_column(worksheet)
    new_line = users_rows + line
    more_data = [[
        f'=ROUND(IF(F{new_line}<0,(100/-F{new_line})*E{new_line},(F{new_line}/100)*E{new_line}),0)',
        f'=master!I{event_id + 1}',
        f'=IFERROR(IFS(REGEXMATCH(H{new_line}, "W"), G{new_line},REGEXMATCH(H{new_line}, "L"), 0-E{new_line}),0)'
    ]]
    worksheet.update(data, f'B{new_line}:F{new_line}')
    worksheet.update(more_data, f'G{new_line}:I{new_line}', raw=False)
    logger.info(f"Added row to '{sheet_name}': {data}, line {new_line}")


async def update_master_list_values(event_id: int, line: int, client: gspread.Client, db_session: AsyncSession):
    total_risk = await get_total_risk_by_event_id(event_id, db_session)
    average_odds = await get_average_weighted_odds_by_event_id(event_id, db_session)
    spreadsheet = client.open(settings.TABLE_NAME)
    worksheet = spreadsheet.worksheet("master")
    worksheet.update([[total_risk, average_odds]], f'F{line}:G{line}')
    logger.info(f"Updated 'master' list: {total_risk}, {average_odds}, line {line}")


async def get_user_balance(fullname: str, client: gspread.Client) -> str:
    spreadsheet = client.open(settings.TABLE_NAME)
    worksheet = spreadsheet.worksheet(f"{fullname} bets")
    return worksheet.acell('K4').value


def count_filled_cells_in_notes_column(worksheet: gspread.Worksheet) -> int:
    values = worksheet.col_values(1)[1:555]
    filled_cells_count = sum(1 for value in values if value)
    return filled_cells_count


async def add_summ_balance_formula(client: gspread.Client):
    spreadsheet = client.open(settings.TABLE_NAME)
    all_sheets = spreadsheet.worksheets()
    sheet_names = [sheet.title for sheet in all_sheets if sheet.title.lower() != 'master']
    formula_parts = [f"INDIRECT(\"{sheet_name}!K4\")" for sheet_name in sheet_names]
    formula = f"=SUM({','.join(formula_parts)})"
    worksheet = await ensure_master_sheet(client)
    worksheet.update([[formula]], f'L4', raw=False)
