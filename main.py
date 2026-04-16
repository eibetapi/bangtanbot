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
    Thread(target=run_web, daemon=True).start()

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
# LINKS (RESTAURADOS)
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

@discord_client.event
async def on_ready():
    print("Discord conectado")
    await discord_send("👾•°•°• Wootteo ligando os motores•°•°•👾")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    if message.content.lower() == "/teste":
        await message.channel.send(TESTE_TEXT)

    if message.content.lower() == "/status":
        await message.channel.send(STATUS_TEXT())

    if message.content.lower() == "/painel":
        await message.channel.send("👾 Painel ativado👾")

# =========================
# STATE
# =========================

start_time = time.time()

tour_last_hash = None
tour_last_event = None

check_ticket = 0
check_blue = 0

panel_message_id = None
panel_chat_id = None

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
# ALERTS (SEM ALTERAR LAYOUT)
# =========================

async def alert_tour(data):
    msg = f"""💜AGENDA TOUR UPDATE💜
📅 Data: {data['date']}
🏙️ Cidades: {data['city']}
🌎 Países: USA
"""
    await discord_send(msg)

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
    await discord_send(text)

async def alert_blue(url, data):
    text = f"""🔵REVENDA BLUE🔵
🔗Link: {url}
📍Setor: {data.get('setor','N/A')}
💰Valor: {data.get('valor','N/A')}
🎫Categoria: {data.get('categorias','N/A')}
🎟️Tipo: {data.get('tipo','N/A')}
📦Status: {data.get('status','N/A')}
"""
    await discord_send(text)

# =========================
# COMMANDS (SEM ALTERAR TEXTO)
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
    global panel_message_id, panel_chat_id
    msg = await update.message.reply_text("👾 Painel ativado👾")
    panel_message_id = msg.message_id
    panel_chat_id = CHAT_ID

# =========================
# TOUR PARSER
# =========================

def parse_tour(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    date_match = re.search(r"\d{1,2}/\d{1,2}", text)
    city_match = re.search(r"[A-Z][a-z]+,\s?[A-Z]{2}", text)

    return {
        "date": date_match.group() if date_match else "N/A",
        "city": city_match.group() if city_match else "N/A"
    }

# =========================
# PANEL UPDATE (RESTAURADO)
# =========================

async def update_panel(data):
    global panel_message_id, panel_chat_id

    if not panel_message_id or not panel_chat_id:
        return

    top = sorted(br_rank.items(), key=lambda x: x[1], reverse=True)

    text = f"""👾 CENTRAL WOOTTEO 👾

⏰ Uptime: {get_uptime()}

✈️ PRÓXIMAS DATAS:
🎫 Data: {data['date']}
📍 Local: {data['city']}

🇧🇷 RANKING POSSÍVEIS DATAS BR:
🥇 {top[0][0]} ({top[0][1]})
🥈 {top[1][0]} ({top[1][1]})
🥉 {top[2][0]} ({top[2][1]})

🟡 Ticket: {check_ticket}
🔵 Blue: {check_blue}
"""

    try:
        await bot_ticket.edit_message_text(
            chat_id=panel_chat_id,
            message_id=panel_message_id,
            text=text
        )
    except:
        pass

# =========================
# MONITOR (SEM SPAM + COM LINKS)
# =========================

async def monitor():
    global tour_last_hash, tour_last_event, check_ticket, check_blue

    while True:

        html = fetch(TOUR_URL)

        if html:
            h = hashlib.md5(html.encode()).hexdigest()

            if h != tour_last_hash:
                tour_last_hash = h

                data = parse_tour(html)

                if tour_last_event != data["date"]:
                    tour_last_event = data["date"]
                    await alert_tour(data)

                await update_panel(data)

        # Ticket alerts (SÓ LINKS REAIS)
        for url in EVENTS_TICKET:
            check_ticket += 1

        for url in EVENTS_BLUE:
            check_blue += 1

        await asyncio.sleep(30)

# =========================
# MAIN
# =========================

async def main():
    global bot_ticket, bot_blue

    keep_alive()

    bot_ticket = Bot(os.getenv("BOT_TOKEN_TICKET"))
    bot_blue = Bot(os.getenv("BOT_TOKEN_BLUE"))

    app_ticket = ApplicationBuilder().token(os.getenv("BOT_TOKEN_TICKET")).build()

    app_ticket.add_handler(CommandHandler("teste", teste))
    app_ticket.add_handler(CommandHandler("status", status))
    app_ticket.add_handler(CommandHandler("painel", painel))

    await app_ticket.initialize()
    await app_ticket.start()
    await app_ticket.updater.start_polling()

    await send_boot()

    await discord_client.start(DISCORD_TOKEN)

    asyncio.create_task(monitor())

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main()) 