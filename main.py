import asyncio
import time
import requests
import hashlib
from bs4 import BeautifulSoup
import os

import discord

from telegram import Bot, Update
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

bot_ticket = Bot(token=BOT_TOKEN_TICKET)
bot_blue = Bot(token=BOT_TOKEN_BLUE)
bot_admin = Bot(token=BOT_TOKEN_TICKET)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# =========================
# DISCORD
# =========================

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

async def send_discord(msg):
    try:
        channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send(msg)
    except:
        pass

# =========================
# UPTIME
# =========================

start_time = time.time()

def get_uptime():
    s = int(time.time() - start_time)
    return f"{s//3600}h {(s%3600)//60}m {s%60}s"

# =========================
# LINKS
# =========================

EVENTS_TICKET = [
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-28-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-30-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-31-10"
]

EVENTS_BLUE = [
    "https://buyticketbrasil.com/evento/bts%E2%80%932026worldtourarirang?data=1793242799000"
]

TOUR_URL = "https://ibighit.com/en/bts/tour/"

# =========================
# STATE
# =========================

last_state = {}

tour_last_hash = None
tour_last_data = None

check_ticket = 0
check_blue = 0

panel_message_id = None

br_rank = {
    "São Paulo": 0,
    "Rio de Janeiro": 0,
    "Curitiba": 0,
    "Belo Horizonte": 0,
    "Brasília": 0,
}

# =========================
# FETCH
# =========================

def fetch(url):
    try:
        return session.get(url, timeout=10).text
    except:
        return None

# =========================
# PARSE TOUR
# =========================

def parse_tour(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    date = "N/A"

    return {
        "date": date,
        "cities": ["N/A"],
        "countries": ["N/A"]
    }

# =========================
# ALERT TOUR (NÃO MEXIDO NO LAYOUT)
# =========================

async def alert_tour(data):
    msg = f"""💜AGENDA TOUR UPDATE💜
📅 Data: {data['date']}
🏙️ Cidades: {", ".join(data['cities'])}
🌎 Países: {", ".join(data['countries'])}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)
    await send_discord(msg)

# =========================
# ALERT TICKET (JINNIE - NÃO MEXIDO)
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
    await send_discord(text)

# =========================
# ALERT BLUE (JOON - COM VALOR)
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
    await send_discord(text)

# =========================
# BOOT MESSAGE
# =========================

async def send_boot():
    msg = "👾•°•°• Wootteo ligando os motores•°•°•👾"
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)
    await bot_blue.send_message(chat_id=CHAT_ID, text=msg)
    await bot_admin.send_message(chat_id=ADMIN_ID, text=msg)
    await send_discord(msg)

# =========================
# COMMANDS
# =========================

async def teste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """🌊TESTE🌊
📅Data: 13/06
🔗Link: https://ibighit.com/en/bts/tour/
📍Setor: Porão da Big Hit
🎫Categoria: Army
🎟️Tipo: OT7
📦Status: disponível
📊Qtd: 07
"""
    await update.message.reply_text(text)
    await send_discord(text)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"""🟢🔮STATUS WOOTTEO🔮
⏰ Uptime: {get_uptime()}
📊 Ticket Checks: {check_ticket}
📊 Blue Checks: {check_blue}
"""
    await update.message.reply_text(msg)
    await send_discord(msg)

async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global panel_message_id
    msg = await update.message.reply_text("👾 Painel ativado👾")
    panel_message_id = msg.message_id

# =========================
# UPDATE PANEL
# =========================

async def update_panel(tour_data=None):
    global panel_message_id

    if not panel_message_id:
        return

    text = f"""👾 CENTRAL WOOTTEO 👾

⏰ Uptime: {get_uptime()}

🌍 PRÓXIMA DATA: {tour_data['date'] if tour_data else 'N/A'}
🏙️ CIDADES: {", ".join(tour_data['cities']) if tour_data else 'N/A'}

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
    global tour_last_hash, tour_last_data, check_ticket, check_blue

    while True:

        # TOUR BTS (ANTI-SPAM DUPLO)
        html = fetch(TOUR_URL)

        if html:
            current_hash = hashlib.md5(html.encode()).hexdigest()
            data = parse_tour(html)

            if tour_last_hash is None:
                tour_last_hash = current_hash
                tour_last_data = data

            elif current_hash != tour_last_hash and data != tour_last_data:
                tour_last_hash = current_hash
                tour_last_data = data
                await alert_tour(data)

        # TICKETS
        for url in EVENTS_TICKET:
            check_ticket += 1
            await alert_ticket(url, {
                "setor":"N/A",
                "categorias":"N/A",
                "tipo":"N/A",
                "status":"N/A",
                "date":"N/A",
                "quantidade":"N/A"
            })

        # BLUE
        for url in EVENTS_BLUE:
            check_blue += 1
            await alert_blue(url, {
                "setor":"N/A",
                "categorias":"N/A",
                "tipo":"N/A",
                "status":"N/A",
                "valor":"N/A"
            })

        await update_panel(tour_last_data)
        await asyncio.sleep(30)

# =========================
# DISCORD EVENTS
# =========================

@discord_client.event
async def on_ready():
    print(f"Discord conectado como {discord_client.user}")
    await send_discord("👾•°•°• Wootteo ligando os motores•°•°•👾")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    if message.content.lower() == "/painel":
        await message.channel.send("👾 Painel ativado👾")

    if message.content.lower() == "/teste":
        await message.channel.send("""🌊TESTE🌊
📅Data: 13/06
🔗Link: https://ibighit.com/en/bts/tour/
📍Setor: Porão da Big Hit
🎫Categoria: Army
🎟️Tipo: OT7
📦Status: disponível
📊Qtd: 07
""")

    if message.content.lower() == "/status":
        await message.channel.send(f"🟢 Uptime {get_uptime()}")

# =========================
# MAIN
# =========================

async def main():
    keep_alive()

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