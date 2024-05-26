import asyncio
from concurrent.futures import ThreadPoolExecutor
import gspread

from config import settings


async def create_new_player_sheet(name: str, client: gspread.Client):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        spreadsheet = await loop.run_in_executor(pool, client.open, settings.TABLE_NAME)
        new_sheet = await loop.run_in_executor(pool, spreadsheet.add_worksheet, name, 100, 20)
        header = ['Notes', 'Date sent', 'League', 'Bet Name', 'Risk', 'Odds', 'Win', 'Result', 'Net']
        await loop.run_in_executor(pool, new_sheet.append_row, header)


async def post_to_master_sheet(data: dict, client: gspread.Client):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        spreadsheet = await loop.run_in_executor(pool, client.open, settings.TABLE_NAME)
        worksheet = await loop.run_in_executor(pool, spreadsheet.worksheet, "master")
        row_values = [data.get(key, '') for key in data.keys()]
        await loop.run_in_executor(pool, worksheet.append_row, row_values)


async def post_to_player_sheet(sheet_name: str, data: dict, client: gspread.Client):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        spreadsheet = await loop.run_in_executor(pool, client.open, settings.TABLE_NAME)
        worksheet = await loop.run_in_executor(pool, spreadsheet.worksheet, sheet_name)
        row_values = [data.get(key, '') for key in data.keys()]
        await loop.run_in_executor(pool, worksheet.append_row, row_values)
