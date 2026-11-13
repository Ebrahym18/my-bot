import requests, time, os

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
BASE = "https://data-api.binance.vision"

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=20)
    except Exception as e:
        print("Send error:", e)

def get_symbols():
    try:
        r = requests.get(f"{BASE}/api/v3/exchangeInfo", timeout=20).json()
        syms = []
        for s in r["symbols"]:
            if s["quoteAsset"] == "USDT" and s["status"] == "TRADING":
                syms.append(s["symbol"])
        return syms[:100]
    except:
        return ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","MATICUSDT"]

def get_klines(symbol):
    try:
        r = requests.get(f"{BASE}/api/v3/klines", params={"symbol": symbol, "interval": "1h", "limit": 100}, timeout=20).json()
        closes = [float(x[4]) for x in r]
        return closes
    except:
        return []

def rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        d = prices[i] - prices[i-1]
        if d > 0:
            gains.append(d)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-d)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def scan():
    print("Scanning...")
    symbols = get_symbols()
    found = False
    for sym in symbols:
        try:
            closes = get_klines(sym)
            if len(closes) < 50:
                continue
            price = closes[-1]
            r = rsi(closes)
            ma50 = sum(closes[-50:]) / 50
            ma20 = sum(closes[-20:]) / 20
            signal = None
            if r < 30 and price > ma50:
                signal = "LONG - BUY"
                entry = price
                sl = price * 0.98
                tp = price * 1.04
            elif r > 70 and price < ma50:
                signal = "SHORT - SELL"
                entry = price
                sl = price * 1.02
                tp = price * 0.96
            if signal:
                found = True
                msg = f"COIN: {sym}\n{signal}\nEntry: {round(entry,4)}\nStop: {round(sl,4)}\nTarget: {round(tp,4)}\nRisk Reward: 1 : 2\nRSI: {round(r,1)}\nMA20: {round(ma20,2)} | MA50: {round(ma50,2)}"
                send(msg)
                print("Sent:", sym)
                time.sleep(1)
        except Exception as e:
            print("Error:", sym, e)
    if not found:
        send("Scan done - No good setup now, will check again in 1 hour.")

send("Bot is ON! I will scan every 1 hour.")
while True:
    scan()
    print("Waiting 1 hour...")
    time.sleep(3600)
