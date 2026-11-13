import os
import requests

TOKEN = os.getenv("BOTTOKEN")
CHATID = os.getenv("CHATID")

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = {"chat_id": CHATID, "text": "سلام ابی! رباتت کار کرد ✅"}
r = requests.get(url, params=data)
print(r.text)
