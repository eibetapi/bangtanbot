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
BOT_TOKEN_BLUE = os.getenv("BOT_TOKEN_BLUE")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

CHAT_ID = -1003972186058
ADMIN_ID = 1407508561

TICKETMASTER_LINKS = [
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-28-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-30-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-31-10"
]

BLUE_LINKS = [
    "https://buyticketbrasil.com/evento/bts%E2%80%932026worldtourarirang?data=1793242799000"
]

TOUR_URL = "https://ibighit.com/en/bts/tour/"

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

tour_last_hash = None
ticket_last_hash = {}
blue_last_hash = {}

panel_message_id = None
panel_chat_id = None

check_ticket = 0
check_blue = 0

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
# TOUR PARSER (BTS)
# =========================

def parse_tour(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    date = re.findall(r"\d{1,2}/\d{1,2}/\d{4}", text)
    city = re.findall(r"[A-Z][a-z]+,\s?[A-Z]{2}", text)

    return {
        "date": date[0] if date else "N/A",
        "city": city[0] if city else "N/A",
        "raw": text
    }

# =========================
# ALERTS (NÃO MEXER LAYOUT)
# =========================

async def alert_tour(data):
    msg = f"""💜AGENDA TOUR UPDATE💜
📅 Data: {data['date']}
🏙️ Cidades: {data['city']}
🌎 Países: USA
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)
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
    await bot_ticket.send_message(chat_id=CHAT_ID, text=text)
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
    await bot_blue.send_message(chat_id=CHAT_ID, text=text)
    await discord_send(text)

# =========================
# BOOT
# =========================

async def send_boot():
    msg = "👾•°•°• Wootteo ligando os motores•°•°•👾"
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)
    await bot_blue.send_message(chat_id=CHAT_ID, text=msg)
    await bot_ticket.send_message(chat_id=ADMIN_ID, text=msg)
    await discord_send(msg)

# =========================
# COMMANDS (TELEGRAM)
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
    await bot_blue.send_message(chat_id=CHAT_ID, text=TESTE_TEXT)
    await discord_send(TESTE_TEXT)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = STATUS_TEXT()
    await update.message.reply_text(msg)
    await bot_blue.send_message(chat_id=CHAT_ID, text=msg)
    await discord_send(msg)

async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global panel_message_id, panel_chat_id
    msg = await update.message.reply_text("👾 Painel ativado👾")
    panel_message_id = msg.message_id
    panel_chat_id = CHAT_ID

# =========================
# PANEL (COMPLETO)
# =========================

async def update_panel(tour_data=None):
    global panel_message_id, panel_chat_id

    if not panel_message_id:
        return

    top = sorted(br_rank.items(), key=lambda x: x[1], reverse=True)

    text = f"""👾 CENTRAL WOOTTEO 👾

⏰ Uptime: {get_uptime()}

✈️ PRÓXIMAS DATAS:
🎫 Data: {tour_data['date'] if tour_data else 'N/A'}
📍 Local: {tour_data['city'] if tour_data else 'N/A'}
⏳ Faltam: N/A dias

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
# MONITOR (SEPARAÇÃO REAL DE ALERTAS)
# =========================

async def monitor():
    global tour_last_hash, check_ticket, check_blue

    while True:

        # TOUR
        html = fetch(TOUR_URL)
        if html:
            h = hashlib.md5(html.encode()).hexdigest()
            data = parse_tour(html)

            if tour_last_hash != h:
                tour_last_hash = h
                await alert_tour(data)

            await update_panel(data)

        # TICKETMASTER (SÓ SE MUDAR HASH POR LINK)
        for url in TICKETMASTER_LINKS:
            html = fetch(url)
            if not html:
                continue

            h = hashlib.md5(html.encode()).hexdigest()

            if ticket_last_hash.get(url) != h:
                ticket_last_hash[url] = h

                await alert_ticket(url, {
                    "setor":"N/A",
                    "categorias":"N/A",
                    "tipo":"N/A",
                    "status":"N/A",
                    "date":"N/A",
                    "quantidade":"N/A"
                })

        # BLUE
        for url in BLUE_LINKS:
            html = fetch(url)
            if not html:
                continue

            h = hashlib.md5(html.encode()).hexdigest()

            if blue_last_hash.get(url) != h:
                blue_last_hash[url] = h

                await alert_blue(url, {
                    "setor":"N/A",
                    "categorias":"N/A",
                    "tipo":"N/A",
                    "status":"N/A",
                    "valor":"N/A"
                })

        check_ticket += 1
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

    await send_boot()

    asyncio.create_task(discord_client.start(DISCORD_TOKEN))
    asyncio.create_task(monitor())

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())