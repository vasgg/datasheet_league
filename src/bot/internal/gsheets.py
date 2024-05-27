import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

import gspread

from config import settings

MASTER_HEADER = ['Notes', 'ID', 'Date sent', 'League', 'Bet Name', 'Worst Odds', 'Responses']
PLAYER_HEADER = ['Notes', 'ID', 'Date sent', 'League', 'Bet Name', 'Risk', 'Odds', 'Win', 'Result', 'Net']

STATS_TABLE = [
    ['average pos odds', '=AVERAGE(FILTER(G:G,G:G>0))'],
    ['average neg odds', '=AVERAGE(FILTER(G:G,G:G<0))']
]
logger = logging.getLogger(__name__)


async def add_stats_table_to_player_sheet(worksheet, pool):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(pool, worksheet.update_acell, 'K3', STATS_TABLE[0][0])
    await loop.run_in_executor(pool, worksheet.update_acell, 'K5', STATS_TABLE[1][0])
    await loop.run_in_executor(pool, worksheet.update_acell, 'K4', STATS_TABLE[0][1])
    await loop.run_in_executor(pool, worksheet.update_acell, 'K6', STATS_TABLE[1][1])


async def ensure_master_sheet(client: gspread.Client):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        spreadsheet = await loop.run_in_executor(pool, client.open, settings.TABLE_NAME)
        try:
            worksheet = await loop.run_in_executor(pool, spreadsheet.worksheet, "master")
        except gspread.exceptions.WorksheetNotFound:
            logger.info("Creating 'master' sheet as it does not exist.")
            worksheet = await loop.run_in_executor(pool, spreadsheet.add_worksheet, "master", 100, 20)
            await loop.run_in_executor(pool, worksheet.append_row, MASTER_HEADER)
            return

        first_row = await loop.run_in_executor(pool, worksheet.row_values, 1)
        if not first_row or first_row != MASTER_HEADER:
            logger.info("Adding headers to 'master' sheet.")
            await loop.run_in_executor(pool, worksheet.insert_row, MASTER_HEADER, 1)


async def create_new_player_sheet(name: str, client: gspread.Client):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        spreadsheet = await loop.run_in_executor(pool, client.open, settings.TABLE_NAME)
        new_sheet = await loop.run_in_executor(pool, spreadsheet.add_worksheet, name, 100, 20)
        await loop.run_in_executor(pool, new_sheet.append_row, PLAYER_HEADER)
        await add_stats_table_to_player_sheet(new_sheet, pool)


async def post_to_master_sheet(data: dict, client: gspread.Client):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        spreadsheet = await loop.run_in_executor(pool, client.open, settings.TABLE_NAME)
        await ensure_master_sheet(client)
        worksheet = await loop.run_in_executor(pool, spreadsheet.worksheet, "master")
        row_values = [data.get(key, '') for key in data.keys()]
        num_rows = len(await loop.run_in_executor(pool, worksheet.get_all_values))
        await loop.run_in_executor(pool, worksheet.insert_row, row_values, num_rows + 1)
        logger.info(f"Added row to 'master': {row_values}")

        all_sheets = await loop.run_in_executor(pool, spreadsheet.worksheets)
        sheet_names = [sheet.title for sheet in all_sheets if sheet.title != 'master']

        countif_formula_parts = [f"COUNTIF('{sheet_name}'!B:B, B{num_rows + 1})" for sheet_name in sheet_names]
        formula = f"= {' + '.join(countif_formula_parts)}"

        await loop.run_in_executor(pool, worksheet.update_acell, f"G{num_rows + 1}", formula)


async def get_column_height(worksheet, column_index, pool):
    loop = asyncio.get_event_loop()
    col_values = await loop.run_in_executor(pool, worksheet.col_values, column_index)
    return len([value for value in col_values if value])


async def post_to_player_sheet(sheet_name: str, data: dict, client: gspread.Client):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        spreadsheet = await loop.run_in_executor(pool, client.open, settings.TABLE_NAME)
        worksheet = await loop.run_in_executor(pool, spreadsheet.worksheet, sheet_name)
        row_values = [data.get(key, '') for key in PLAYER_HEADER]

        num_rows = await get_column_height(worksheet, 2, pool)
        await loop.run_in_executor(pool, worksheet.insert_row, row_values, num_rows + 1)

        logger.info(f"Added row to '{sheet_name}': {row_values}")


