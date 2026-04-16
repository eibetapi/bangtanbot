import asyncio
import time
import requests
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
import os
import re

import discord

from telegram import Update
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
BOT_TOKEN_BLUE = os.getenv("BOT_TOKEN_BLUE")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

CHAT_ID = -1003972186058
ADMIN_ID = 1407508561

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

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
# STATE
# =========================

last_state = {}

tour_last_hash = None
tour_last_event = None

check_ticket = 0
check_blue = 0

panel_message_id = None

start_time = time.time()

br_rank = {
    "São Paulo": 0,
    "Rio de Janeiro": 0,
    "Curitiba": 0,
    "Belo Horizonte": 0,
    "Brasília": 0,
}

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
        return session.get(url, timeout=10).text
    except:
        return None

# =========================
# TOUR PARSER (REAL DATA FIX)
# =========================

def parse_tour(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    # 🔥 DATA US FORMAT (04/25/2026)
    date_match = re.search(r"\d{1,2}/\d{1,2}/\d{4}", text)

    event_date = None
    days_left = "N/A"

    if date_match:
        event_date = datetime.strptime(date_match.group(), "%m/%d/%Y")
        days_left = (event_date - datetime.now()).days

    # 🌎 CIDADE (ex: Tampa, FL)
    city_match = re.search(r"([A-Z][a-z]+,\s?[A-Z]{2})", text)

    city = city_match.group() if city_match else "N/A"

    return {
        "date": event_date.strftime("%m/%d/%Y") if event_date else "N/A",
        "city": city,
        "days_left": days_left
    }

# =========================
# ALERT TOUR (SÓ QUANDO MUDAR)
# =========================

async def alert_tour(data):
    msg = f"""💜AGENDA TOUR UPDATE💜
📅 Data: {data['date']}
🏙️ Cidades: {data['city']}
🌎 Países: USA
"""
    await discord_send(msg)

# =========================
# ALERT TICKET (SEU LAYOUT 100%)
# =========================

async def alert_ticket(url, data):
    text = f"""🔥ALERTA DE REPOSIÇÃO 🔥
🔗Link: {url}
📍Setor: N/A
🎫Categoria: N/A
🎟️Tipo: N/A
📦Status: N/A

🎁ALERTA DE NOVA DATA🎁 
📅Data: N/A 
🔗Link: {url} 
📍Setor: N/A 
🎫Categoria: N/A 
🎟️Tipo: N/A 
📦Status: N/A 
📊Qtd: N/A
"""
    await discord_send(text)

# =========================
# ALERT BLUE (SEU LAYOUT)
# =========================

async def alert_blue(url, data):
    text = f"""🔵REVENDA BLUE🔵
🔗Link: {url}
📍Setor: N/A
💰Valor: N/A
🎫Categoria: N/A
🎟️Tipo: N/A
📦Status: N/A
"""
    await discord_send(text)

# =========================
# BOOT
# =========================

async def send_boot():
    msg = "👾•°•°• Wootteo ligando os motores•°•°•👾"
    await discord_send(msg)

# =========================
# COMMANDS (NÃO MEXI NO TEXTO)
# =========================

TESTE_TEXT = """🌊TESTE🌊
📅Data: 13/06
🔗Link: https://ibighit.com/en/bts/tour/
📍Setor: Porão da Big Hit
🎫Categoria: Army
🎟️Tipo: OT7
📦Status: disponível
📊Qtd: 07
"""

STATUS_TEXT = lambda: f"""🟢🔮STATUS WOOTTEO🔮
⏰ Uptime: {get_uptime()}
📊 Ticket Checks: {check_ticket}
📊 Blue Checks: {check_blue}
"""

async def teste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TESTE_TEXT)
    await discord_send(TESTE_TEXT)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(STATUS_TEXT())
    await discord_send(STATUS_TEXT())

async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global panel_message_id
    msg = await update.message.reply_text("👾 Painel ativado👾")
    panel_message_id = msg.message_id

# =========================
# PANEL UPDATE (COM DATA REAL)
# =========================

async def update_panel(tour_data=None):
    global panel_message_id

    if not panel_message_id:
        return

    top = sorted(br_rank.items(), key=lambda x: x[1], reverse=True)

    text = f"""👾 CENTRAL WOOTTEO 👾

⏰ Uptime: {get_uptime()}

✈️ PRÓXIMAS DATAS:
🎫 Data: {tour_data['date'] if tour_data else 'N/A'}
📍 Local: {tour_data['city'] if tour_data else 'N/A'}
⏳ Faltam: {tour_data['days_left'] if tour_data else 'N/A'} dias

🇧🇷 RANKING POSSÍVEIS DATAS BR:
🥇 {top[0][0]} ({top[0][1]})
🥈 {top[1][0]} ({top[1][1]})
🥉 {top[2][0]} ({top[2][1]})

🟡 Ticket: {check_ticket}
🔵 Blue: {check_blue}
"""

    try:
        await discord_send(text)
    except:
        pass

# =========================
# MONITOR (SEM SPAM REAL)
# =========================

async def monitor():
    global tour_last_hash, tour_last_event

    TOUR_URL = "https://ibighit.com/en/bts/tour/"

    while True:

        html = fetch(TOUR_URL)

        if html:
            h = hashlib.md5(html.encode()).hexdigest()
            data = parse_tour(html)

            if tour_last_hash != h:
                tour_last_hash = h

                # só dispara se evento realmente mudou
                if tour_last_event != data["date"]:
                    tour_last_event = data["date"]
                    await alert_tour(data)

                await update_panel(data)

        await asyncio.sleep(30)

# =========================
# MAIN
# =========================

async def main():
    keep_alive()

    from telegram import Bot

    global bot_ticket, bot_blue
    bot_ticket = Bot(os.getenv("BOT_TOKEN_TICKET"))
    bot_blue = Bot(os.getenv("BOT_TOKEN_BLUE"))

    app_ticket = ApplicationBuilder().token(os.getenv("BOT_TOKEN_TICKET")).build()
    app_blue = ApplicationBuilder().token(os.getenv("BOT_TOKEN_BLUE")).build()

    app_ticket.add_handler(CommandHandler("teste", teste))
    app_ticket.add_handler(CommandHandler("status", status))
    app_ticket.add_handler(CommandHandler("painel", painel))

    await send_boot()

    asyncio.create_task(discord_client.start(os.getenv("DISCORD_TOKEN")))
    asyncio.create_task(monitor())

    await app_ticket.initialize()
    await app_ticket.start()

    await asyncio.Event().wait()

asyncio.run(main())