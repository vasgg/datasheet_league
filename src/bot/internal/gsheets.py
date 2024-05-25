import asyncio

import gspread
from oauth2client.service_account import ServiceAccountCredentials


async def update_master_sheet(cell: str, value: int):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(credentials)

    spreadsheet = client.open("League_bets")
    worksheet = spreadsheet.sheet1

    await asyncio.to_thread(worksheet.update, cell, [[value]])
    return {"message": f'Users counter updated. Cell: {cell} Value: {value}'}


async def create_new_sheet(name: str, client: gspread.Client):
    spreadsheet = client.open("League_bets")
    new_sheet = spreadsheet.add_worksheet(title=name, rows=100, cols=20)
    header = ['Notes', 'Date sent', 'League', 'Bet Name', 'Risk', 'Odds', 'Win', 'Result', 'Net']
    new_sheet.append_row(header)
