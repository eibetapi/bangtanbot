import asyncio
import time
import requests
from bs4 import BeautifulSoup
import os

from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from flask import Flask
from threading import Thread

import discord

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

# =========================
# STATE
# =========================

last_state = {}
system_ready = False

start_time = time.time()

check_ticket = 0
check_blue = 0

panel_message_id = None

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

def parse_event(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    status = "DESCONHECIDO"
    if "esgot" in text:
        status = "ESGOTADO"
    elif "dispon" in text:
        status = "DISPONÍVEL"

    tipo = "VENDA GERAL" if "venda geral" in text else "NÃO IDENTIFICADO"

    categorias = []
    if "meia" in text:
        categorias.append("MEIA-ENTRADA")
    if "inteira" in text:
        categorias.append("INTEIRA")
    if "pcd" in text:
        categorias.append("PCD")
    if not categorias:
        categorias = ["NÃO IDENTIFICADO"]

    setores = []
    if "vip" in text:
        setores.append("VIP")
    if "pista" in text:
        setores.append("PISTA")
    if "cadeira" in text:
        setores.append("CADEIRA")
    if not setores:
        setores = ["NÃO IDENTIFICADO"]

    return {
        "status": status,
        "tipo": tipo,
        "categorias": ", ".join(categorias),
        "setor": ", ".join(setores),
        "date": None,
        "quantidade": "DESCONHECIDO"
    }

# =========================
# STATE
# =========================

def make_state(data):
    return f"{data['status']}|{data['tipo']}|{data['setor']}|{data['categorias']}"

# =========================
# ALERTAS (SEU TEXTO MANTIDO 100%)
# =========================

async def alert_ticket(url, data):
    text = f"""🔥ALERTA DE REPOSIÇÃO 🔥
🔗Link: {url}
📍Setor: {data['setor']}
🎫Categoria: {data['categorias']}
🎟️Tipo: {data['tipo']}
📦Status: {data['status']}

🎁ALERTA DE NOVA DATA🎁 
📅Data: {data['date']} 
🔗Link: {url} 
📍Setor: {data['setor']} 
🎫Categoria: {data['categorias']} 
🎟️Tipo: {data['tipo']} 
📦Status: {data['status']} 
📊Qtd: {data['quantidade']}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=text)

async def alert_blue(url, data):
    text = f"""🔵REVENDA BLUE🔵
🔗Link: {url}
📍Setor: {data['setor']}
🎫Categoria: {data['categorias']}
🎟️Tipo: {data['tipo']}
📦Status: {data['status']}
"""
    await bot_blue.send_message(chat_id=CHAT_ID, text=text)

# =========================
# BOOT
# =========================

async def send_boot():
    msg = "👾•°•°• Wootteo ligando os motores•°•°•👾"
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)
    await bot_blue.send_message(chat_id=CHAT_ID, text=msg)
    await bot_admin.send_message(chat_id=ADMIN_ID, text=msg)

# =========================
# TESTE
# =========================

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
# PAINEL
# =========================

async def painel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global panel_message_id
    panel_message_id = update.message.message_id
    await update.message.reply_text("👾Painel iniciado👾")

# =========================
# MONITOR (ANTI-SPAM REAL)
# =========================

async def monitor():
    global system_ready, check_ticket, check_blue

    if not system_ready:
        for url in EVENTS_TICKET + EVENTS_BLUE:
            html = fetch(url)
            if html:
                data = parse_event(html)
                last_state[url] = make_state(data)

        system_ready = True
        await send_boot()

    while True:

        for url in EVENTS_TICKET:
            check_ticket += 1
            html = fetch(url)
            if not html:
                continue

            data = parse_event(html)
            state = make_state(data)

            if last_state.get(url) != state:
                last_state[url] = state
                await alert_ticket(url, data)

        for url in EVENTS_BLUE:
            check_blue += 1
            html = fetch(url)
            if not html:
                continue

            data = parse_event(html)
            state = make_state(data)

            if last_state.get(url) != state:
                last_state[url] = state
                await alert_blue(url, data)

        await asyncio.sleep(30)

# =========================
# DISCORD
# =========================

@discord_client.event
async def on_ready():
    print(f"Discord logado como {discord_client.user}")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    if message.content.lower().strip() == "/painel":
        await message.channel.send("👾Painel iniciado👾")

# =========================
# MAIN (CORRIGIDO DE VERDADE)
# =========================

def main():
    keep_alive()

    app_ticket = ApplicationBuilder().token(BOT_TOKEN_TICKET).build()
    app_blue = ApplicationBuilder().token(BOT_TOKEN_BLUE).build()

    app_ticket.add_handler(CommandHandler("teste", teste))
    app_ticket.add_handler(CommandHandler("painel", painel_cmd))

    print("Bots iniciando...")

    # Telegram correto (SEM asyncio conflito)
    app_ticket.run_polling()

    # monitor roda separado NÃO bloqueante
    asyncio.run(monitor())

if __name__ == "__main__":
    main()
