import requests
import os

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHATID"]
BASE = "https://data-api.binance.vision"

def send(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHATID, "text": text}, timeout=10)

def analyze(symbol):
    url = f"{BASE}/api/v3/klines?symbol={symbol}&interval=1h&limit=250"
    klines = requests.get(url, timeout=10).json()
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
    gains=[]; losses_list=[]
    for i in range(1,15):
        diff = closes[-i] - closes[-i-1]
        if diff>0: gains.append(diff)
        else: losses_list.append(abs(diff))
    avg_gain = sum(gains)/14 if gains else 0.01
    avg_loss = sum(losses_list)/14 if losses_list else 0.01
    rsi = 100 - (100/(1+avg_gain/avg_loss))
    atr = sum([highs[i]-lows[i] for i in range(-14,0)])/14
    if price > ema50 > ema200 and 30 < rsi < 65:
        entry=price; sl=price-(atr*1.5); tp=price+((entry-sl)*2)
        return f"🪙 {symbol}\nLONG 🟢\n📍 ورود: {entry:.4f}\n🛑 استاپ: {sl:.4f}\n🎯 تیپی: {tp:.4f}\nRSI: {rsi:.1f}"
    elif price < ema50 < ema200 and 35 < rsi < 70:
        entry=price; sl=price+(atr*1.5); tp=price-((sl-entry)*2)
        return f"🪙 {symbol}\nSHORT 🔴\n📍 ورود: {entry:.4f}\n🛑 استاپ: {sl:.4f}\n🎯 تیپی: {tp:.4f}\nRSI: {rsi:.1f}"
    return None

coins = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"]
msg = "📈 سیگنال‌های جدید:\n\n"
found = False
for coin in coins:
    try:
        res = analyze(coin)
        if res:
            found = True
            msg += res + "\n➖➖➖\n"
    except: pass

if found:
    send(msg)
else:
    send("ربات چک کرد، سیگنال جدید نبود ✅")
