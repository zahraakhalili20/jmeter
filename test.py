#!/usr/bin/python
import os
import requests
from os import listdir
from os.path import isfile, join
import time
from datetime import datetime
import io
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import gspread

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client.json', scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("Template Report")
print(sheet)
sheet_id=sheet.worksheet("test_run_1").id
spreadsheet_id=sheet.id
row_count=9

#copy the first run template
headers = {
    "Authorization": "Bearer " + creds.get_access_token().access_token,
    "Content-Type": "application/json",
}
reqs = [
    {
        "copyPaste": {
            "source": {
                "sheetId": sheet_id,
                "startRowIndex": 2,
                "endRowIndex": 8,
                "startColumnIndex": 0,
                "endColumnIndex": 18,
            },
            "destination": {
                "sheetId": sheet_id,
                "startRowIndex": row_count,
                "endRowIndex": row_count + 7,
                "startColumnIndex": 0,
                "endColumnIndex": 18,
            },
            "pasteType": "PASTE_NORMAL",
            "pasteOrientation": "NORMAL",
        }
    }
]

r = requests.post(
    f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate",
    headers=headers,
    data=json.dumps({"requests": reqs}),
)