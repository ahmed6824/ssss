from flask import Flask, request, jsonify
from binance.client import Client
from binance.enums import *
import os

app = Flask(__name__)

# Load Binance API keys from environment variables
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# Initialize Binance Futures client
client = Client(API_KEY, API_SECRET)
client.FUTURES_URL = 'https://binance-docs.github.io/apidocs/futures/en/'

# Symbol and leverage (customize if needed)
SYMBOL = "SOLUSDT"
LEVERAGE = int(os.getenv("LEVERAGE", 10))

# Set leverage
client.futures_change_leverage(symbol=SYMBOL, leverage=LEVERAGE)

def calculate_quantity(symbol, leverage):
    """Calculate max quantity based on USDT balance and current price."""
    balance_info = client.futures_account_balance()
    usdt_balance = next(item for item in balance_info if item['asset'] == 'USDT')
    balance = float(usdt_balance['balance'])
    price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
    qty = (balance * leverage) / price
    return round(qty, 2)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook Received:", data)

    action = data.get('signal', '').lower()
    if action not in ["buy", "sell"]:
        return jsonify({"error": "Invalid signal"}), 400

    side = SIDE_BUY if action == "buy" else SIDE_SELL
    quantity = calculate_quantity(SYMBOL, LEVERAGE)

    try:
        order = client.futures_create_order(
            symbol=SYMBOL,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity,
            positionSide="BOTH"
        )
        return jsonify({"status": "success", "order": order}), 200
    except Exception as e:
        print("Order error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
