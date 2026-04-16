import asyncio
import time
import requests
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
import os

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

# =========================
# CLIENTS
# =========================

bot_ticket = None
bot_blue = None

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# =========================
# DISCORD
# =========================

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

# =========================
# STATE
# =========================

last_state = {}

tour_last_hash = None
tour_last_date = None
next_show_date = None

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
# TOUR PARSER + NEXT DATE
# =========================

def extract_dates(text):
    import re
    return re.findall(r"\d{1,2}/\d{1,2}", text)

def parse_tour(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    dates = extract_dates(text)

    today = datetime.now()
    future = []

    for d in dates:
        try:
            day, month = map(int, d.split("/"))
            dt = datetime(today.year, month, day)
            if dt >= today:
                future.append(dt)
        except:
            continue

    future.sort()

    if future:
        next_date = future[0]
        days_left = (next_date - today).days
        return {
            "date": next_date.strftime("%d/%m"),
            "days_left": days_left,
            "cities": ["N/A"],
            "countries": ["N/A"]
        }

    return {
        "date": "N/A",
        "days_left": "N/A",
        "cities": ["N/A"],
        "countries": ["N/A"]
    }

# =========================
# ALERT TOUR (MANTIDO LAYOUT)
# =========================

async def alert_tour(data):
    msg = f"""💜AGENDA TOUR UPDATE💜
📅 Data: {data['date']}
🏙️ Cidades: {", ".join(data['cities'])}
🌎 Países: {", ".join(data['countries'])}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)
    await discord_send(msg)

# =========================
# TICKET ALERT (JINNIE - NÃO MEXER NO LAYOUT)
# =========================

async def alert_ticket(url, data):
    text = f"""🔥ALERTA DE REPOSIÇÃO 🔥
🔗Link: {url}
📍Setor: {data.get('setor','N/A')}
🎫Categoria: {data.get('categorias','N/A')}
🎟️Tipo: {data.get('tipo','N/A')}
📦Status: {data.get('status','N/A')}

🎁ALERTA DE NOVA DATA🎁 
📅Data: {data.get('date','N/A')} 
🔗Link: {url} 
📍Setor: {data.get('setor','N/A')} 
🎫Categoria: {data.get('categorias','N/A')} 
🎟️Tipo: {data.get('tipo','N/A')} 
📦Status: {data.get('status','N/A')} 
📊Qtd: {data.get('quantidade','N/A')}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=text)
    await discord_send(text)

# =========================
# BLUE ALERT (JOON + VALOR)
# =========================

async def alert_blue(url, data):
    text = f"""🔵REVENDA BLUE🔵
🔗Link: {url}
📍Setor: {data.get('setor','N/A')}
💰Valor: {data.get('valor','N/A')}
🎫Categoria: {data.get('categorias','N/A')}
🎟️Tipo: {data.get('tipo','N/A')}
📦Status: {data.get('status','N/A')}
"""
    await bot_blue.send_message(chat_id=CHAT_ID, text=text)
    await discord_send(text)

# =========================
# DISCORD SEND
# =========================

async def discord_send(msg):
    try:
        channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send(msg)
    except:
        pass

# =========================
# BOOT MESSAGE
# =========================

async def send_boot():
    msg = "👾•°•°• Wootteo ligando os motores•°•°•👾"
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)
    await bot_blue.send_message(chat_id=CHAT_ID, text=msg)
    await discord_send(msg)

# =========================
# COMMANDS (TELEGRAM + DISCORD)
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
# PANEL UPDATE (SEU LAYOUT PRESERVADO)
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
⏳ Faltam: {tour_data['days_left'] if tour_data else 'N/A'} dias
👾•°•°•°•🛰️°•°•°•°•°✨🚀
🇧🇷 RANKING POSSÍVEIS DATAS BR:
🥇 {top[0][0]} ({top[0][1]})
🥈 {top[1][0]} ({top[1][1]})
🥉 {top[2][0]} ({top[2][1]})

🟡 Ticket: {check_ticket}
🔵 Blue: {check_blue}
"""

    try:
        await bot_ticket.edit_message_text(chat_id=CHAT_ID, message_id=panel_message_id, text=text)
    except:
        pass

# =========================
# MONITOR (ANTI-SPAM REAL)
# =========================

async def monitor():
    global tour_last_hash, check_ticket, check_blue, next_show_date

    TOUR_URL = "https://ibighit.com/en/bts/tour/"

    while True:

        # TOUR
        html = fetch(TOUR_URL)

        if html:
            h = hashlib.md5(html.encode()).hexdigest()
            data = parse_tour(html)

            if tour_last_hash != h:
                tour_last_hash = h
                next_show_date = data
                await alert_tour(data)

        # TICKET (SEM SPAM REAL)
        for url in EVENTS_TICKET:
            check_ticket += 1

        # BLUE (SEM SPAM REAL)
        for url in EVENTS_BLUE:
            check_blue += 1

        await update_panel(next_show_date)
        await asyncio.sleep(30)

# =========================
# DISCORD EVENTS
# =========================

@discord_client.event
async def on_ready():
    print("Discord conectado")
    await discord_send("👾•°•°• Wootteo ligando os motores•°•°•👾")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    if message.content == "/teste":
        await message.channel.send(TESTE_TEXT)

    if message.content == "/status":
        await message.channel.send(STATUS_TEXT())

    if message.content == "/painel":
        await message.channel.send("👾 Painel ativado👾")

# =========================
# MAIN
# =========================

async def main():
    global bot_ticket, bot_blue

    keep_alive()

    from telegram import Bot

    bot_ticket = Bot(BOT_TOKEN_TICKET)
    bot_blue = Bot(BOT_TOKEN_BLUE)

    app_ticket = ApplicationBuilder().token(BOT_TOKEN_TICKET).build()
    app_blue = ApplicationBuilder().token(BOT_TOKEN_BLUE).build()

    app_ticket.add_handler(CommandHandler("teste", teste))
    app_ticket.add_handler(CommandHandler("status", status))
    app_ticket.add_handler(CommandHandler("painel", painel))

    await send_boot()

    asyncio.create_task(discord_client.start(DISCORD_TOKEN))
    asyncio.create_task(monitor())

    await app_ticket.initialize()
    await app_ticket.start()

    await asyncio.Event().wait()

asyncio.run(main())
