import os
import requests
import gspread
import logging
from dotenv import load_dotenv
from datetime import datetime, time
from oauth2client.service_account import ServiceAccountCredentials

# Setup logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

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
        logging.info("Inserting headers into sheet.")
        sheet.insert_row(expected, 1)

def fetch_stock_data(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={ALPHA_API_KEY}&outputsize=compact"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        series = data.get("Time Series (5min)")
        if not series:
            raise ValueError(f"No intraday data for {symbol}: {data.get('Note') or data}")
        latest_time = max(series.keys())  # e.g., '2025-04-04 15:35:00'
        values = series[latest_time]
        logging.info(f"Fetched intraday data for {symbol} at {latest_time}")
        return {
            "date": latest_time.split()[0],  # keep only date
            "symbol": symbol,
            "open": values["1. open"],
            "close": values["4. close"],
            "high": values["2. high"],
            "low": values["3. low"],
            "volume": values["5. volume"]
        }
    except Exception as e:
        logging.error(f"Failed intraday fetch for {symbol}: {e}")
        raise


def row_needs_update(date, symbol, new_data):
    all_records = sheet.get_all_records()
    for i, row in enumerate(all_records, start=2):
        if row["Date"] == date and row["Symbol"] == symbol:
            for key in ["Open", "Close", "High", "Low", "Volume"]:
                sheet_val = str(row.get(key, "")).strip()
                api_val = str(new_data[key.lower()]).strip()
                if sheet_val != api_val:
                    logging.info(f"Data mismatch for {symbol} on {date} in column {key}")
                    return (i, True)
            return (i, False)
    return (None, True)

def update_stocks():
    ensure_headers()
    results = []
    all_records = sheet.get_all_records()
    row_lookup = {
        (row["Date"].strip(), row["Symbol"].strip()): i + 2
        for i, row in enumerate(all_records)
    }

    for symbol in STOCK_SYMBOLS:
        try:
            data = fetch_stock_data(symbol)
            row_values = [
                data["date"], data["symbol"],
                data["open"], data["close"],
                data["high"], data["low"], data["volume"]
            ]
            key = (data["date"], data["symbol"])
            if key in row_lookup:
                sheet.update(f"A{row_lookup[key]}:G{row_lookup[key]}", [row_values])
                logging.info(f"Overwrote row {row_lookup[key]} for {symbol}")
                results.append(f"Overwrote {symbol}")
            else:
                sheet.append_row(row_values)
                logging.info(f"Appended new row for {symbol}")
                results.append(f"Added {symbol}")
        except Exception as e:
            logging.error(f"Error updating {symbol}: {e}")
            results.append(f"Error with {symbol}: {e}")
    return results

def get_latest_data():
    try:
        rows = sheet.get_all_records()
        logging.info(f"Retrieved {len(rows)} rows from sheet.")
        return rows
    except Exception as e:
        logging.error(f"Error retrieving data from sheet: {e}")
        return []

def is_market_open():
    now = datetime.utcnow()
    open_time = time(13, 30)
    close_time = time(20, 0)
    is_open = now.weekday() < 5 and open_time <= now.time() <= close_time
    logging.info(f"Market open: {is_open}")
    return is_open
