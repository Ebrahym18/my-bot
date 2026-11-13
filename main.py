import os
import requests
import json
TOKEN = os.getenv("BOTTOKEN")
CHATID = os.getenv("CHATID")
BASE = "https://data-api.binance.vision"
def send(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHATID, "text": text})
def get_price(symbol):
    url = BASE + f"/api/v3/ticker/price?symbol={symbol}"
    return float(requests.get(url).json()['price'])
def get_top_coins():
    return ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT']
def analyze(symbol):
    url = BASE + f"/api/v3/klines?symbol={symbol}&interval=1h&limit=250"
    klines = requests.get(url).json()
    if not isinstance(klines, list):
        return None
    if len(klines) < 210:
        return None
    closes = [float(k[4]) for k in klines]
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    price = closes[-1]
    def ema(data, period):
        k = 2/(period+1)
        e = data[0]
        for p in data[1:]:
            e = p*k + e*(1-k)
        return e
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)
    gains = []
    losses_list = []
    for i in range(1,15):
        diff = closes[-i] - closes[-i-1]
        if diff > 0:
            gains.append(diff)
        else:
            losses_list.append(abs(diff))
    avg_gain = sum(gains)/14 if gains else 0.01
    avg_loss = sum(losses_list)/14 if losses_list else 0.01
    rsi = 100 - (100/(1+avg_gain/avg_loss))
    atr = sum([highs[i]-lows[i] for i in range(-14,0)])/14
    if price > ema50 > ema200 and 30 < rsi < 65:
        entry = price
        sl = price-(atr*1.5)
        tp = price+((entry-sl)*2)
        return {"symbol": symbol, "type": "LONG", "entry": entry, "sl": sl, "tp": tp, "rsi": rsi}
    if price < ema50 < ema200 and 35 < rsi < 70:
        entry = price
        sl = price+(atr*1.5)
        tp = price-((sl-entry)*2)
        return {"symbol": symbol, "type": "SHORT", "entry": entry, "sl": sl, "tp": tp, "rsi": rsi}
    return None
active = []
wins = 0
losses = 0
history = []
if os.path.exists("trades.json"):
    with open("trades.json") as f:
        data = json.load(f)
        active = data.get("active", [])
        wins = data.get("wins", 0)
        losses = data.get("losses", 0)
        history = data.get("history", [])
new_active = []
for trade in active:
    price = get_price(trade['symbol'])
    hit_tp = False
    hit_sl = False
    if "LONG" in trade['type']:
        if price >= trade['tp']:
            hit_tp = True
        if price <= trade['sl']:
            hit_sl = True
    else:
        if price <= trade['tp']:
            hit_tp = True
        if price >= trade['sl']:
            hit_sl = True
    if hit_tp:
        wins += 1
        history.append("WIN " + trade['symbol'])
        send("✅ حد سود خورد " + trade['symbol'] + " - برد")
    elif hit_sl:
        losses += 1
        history.append("LOSS " + trade['symbol'])
        send("❌ حد ضرر خورد " + trade['symbol'] + " - باخت")
    else:
        new_active.append(trade)
active = new_active
coins = get_top_coins()
msg = "📊 سیگنال جدید (تایم 1 ساعته):\n\n"
found = False
for coin in coins:
    if any(t['symbol']==coin for t in active):
        continue
    res = analyze(coin)
    if res:
        found = True
        active.append(res)
        if res['type'] == "LONG":
            typ = "🟢 خرید (LONG)"
        else:
            typ = "🔴 فروش (SHORT)"
        msg += "🪙 " + res['symbol'] + " " + typ + "\nورود: " + str(round(res['entry'],4)) + "\nحد ضرر: " + str(round(res['sl'],4)) + "\nحد سود: " + str(round(res['tp'],4)) + "\nRSI: " + str(round(res['rsi'],1)) + "\n\n"
if found:
    send(msg)
with open("trades.json","w") as f:
    json.dump({"active": active, "wins": wins, "losses": losses, "history": history}, f)
