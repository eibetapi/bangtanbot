import asyncio
import time
import requests
from bs4 import BeautifulSoup
import os
import re

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

CHAT_ID = -1003972186058
ADMIN_ID = 1407508561

bot_ticket = Bot(token=BOT_TOKEN_TICKET)
bot_blue = Bot(token=BOT_TOKEN_BLUE)
bot_admin = Bot(token=BOT_TOKEN_TICKET)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

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
# STATE (ANTI-SPAM REAL)
# =========================

last_state = {}
initialized = False

# =========================
# FETCH
# =========================

def fetch(url):
    try:
        return session.get(url, timeout=10).text
    except:
        return None

# =========================
# PARSER (ESTADO REAL)
# =========================

def parse_event(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    if any(x in text for x in ["esgot", "sold out"]):
        status = "ESGOTADO"
    elif any(x in text for x in ["dispon", "available"]):
        status = "DISPONÍVEL"
    else:
        status = "DESCONHECIDO"

    if "pré-venda" in text or "pre venda" in text:
        tipo = "PRÉ-VENDA"
    elif "venda geral" in text:
        tipo = "VENDA GERAL"
    else:
        tipo = "NÃO IDENTIFICADO"

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

    date = None
    time_tag = soup.find("time")
    if time_tag:
        date = time_tag.get_text(strip=True)

    return {
        "status": status,
        "tipo": tipo,
        "categorias": ", ".join(categorias),
        "setor": ", ".join(setores),
        "date": date,
        "quantidade": "DESCONHECIDO"
    }

# =========================
# STATE BUILDER
# =========================

def make_state(data):
    return f"{data['status']}|{data['tipo']}|{data['setor']}|{data['categorias']}|{data['quantidade']}|{data['date']}"

# =========================
# ALERTAS (SEU FORMATO ORIGINAL)
# =========================

async def alert_ticket(url, data):
    text = f"""🔥ALERTA DE REPOSIÇÃO 🔥
📅Data: {data['date']}
🔗Link: {url}
📍Setor: {data['setor']}
🎫Categoria: {data['categorias']}
🎟️Tipo: {data['tipo']}
📦Status: {data['status']}
📊Qtd: {data['quantidade']}

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
📅Data: {data['date']}
🔗Link: {url}
📍Setor: {data['setor']}
🎫Categoria: {data['categorias']}
🎟️Tipo: {data['tipo']}
💰Valor: 
📦Status: {data['status']}
📊Qtd: {data['quantidade']}
"""
    await bot_blue.send_message(chat_id=CHAT_ID, text=text)

# =========================
# TESTE (OBRIGATÓRIO 1X)
# =========================

async def send_boot_messages():
    await bot_ticket.send_message(chat_id=CHAT_ID, text="🧪 BOT TICKET ONLINE")
    await bot_blue.send_message(chat_id=CHAT_ID, text="🧪 BOT BLUE ONLINE")

    await bot_admin.send_message(
        chat_id=ADMIN_ID,
        text="👾•°•°•Painel iniciado•°•°•👾"
    )

# =========================
# COMANDO TESTE
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
# MONITOR (SEM SPAM REAL)
# =========================

async def monitor():
    global initialized

    while True:

        # TICKETMASTER
        for url in EVENTS_TICKET:
            html = fetch(url)
            if not html:
                continue

            data = parse_event(html)
            state = make_state(data)

            old = last_state.get(url)

            # 🔥 PRIMEIRA EXECUÇÃO = só salva (NÃO ALERTA)
            if old is None:
                last_state[url] = state
                continue

            # 🔥 só alerta mudança real
            if old != state:
                last_state[url] = state
                await alert_ticket(url, data)

        # BLUE
        for url in EVENTS_BLUE:
            html = fetch(url)
            if not html:
                continue

            data = parse_event(html)
            state = make_state(data)

            old = last_state.get(url)

            if old is None:
                last_state[url] = state
                continue

            if old != state:
                last_state[url] = state
                await alert_blue(url, data)

        await asyncio.sleep(30)

# =========================
# MAIN
# =========================

async def main():
    keep_alive()

    app_ticket = ApplicationBuilder().token(BOT_TOKEN_TICKET).build()
    app_blue = ApplicationBuilder().token(BOT_TOKEN_BLUE).build()

    for app in [app_ticket, app_blue]:
        app.add_handler(CommandHandler("teste", teste))

    await send_boot_messages()

    await app_ticket.initialize()
    await app_blue.initialize()

    await app_ticket.start()
    await app_blue.start()

    asyncio.create_task(monitor())

    await asyncio.Event().wait()

asyncio.run(main())
