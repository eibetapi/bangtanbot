import asyncio
import time
import requests
import hashlib
from bs4 import BeautifulSoup
import os

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# KEEP ALIVE
# =========================

from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bots rodando"

def run_web():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run_web).start()

# =========================
# CONFIG
# =========================

BOT_TOKEN_TICKET = os.getenv("BOT_TOKEN_TICKET")
BOT_TOKEN_BLUE = os.getenv("BOT_TOKEN_BLUE")

CHAT_ID = -1003972186058
ADMIN_ID = 1407508561

bot_ticket = Bot(token=BOT_TOKEN_TICKET)
bot_blue = Bot(token=BOT_TOKEN_BLUE)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# =========================
# UPTIME
# =========================

start_time = time.time()
last_reconnect = "Nenhuma"

check_ticket = 0
check_blue = 0

blocked_ticket = 0
blocked_blue = 0

def get_uptime():
    s = int(time.time() - start_time)
    return f"{s//3600}h {(s%3600)//60}m {s%60}s"

# =========================
# PAINEL
# =========================

panel_message_id = None

async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global panel_message_id

    msg = await update.message.reply_text(
        "👾•°•°• Painel Wootteo iniciado•°•°•👾"
    )

    panel_message_id = msg.message_id

async def update_panel():
    global panel_message_id

    if not panel_message_id:
        return

    text = f"""👾•°•°• Central Wootteo •°•°•👾

🟢 Status: ONLINE
⏱️ Uptime: {get_uptime()}
🔄 Reconexão: {last_reconnect}

🎟️ Ticketmaster
📊 Checks: {check_ticket}
🚫 Bloqueios: {blocked_ticket}

🔵 Blue
📊 Checks: {check_blue}
🚫 Bloqueios: {blocked_blue}
"""

    try:
        await bot_ticket.edit_message_text(
            chat_id=CHAT_ID,
            message_id=panel_message_id,
            text=text
        )
    except:
        pass

# =========================
# LINKS
# =========================

EVENTS_TICKET = [
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-28-10"
]

EVENTS_BLUE = [
    "https://buyticketbrasil.com/evento/bts%E2%80%932026worldtourarirang?data=1793242799000"
]

last_state = {}

# =========================
# FETCH
# =========================

def fetch(url):
    try:
        return session.get(url, timeout=10).text
    except:
        return None

# =========================
# ALERTAS
# =========================

def alert_ticket(url):
    bot_ticket.send_message(
        chat_id=CHAT_ID,
        text=f"🔥 ALERTA\n{url}"
    )

def alert_blue(link):
    bot_blue.send_message(
        chat_id=CHAT_ID,
        text=f"🔵 {link}"
    )

# =========================
# STATUS
# =========================

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🟢 BOT ONLINE\nUptime: {get_uptime()}"
    )

# =========================
# MONITOR
# =========================

async def monitor():
    global check_ticket, check_blue

    while True:
        try:
            for url in EVENTS_TICKET:
                check_ticket += 1
                html = fetch(url)
                if html and url not in last_state:
                    last_state[url] = True
                    alert_ticket(url)

            for url in EVENTS_BLUE:
                check_blue += 1
                html = fetch(url)
                if html and url not in last_state:
                    last_state[url] = True
                    alert_blue(url)

            await update_panel()
            await asyncio.sleep(30)

        except Exception as e:
            print("ERRO:", e)

# =========================
# MAIN
# =========================

async def main():
    keep_alive()

    app_ticket = ApplicationBuilder().token(BOT_TOKEN_TICKET).build()
    app_blue = ApplicationBuilder().token(BOT_TOKEN_BLUE).build()

    for app in [app_ticket, app_blue]:
        app.add_handler(CommandHandler("status", status))
        app.add_handler(CommandHandler("painel", painel))

    # roda monitor
    asyncio.create_task(monitor())

    print("🔥 Bots iniciando...")

    # roda bots corretamente
    asyncio.create_task(app_ticket.run_polling())
    asyncio.create_task(app_blue.run_polling())

    # mantém vivo
    await asyncio.Event().wait()

asyncio.run(main())

