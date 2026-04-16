import asyncio
import time
import requests
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
import os
import re

import discord

from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from flask import Flask
from threading import Thread

# =========================
# KEEP ALIVE
# =========================

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

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

CHAT_ID = -1003972186058
ADMIN_ID = 1407508561

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# =========================
# LINKS
# =========================

TICKET_LINKS = [
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-28-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-30-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-31-10"
]

BLUE_LINKS = [
    "https://buyticketbrasil.com/evento/bts%E2%80%932026worldtourarirang"
]

BTS_URL = "https://ibighit.com/en/bts/tour/"

# =========================
# DISCORD
# =========================

intents = discord.Intents.default()
intents.message_content = True

discord_client = discord.Client(intents=intents)

async def discord_send(msg):
    try:
        channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send(msg)
    except:
        pass

# =========================
# STATE (ANTI-SPAM REAL)
# =========================

ticket_hash = {}
blue_hash = {}
bts_hash = None

boot_done = False

panel_message_id = None
panel_chat_id = None

panel_enabled = False

check_ticket = 0
check_blue = 0

start_time = time.time()

# =========================
# UPTIME
# =========================

def get_uptime():
    s = int(time.time() - start_time)
    return f"{s//3600}h {(s%3600)//60}m {s%60}s"

# =========================
# FETCH
# =========================

def fetch(url):
    try:
        return requests.get(url, timeout=10).text
    except:
        return None

# =========================
# PARSER
# =========================

def parse_tour(html):
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)

    date = re.findall(r"\d{1,2}/\d{1,2}/\d{4}", text)
    city = re.findall(r"[A-Z][a-z]+,\s?[A-Z]{2}", text)

    return {
        "date": date[0] if date else "N/A",
        "city": city[0] if city else "N/A"
    }

# =========================
# ALERTS (SEM MUDAR LAYOUT)
# =========================

async def alert_ticket(url):
    msg = f"""🔥ALERTA DE REPOSIÇÃO 🔥
🔗Link: {url}
📍Setor: N/A
🎫Categoria: N/A
🎟️Tipo: N/A
📦Status: ATUALIZADO

🎁ALERTA DE NOVA DATA🎁 
📅Data: N/A 
🔗Link: {url} 
📍Setor: N/A 
🎫Categoria: N/A 
🎟️Tipo: N/A 
📦Status: ATUALIZADO 
📊Qtd: N/A
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def alert_blue(url):
    msg = f"""🔵REVENDA BLUE🔵
🔗Link: {url}
📍Setor: N/A
💰Valor: N/A
🎫Categoria: N/A
🎟️Tipo: N/A
📦Status: ATUALIZADO
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def alert_bts(data):
    msg = f"""💜AGENDA TOUR UPDATE💜
📅 Data: {data['date']}
🏙️ Cidades: {data['city']}
🌎 Países: USA
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

# =========================
# BOOT (SEMPRE FIXO)
# =========================

async def send_boot():
    global boot_done

    msg = "👾•°•°• Wootteo ligando os motores•°•°•👾"

    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)
    await discord_send(msg)

    boot_done = True

# =========================
# TESTE (4 POSTS)
# =========================

async def teste(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await alert_ticket("https://test.com/ticket")
    await alert_ticket("https://test.com/ticket")
    await alert_blue("https://test.com/blue")
    await alert_bts({"date": "N/A", "city": "N/A"})

# =========================
# STATUS
# =========================

STATUS_TEXT = lambda: f"""🟢STATUS WOOTTEO°•°•°•°•👾
⏰ Uptime: {get_uptime()}
📊 Ticket Checks: {check_ticket}
📊 Blue Checks: {check_blue}
"""

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = STATUS_TEXT()
    await update.message.reply_text(msg)
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

# =========================
# PAINEL
# =========================

async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global panel_message_id, panel_chat_id, panel_enabled

    panel_enabled = True

    msg = await update.message.reply_text("👾 Painel ativado👾")
    panel_message_id = msg.message_id
    panel_chat_id = CHAT_ID

# =========================
# PANEL UPDATE
# =========================

async def update_panel(tour_data=None):
    global panel_message_id, panel_chat_id

    if not panel_enabled:
        return

    top = {"São Paulo": 0, "Rio de Janeiro": 0, "Curitiba": 0}

    text = f"""👾 CENTRAL WOOTTEO 👾

⏰ Uptime: {get_uptime()}

✈️ PRÓXIMAS DATAS:
🎫 Data: {tour_data['date'] if tour_data else 'N/A'}
📍 Local: {tour_data['city'] if tour_data else 'N/A'}

🇧🇷 RANKING:
🥇 São Paulo (0)
🥈 Rio de Janeiro (0)
🥉 Curitiba (0)

🟡 Ticket: {check_ticket}
🔵 Blue: {check_blue}
"""

    try:
        await bot_ticket.send_message(chat_id=panel_chat_id, text=text)
    except:
        pass

# =========================
# MONITOR (SEM SPAM)
# =========================

async def monitor():
    global ticket_hash, blue_hash, bts_hash, check_ticket, check_blue

    while True:

        # BOT START LOCK
        html = fetch(BTS_URL)

        if html:
            h = hashlib.md5(html.encode()).hexdigest()
            data = parse_tour(html)

            if bts_hash != h and boot_done:
                bts_hash = h
                await alert_bts(data)

        for url in TICKET_LINKS:
            html = fetch(url)
            if not html:
                continue

            h = hashlib.md5(html.encode()).hexdigest()

            if ticket_hash.get(url) != h:
                ticket_hash[url] = h
                if boot_done:
                    await alert_ticket(url)

        for url in BLUE_LINKS:
            html = fetch(url)
            if not html:
                continue

            h = hashlib.md5(html.encode()).hexdigest()

            if blue_hash.get(url) != h:
                blue_hash[url] = h
                if boot_done:
                    await alert_blue(url)

        check_ticket += 1
        check_blue += 1

        await asyncio.sleep(30)

# =========================
# MAIN
# =========================

async def main():

    keep_alive()

    global bot_ticket

    bot_ticket = Bot(os.getenv("BOT_TOKEN_TICKET"))

    app_ticket = ApplicationBuilder().token(os.getenv("BOT_TOKEN_TICKET")).build()

    app_ticket.add_handler(CommandHandler("teste", teste))
    app_ticket.add_handler(CommandHandler("status", status))
    app_ticket.add_handler(CommandHandler("painel", painel))

    await app_ticket.initialize()
    await app_ticket.start()

    await send_boot()

    asyncio.create_task(discord_client.start(DISCORD_TOKEN))
    asyncio.create_task(monitor())

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())