import asyncio
import time
import requests
import hashlib
from bs4 import BeautifulSoup
import os
import re

import discord

from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from flask import Flask
from threading import Thread

# =========================
# KEEP ALIVE (RAILWAY)
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
discord_client = discord.Client(intents=intents)

async def send_discord(msg):
    try:
        channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send(msg)
    except:
        pass

@discord_client.event
async def on_ready():
    print(f"Discord conectado como {discord_client.user}")

# =========================
# UPTIME
# =========================

start_time = time.time()
last_reconnect = "Nenhuma"

check_ticket = 0
check_blue = 0

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
tour_last_state = None

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
# SMART SIGNATURE (ANTI-SPAM REAL)
# =========================

def smart_signature(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(" ", strip=True).lower()
    text = re.sub(r"\s+", " ", text)

    keywords = [
        "sold out", "available", "esgotado", "disponível",
        "tickets", "ingressos", "buy", "comprar",
        "tour", "data", "date"
    ]

    filtered = " ".join([
        w for w in text.split()
        if any(k in w for k in keywords) or len(w) < 20
    ])

    return hashlib.md5(filtered.encode()).hexdigest()

# =========================
# TOUR PARSER
# =========================

def parse_tour(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    date = re.search(r"\d{1,2}/\d{1,2}", text)
    date = date.group() if date else "N/A"

    cities = []
    countries = []

    known_countries = ["brazil", "japan", "korea", "usa", "france", "uk"]
    for k in known_countries:
        if k in text:
            countries.append(k.upper())

    br_cities = ["são paulo", "rio de janeiro", "curitiba", "belo horizonte", "brasília"]
    for c in br_cities:
        if c in text:
            cities.append(c.title())
            br_rank[c.title()] += 1

    return {
        "date": date,
        "cities": cities or ["N/A"],
        "countries": countries or ["N/A"]
    }

# =========================
# ALERTAS
# =========================

async def alert_tour(data):
    msg = f"""💜AGENDA TOUR UPDATE💜
📅 Data: {data['date']}
🏙️ Cidades: {", ".join(data['cities'])}
🌎 Países: {", ".join(data['countries'])}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)
    await send_discord(msg)

async def alert_ticket(url):
    msg = f"""🔥 ALERTA TICKETMASTER
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)
    await send_discord(msg)

async def alert_blue(url):
    msg = f"""🔵 ALERTA BLUE
🔗 {url}
"""
    await bot_blue.send_message(chat_id=CHAT_ID, text=msg)
    await send_discord(msg)

# =========================
# PAINEL
# =========================

panel_message_id = None

async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global panel_message_id
    msg = await update.message.reply_text("👾 Painel ativado")
    panel_message_id = msg.message_id

async def update_panel(tour_data=None):
    global panel_message_id

    if not panel_message_id:
        return

    top = sorted(br_rank.items(), key=lambda x: x[1], reverse=True)

    text = f"""👾 CENTRAL WOOTTEO 👾

⏰ Uptime: {get_uptime()}

🌍 PRÓXIMA DATA: {tour_data['date'] if tour_data else 'N/A'}
🏙️ CIDADES: {", ".join(tour_data['cities']) if tour_data else 'N/A'}

🇧🇷 RANKING BR:
🥇 {top[0][0]} ({top[0][1]})
🥈 {top[1][0]} ({top[1][1]})
🥉 {top[2][0]} ({top[2][1]})

🟡 Ticket: {check_ticket}
🔵 Blue: {check_blue}
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
# COMANDOS
# =========================

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟢 ONLINE")

async def teste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""🌊TESTE🌊
📅Data: 13/06
🔗Link: https://ibighit.com/en/bts/tour/
📍Setor: Porão da Big Hit
🎫Categoria: Army
🎟️Tipo: OT7
📦Status: disponível
📊Qtd: 07
""")

# =========================
# MONITOR (ANTI-SPAM REAL)
# =========================

async def monitor():
    global check_ticket, check_blue, tour_last_state

    tour_cache = None

    while True:

        # TOUR
        html = fetch(TOUR_URL)

        if html:
            sig = smart_signature(html)
            data = parse_tour(html)

            if tour_last_state != sig:
                tour_last_state = sig
                tour_cache = data
                await alert_tour(data)

        # TICKETMASTER
        for url in EVENTS_TICKET:
            check_ticket += 1
            html = fetch(url)
            if html:
                sig = smart_signature(html)

                if url not in last_state or last_state[url] != sig:
                    last_state[url] = sig
                    await alert_ticket(url)

        # BLUE
        for url in EVENTS_BLUE:
            check_blue += 1
            html = fetch(url)
            if html:
                sig = smart_signature(html)

                if url not in last_state or last_state[url] != sig:
                    last_state[url] = sig
                    await alert_blue(url)

        await update_panel(tour_cache)
        await asyncio.sleep(30)

# =========================
# MAIN
# =========================

async def main():
    keep_alive()

    app_ticket = ApplicationBuilder().token(BOT_TOKEN_TICKET).build()
    app_blue = ApplicationBuilder().token(BOT_TOKEN_BLUE).build()

    for app in [app_ticket, app_blue]:
        app.add_handler(CommandHandler("status", status))
        app.add_handler(CommandHandler("teste", teste))
        app.add_handler(CommandHandler("painel", painel))

    print("🔥 Bots iniciando...")

    await bot_admin.send_message(CHAT_ID, "👾 sistema iniciado")

    asyncio.create_task(discord_client.start(DISCORD_TOKEN))
    asyncio.create_task(monitor())

    await app_ticket.initialize()
    await app_blue.initialize()

    await app_ticket.start()
    await app_blue.start()

    await asyncio.Event().wait()

asyncio.run(main())
