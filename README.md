# 🖥️ Stock Tracker Web App with UI

This Dockerized Flask app allows you to fetch stock data, display it in a browser, check market status, and download the data as CSV.

## Features
- Beautiful Bootstrap UI
- Market open/closed indicator (NYSE hours, UTC)
- Manual update button
- CSV download button
- Auto headers, deduplication, and update logic
- Runs in Docker

## Setup
1. Add your `.env` file:
```
ALPHA_VANTAGE_API_KEY=your_key
STOCK_SYMBOLS=AAPL,MSFT,GOOGL
GOOGLE_SHEET_NAME=Stock Data
```

2. Add your `credentials.json` (Google Service Account)

3. Build and run:
```bash
docker build -t stock-ui .
docker run -p 5000:5000 --env-file .env -v $(pwd)/credentials.json:/app/credentials.json stock-ui
```

4. Visit http://localhost:5000

Enjoy!