import os
import requests
import gspread
from dotenv import load_dotenv
from datetime import datetime, time
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

ALPHA_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
STOCK_SYMBOLS = os.getenv("STOCK_SYMBOLS", "AAPL,MSFT,GOOGL").split(",")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Stock Data")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(GOOGLE_SHEET_NAME).sheet1

def ensure_headers():
    expected = ["Date", "Symbol", "Open", "Close", "High", "Low", "Volume"]
    headers = sheet.row_values(1)
    if headers != expected:
        sheet.insert_row(expected, 1)

def fetch_stock_data(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_API_KEY}"
    response = requests.get(url)
    data = response.json()
    time_series = data.get("Time Series (Daily)")
    if not time_series:
        raise ValueError(f"Failed to retrieve data for {symbol}: {data.get('Note') or data}")
    latest_date = max(time_series.keys())
    daily_data = time_series[latest_date]
    return {
        "date": latest_date,
        "symbol": symbol,
        "open": daily_data["1. open"],
        "close": daily_data["4. close"],
        "high": daily_data["2. high"],
        "low": daily_data["3. low"],
        "volume": daily_data["5. volume"]
    }

def row_needs_update(date, symbol, new_data):
    all_records = sheet.get_all_records()
    for i, row in enumerate(all_records, start=2):
        if row["Date"] == date and row["Symbol"] == symbol:
            for key in ["Open", "Close", "High", "Low", "Volume"]:
                sheet_val = str(row.get(key, "")).strip()
                api_val = str(new_data[key.lower()]).strip()
                if sheet_val != api_val:
                    return (i, True)
            return (i, False)
    return (None, True)

def update_stocks():
    ensure_headers()
    results = []
    for symbol in STOCK_SYMBOLS:
        data = fetch_stock_data(symbol)
        row_number, needs_update = row_needs_update(data["date"], data["symbol"], data)
        if row_number is None:
            sheet.append_row([data["date"], data["symbol"], data["open"], data["close"], data["high"], data["low"], data["volume"]])
            results.append(f"Added {symbol}")
        elif needs_update:
            sheet.update(f"A{row_number}:G{row_number}", [[data["date"], data["symbol"], data["open"], data["close"], data["high"], data["low"], data["volume"]]])
            results.append(f"Updated {symbol}")
        else:
            results.append(f"{symbol} up-to-date")
    return results

def get_latest_data():
    rows = sheet.get_all_records()
    return rows

def is_market_open():
    now = datetime.utcnow()
    open_time = time(13, 30)
    close_time = time(20, 0)
    return now.weekday() < 5 and open_time <= now.time() <= close_time