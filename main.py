if res:
            found=True
            active.append(res)
            msg += f"🪙 {res['symbol']}\n{res['type']}\n📍 ورود: {res['entry']:.4f}\n🛑 استاپ: {res['sl']:.4f}\n🎯 تیک پروفیت: {res['tp']:.4f}\n⚖️ RR: 1:2 | RSI: {res['rsi']:.1f}\n➖➖➖\n"
    except: pass
if found:
    send(msg)

# 3. گزارش آخر شب ساعت 23 به وقت ترکیه (20 به وقت UTC)
now_utc = datetime.utcnow()
if now_utc.hour == 20:
    total = wins + losses
    winrate = (wins/total*100) if total>0 else 0
    daily = f"📊 گزارش روزانه\n\nکل معامله: {total}\n✅ برد: {wins}\n❌ باخت: {losses}\n🏆 وین ریت: {winrate:.1f}%\n\n" + ("\n".join(history) if history else "امروز معامله‌ای بسته نشد.")
    send(daily)

# ذخیره کردن
with open("trades.json","w") as f:
    json.dump({"active": active, "wins": wins, "losses": losses, "history": history}, f)
