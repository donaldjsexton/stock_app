from flask import Flask, render_template, jsonify, send_file
from stock_utils import update_stocks, get_latest_data, is_market_open
import csv
import os

app = Flask(__name__)

@app.route("/")
def index():
    market_open = is_market_open()
    latest_data = get_latest_data()
    return render_template("index.html", market_open=market_open, stocks=latest_data)

@app.route("/update")
def update():
    result = update_stocks()
    return jsonify({"status": "success", "details": result})

@app.route("/download")
def download():
    filename = "latest_data.csv"
    data = get_latest_data()
    with open(filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Symbol", "Open", "Close", "High", "Low", "Volume"])
        for row in data:
            writer.writerow([row[col] for col in ["Date", "Symbol", "Open", "Close", "High", "Low", "Volume"]])
    return send_file(filename, as_attachment=True)
    
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)