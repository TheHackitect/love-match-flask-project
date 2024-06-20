import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot, Poll
import time
import schedule
import asyncio
import sqlite3

# Configuration
# TOKEN = '7232566915:AAEBrH8ddk3jloU8IO4XiPCTBaStlGqIJbc'
TOKEN = '5982304690:AAEHikZumTlJUpZx4Ivmro-CFpDNVILnwj8'
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1ZG4ctUtbkRq8dZg13stXiHgiYT_VLMIqAlDJeEA5at4/edit?usp=sharing'
# SHEET_URL = 'https://docs.google.com/spreadsheets/d/1iFfUfiOt-OFMvD8MVfD3VwBkrMzbf5lVQ4vMychu2_M/edit?usp=sharing'
CREDENTIALS_FILE = 'credentials.json'  # Path to your Google API credentials JSON file

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL)
worksheet = sheet.get_worksheet(1)  # Assuming the data is in the first worksheet

# Telegram bot setup
bot = Bot(token=TOKEN)


# SQLite setup
conn = sqlite3.connect('results.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_results (
        user_id TEXT PRIMARY KEY,
        match1 TEXT,
        match2 TEXT,
        match3 TEXT
    )
''')
conn.commit()

async def send_results():
    rows = worksheet.get_all_records()
    print(rows)
    for i, row in enumerate(rows):  # start=2 to account for the header row
        user_id = row['user_id']
        print(user_id)
        results = [row['Match #1'], row['Match #2'], row['Match #3']]
        message = f"Your results are: {results}"
        try:
            await bot.send_message(chat_id=user_id, text=message)
        except:
            pass

def post_prompts():
    rows = worksheet.get_all_records()
    for row in rows:
        if row['type'] == 'prompt':
            image_url = row['url']
            chat_id = row['group_id']
            bot.send_photo(chat_id=chat_id, photo=image_url)

def create_poll():
    question = "What's your favorite color?"
    options = ["Red", "Blue", "Green", "Yellow"]
    bot.send_poll(chat_id='@thehackitect_feedbacks', question=question, options=options, is_anonymous=False, allows_multiple_answers=False)

def add_users_to_group():
    rows = worksheet.get_all_records()
    for i, row in enumerate(rows, start=2):  # start=2 to account for the header row
        if row['status'] == 'new':
            user_id = row['user_id']
            group_id = row['group_id']
            bot.send_message(chat_id=group_id, text=f"Welcome {user_id}!", parse_mode='Markdown')
            # Update the status in the sheet to avoid re-adding
            worksheet.update_cell(i, list(row.keys()).index('status') + 1, 'added')  # +1 because update_cell is 1-indexed

# Scheduling tasks
schedule.every().day.at("10:00").do(post_prompts)  # Schedule for 10 AM every day
schedule.every().day.at("11:00").do(create_poll)   # Schedule for 11 AM every day

while True:
    asyncio.run(send_results())
    add_users_to_group()
    schedule.run_pending()
    time.sleep(60)  # Check every 60 seconds for new data and scheduled tasks
