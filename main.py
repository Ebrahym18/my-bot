import os, requests, json
from datetime import datetime

TOKEN = os.getenv("BOTTOKEN")
CHATID = os.getenv("CHATID")

def send(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHATID, "text": text})

def get_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    return float(requests.get(url).json()['price'])

def get_top_coins():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url).json()
    pairs = [d for d in data if d['symbol'].endswith('USDT') and 'UP' not in d['symbol'] and 'DOWN' not in d['symbol']]
    sorted_coins = sorted(pairs, key=lambda x: abs(float(x['priceChangePercent'])), reverse=True)
    top = ['BTCUSDT', 'ETHUSDT']
    for c in sorted_coins:
        if c['symbol'] not in top:
            top.append(c['symbol'])
        if len(top) >= 6:
            break
    return top

def analyze(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=250"
    klines = requests.get(url).json()
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
        return {"symbol": symbol, "type": "LONG 🟢", "entry": entry, "sl": sl, "tp": tp, "rsi": rsi}
    if price < ema50 < ema200 and 35 < rsi < 70:
        entry = price
        sl = price+(atr*1.5)
        tp = price-((sl-entry)*2)
        return {"symbol": symbol, "type": "SHORT 🔴", "entry": entry, "sl": sl, "tp": tp, "rsi": rsi}
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
        history.append(f"✅ {trade['symbol']} تیپی زد 🎯")
        send(f"🎯 تیپی خورد!\n🪙 {trade['symbol']} {trade['type']}\nورود: {trade['entry']:.4f}\nخروج: {price:.4f}\nسود: +2R ✅")
    elif hit_sl:
        losses += 1
        history.append(f"❌ {trade['symbol']} استاپ خورد 🛑")
        send(f"🛑 استاپ خورد!\n🪙 {trade['symbol']} {trade['type']}\nورود: {trade['entry']:.4f}\nخروج: {price:.4f}\nضرر: -1R ❌")
    else:
        new_active.append(trade)
active = new_active

coins = get_top_coins()
msg = "📈 سیگنال‌های جدید (1 ساعته):\n\n"
found = False
for coin in coins:
    if any(t['symbol']==coin for t in active):
        continue
    res = analyze(coin)
    if res:
        found = True
        active.append(res)
        msg += f"🪙 {res['symbol']}\n{res['type']}\n📍 ورود: {res['entry']:.4f}\n🛑 استاپ: {res['sl']:.4f}\n🎯 تیک پروفیت: {res['tp']:.4f}\n⚖️ RR: 1:2 | RSI: {res['rsi']:.1f}\n➖➖➖\n"
if found:
    send(msg) now_utc = datetime.utcnow()
ifnow_utc = datetime.utcnow()
if now_utc.hour == 20:
    total = wins + losses
    winrate = (wins/total*100) if total>0 else 0
    daily = f"📊 گزارش روزانه..."
    send(daily)
