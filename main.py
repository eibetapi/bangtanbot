import asyncio
import time
import random
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

BOT_TOKEN_TICKET = 8627731148:AAFWE_a7IpMVp33KexLtCLVtzzsM6LEQ86E
BOT_TOKEN_BLUE = 8444232711:AAHnxO392HDQSLps11ztCWpq5LO7xr6jBec

CHAT_ID = -1003972186058
ADMIN_ID = 1407508561

bot_ticket = Bot(token=BOT_TOKEN_TICKET)
bot_blue = Bot(token=BOT_TOKEN_BLUE)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# =========================
# UPTIME / CONTADORES
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

    text = f"""👾•°•°• Central Wootteo de Controle •°•°•👾

🟢 Status: ONLINE
⏱️ Uptime: {get_uptime()}
🔄 Reconexão: {last_reconnect}

🎟️ Ticketmaster
📊 Checks: {check_ticket}
🚫 Bloqueios: {blocked_ticket}

🔵 Blue (Revenda)
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
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-28-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-30-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-31-10"
]

EVENTS_BLUE = [
    "https://buyticketbrasil.com/evento/bts%E2%80%932026worldtourarirang?data=1793242799000",
    "https://buyticketbrasil.com/evento/bts%E2%80%932026worldtourarirang?data=1793415599000",
    "https://buyticketbrasil.com/evento/bts%E2%80%932026worldtourarirang?data=1793501999000"
]

# =========================
# ESTADO
# =========================

last_state = {}

# =========================
# FETCH
# =========================

def fetch(url, is_ticket=True):
    global blocked_ticket, blocked_blue

    try:
        r = session.get(url, timeout=12)

        if r.status_code in [403, 429]:
            if is_ticket:
                blocked_ticket += 1
            else:
                blocked_blue += 1
            return None

        return r.text

    except:
        return None

# =========================
# PARSERS
# =========================

def parse_ticket(html):
    text = html.lower()
    h = hashlib.md5(text.encode()).hexdigest()
    return ("DISPONIVEL" if "esgotado" not in text else "ESGOTADO"), h

def parse_blue(html):
    soup = BeautifulSoup(html, "html.parser")

    link = None
    for a in soup.find_all("a", href=True):
        if "version-live" in a["href"]:
            link = a["href"]
            break

    if not link:
        return None, None, None, None

    text = soup.get_text(" ", strip=True).lower()
    h = hashlib.md5(text.encode()).hexdigest()

    valor = next((t for t in text.split() if "r$" in t), "N/A")

    if "meia" in text:
        cat = "Meia entrada"
    elif "inteira" in text:
        cat = "Inteira"
    elif "idoso" in text:
        cat = "Idoso"
    elif "pcd" in text:
        cat = "PCD"
    else:
        cat = "N/A"

    return link, valor, cat, h

# =========================
# ALERTAS
# =========================

def alert_ticket(url):
    bot_ticket.send_message(
        chat_id=CHAT_ID,
        text=f"🔥 ALERTA DE REPOSIÇÃO 🔥\n\n🎟️ {url}"
    )

def alert_blue(link, valor, categoria):
    msg = f"""🔵REVENDA BLUE🔵

🔗 {link}
💰 {valor}
🏷️ {categoria}
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 CLIQUE AQUI", url=link)]
    ])

    bot_blue.send_message(
        chat_id=CHAT_ID,
        text=msg,
        reply_markup=keyboard
    )

# =========================
# STATUS
# =========================

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🟢 BOT ATIVO\nuptime: {get_uptime()}"
    )

# =========================
# LOOP
# =========================

async def monitor():
    global last_reconnect, check_ticket, check_blue

    while True:
        try:

            for url in EVENTS_TICKET:
                check_ticket += 1
                html = fetch(url, True)
                if not html:
                    continue

                status_t, h = parse_ticket(html)

                if last_state.get(url) != h:
                    last_state[url] = h
                    if status_t == "DISPONIVEL":
                        alert_ticket(url)

            for url in EVENTS_BLUE:
                check_blue += 1
                html = fetch(url, False)
                if not html:
                    continue

                link, valor, cat, h = parse_blue(html)

                if link and last_state.get(url) != h:
                    last_state[url] = h
                    alert_blue(link, valor, cat)

            await update_panel()

            print("🟢 BOT RODANDO - OK")

            await asyncio.sleep(30)

        except Exception as e:
            print("ERRO:", e)
            last_reconnect = time.strftime("%H:%M:%S")

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

    # inicia bots
    await app_ticket.initialize()
    await app_blue.initialize()

    await app_ticket.start()
    await app_blue.start()

    # inicia polling (ESSENCIAL)
    await app_ticket.updater.start_polling()
    await app_blue.updater.start_polling()

    # roda monitor em paralelo
    asyncio.create_task(monitor())

    print("🔥 Bots online!")

    # mantém rodando
    await asyncio.Event().wait()

asyncio.run(main())