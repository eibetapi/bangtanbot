import asyncio
import time
import requests
import hashlib
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from flask import Flask
from threading import Thread

# =========================
# KEEP ALIVE
# =========================

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bots rodando"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_web, daemon=True).start()


# =========================
# CONFIG
# =========================

CHAT_ID = -1003972186058

start_time = time.time()

bot_ticket = None

panel_message_id = None
panel_chat_id = None

check_ticket = 0
check_blue = 0

last_ticket_check = time.time()
last_blue_check = time.time()


# =========================
# LINKS (NÃO REMOVER)
# =========================

TICKET_LINKS = [
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-28-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-30-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-31-10"
]

BLUE_LINKS = [
    "https://buyticketbrasil.com/evento/bts-2026-world-tour-arirang"
]


# =========================
# AGENDA FIXA
# =========================

AGENDA = [
    ("18/04/2026", "Tóquio, Japão"),
    ("25/04/2026", "Tampa, EUA"),
    ("26/04/2026", "Tampa, EUA"),
    ("28/04/2026", "Tampa, EUA"),
    ("02/05/2026", "El Paso, EUA"),
    ("03/05/2026", "El Paso, EUA"),
    ("07/05/2026", "Cidade do México, México"),
    ("09/05/2026", "Cidade do México, México"),
    ("10/05/2026", "Cidade do México, México"),
    ("16/05/2026", "Stanford, EUA"),
    ("17/05/2026", "Stanford, EUA"),
    ("19/05/2026", "Stanford, EUA"),
    ("23/05/2026", "Las Vegas, EUA"),
    ("24/05/2026", "Las Vegas, EUA"),
    ("27/05/2026", "Las Vegas, EUA"),
    ("28/05/2026", "Las Vegas, EUA"),
    ("12/06/2026", "Busan, Coreia do Sul"),
    ("13/06/2026", "Busan, Coreia do Sul"),
    ("26/06/2026", "Madrid, Espanha"),
    ("27/06/2026", "Madrid, Espanha"),
    ("01/07/2026", "Bruxelas, Bélgica"),
    ("02/07/2026", "Bruxelas, Bélgica"),
    ("06/07/2026", "Londres, Reino Unido"),
    ("07/07/2026", "Londres, Reino Unido"),
    ("11/07/2026", "Munique, Alemanha"),
    ("12/07/2026", "Munique, Alemanha"),
    ("17/07/2026", "Paris, França"),
    ("18/07/2026", "Paris, França"),
    ("01/08/2026", "East Rutherford, EUA"),
    ("02/08/2026", "East Rutherford, EUA"),
    ("05/08/2026", "Foxborough, EUA"),
    ("06/08/2026", "Foxborough, EUA"),
    ("10/08/2026", "Baltimore, EUA"),
    ("11/08/2026", "Baltimore, EUA"),
    ("15/08/2026", "Arlington, EUA"),
    ("16/08/2026", "Arlington, EUA"),
    ("22/08/2026", "Toronto, Canadá"),
    ("23/08/2026", "Toronto, Canadá"),
    ("27/08/2026", "Chicago, EUA"),
    ("28/08/2026", "Chicago, EUA"),
    ("01/09/2026", "Los Angeles, EUA"),
    ("02/09/2026", "Los Angeles, EUA"),
    ("05/09/2026", "Los Angeles, EUA"),
    ("06/09/2026", "Los Angeles, EUA"),
    ("02/10/2026", "Bogotá, Colômbia"),
    ("03/10/2026", "Bogotá, Colômbia"),
    ("07/10/2026", "Lima, Peru"),
    ("09/10/2026", "Lima, Peru"),
    ("10/10/2026", "Lima, Peru"),
    ("14/10/2026", "Santiago, Chile"),
    ("16/10/2026", "Santiago, Chile"),
    ("17/10/2026", "Santiago, Chile"),
    ("21/10/2026", "Buenos Aires, Argentina"),
    ("23/10/2026", "Buenos Aires, Argentina"),
    ("24/10/2026", "Buenos Aires, Argentina"),
    ("28/10/2026", "São Paulo, Brasil"),
    ("30/10/2026", "São Paulo, Brasil"),
    ("31/10/2026", "São Paulo, Brasil"),
    ("19/11/2026", "Kaohsiung, Taiwan"),
    ("21/11/2026", "Kaohsiung, Taiwan"),
    ("22/11/2026", "Kaohsiung, Taiwan"),
    ("03/12/2026", "Banguecoque, Tailândia"),
    ("05/12/2026", "Banguecoque, Tailândia"),
    ("06/12/2026", "Banguecoque, Tailândia"),
    ("12/12/2026", "Kuala Lumpur, Malásia"),
    ("13/12/2026", "Kuala Lumpur, Malásia"),
    ("17/12/2026", "Singapura, Singapura"),
    ("19/12/2026", "Singapura, Singapura"),
    ("20/12/2026", "Singapura, Singapura"),
    ("22/12/2026", "Singapura, Singapura"),
    ("26/12/2026", "Jacarta, Indonésia"),
    ("27/12/2026", "Jacarta, Indonésia"),
    ("12/02/2027", "Melbourne, Austrália"),
    ("13/02/2027", "Melbourne, Austrália"),
    ("20/02/2027", "Sydney, Austrália"),
    ("21/02/2027", "Sydney, Austrália"),
    ("04/03/2027", "Hong Kong, China"),
    ("06/03/2027", "Hong Kong, China"),
    ("07/03/2027", "Hong Kong, China"),
    ("13/03/2027", "Manila, Filipinas"),
    ("14/03/2027", "Manila, Filipinas"),
]


# =========================
# CONTROLE
# =========================

boot_lock = True


# =========================
# UTIL
# =========================

def get_uptime():
    s = int(time.time() - start_time)
    return f"{s//3600}h {(s%3600)//60}m {s%60}s"

def resolve_status(found):
    return "DISPONÍVEL" if found else "ESGOTADO"

def clean(v):
    return v if v and str(v).strip() else "ESGOTADO"

def days_left(date_str):
    try:
        d = datetime.strptime(date_str, "%d/%m/%Y")
        delta = (d - datetime.now()).days
        return max(delta, 0)
    except:
        return "..."

def minutes_since(ts):
    return int((time.time() - ts) / 60)

def get_next_show():
    now = datetime.now()
    for d, city in AGENDA:
        try:
            dt = datetime.strptime(d, "%d/%m/%Y")
            if dt >= now:
                return d, city, days_left(d)
        except:
            continue
    return "carregando...", "carregando...", "..."


# =========================
# 1. RESET / RECONNECT
# =========================

async def send_boot():
    global boot_lock, panel_message_id, panel_chat_id
    boot_lock = True

    await bot_ticket.send_message(chat_id=CHAT_ID, text="🛸•°•Wootteo entrando em rota°•°🛸")

    msg = await bot_ticket.send_message(
        chat_id=CHAT_ID,
        text="👾 PAINEL DE CONTROLE 👾\n\nInicializando..."
    )

    panel_message_id = msg.message_id
    panel_chat_id = CHAT_ID

    try:
        await bot_ticket.pin_chat_message(chat_id=panel_chat_id, message_id=panel_message_id, disable_notification=True)
    except:
        pass

    boot_lock = False
    await update_panel()


# =========================
# 2. PAINEL
# =========================

async def update_panel():
    global panel_message_id
    if not panel_message_id: return

    data, city, dias = get_next_show()
    dias_br = days_left("28/10/2026")

    text = f"""👾*PAINEL DE CONTROLE*👾

🔴*⊙⊝⊜ ARIRANG TOUR ⊙⊝⊜*🔴

✈️ *PRÓXIMAS DATAS*

🎫 *Data:* {data}
📍 *Local:* {city}
🔔 Faltam {dias} dias.

⏳Faltam {dias_br} dias para o BTS no Brasil.

🟡 Ticketmaster
acesso realizado: {check_ticket} | último rastreio há {minutes_since(last_ticket_check)} min
🔵 Buyticket
acesso realizado: {check_blue} | último rastreio há {minutes_since(last_blue_check)} min
"""
    try:
        await bot_ticket.edit_message_text(chat_id=panel_chat_id, message_id=panel_message_id, text=text, parse_mode="Markdown")
    except:
        pass


# =========================
# 3. ALERTAS (OFICIAIS E TESTE)
# =========================

async def test_reposicao(url, key, found):
    msg = f"⚠️**TESTE**⚠️\n\n🔥ALERTA DE REPOSIÇÃO 🔥\n📅 Data: {clean(key)}\n🔗Link: {url}\n✅Status: {resolve_status(found)}"
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_nova_data(url, key, found):
    msg = f"⚠️**TESTE**⚠️\n\n🎁ALERTA DE NOVA DATA🎁\n📅Data: {clean(key)}\n🔗Link: {url}\n✅Status: {resolve_status(found)}"
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_blue(url, key, found):
    msg = f"⚠️**TESTE**⚠️\n\n🔵REVENDA BLUE🔵\n📅Data: {clean(key)}\n🔗Link: {url}\n✅Status: {resolve_status(found)}"
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_agenda(data):
    msg = f"⚠️**TESTE**⚠️\n\n💜AGENDA NOVAS DATAS💜\n📅 Data: {clean(data.get('date'))}\n🏙️ Cidade: {clean(data.get('city'))}\n🌎 País: {clean(data.get('country'))}"
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


# =========================
# 5. COMANDOS (PV)
# =========================

async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    # Filtra para responder apenas no Privado
    if update.message.chat.type != "private": return

    text = update.message.text.lower()

    if "/teste" in text:
        await test_reposicao(TICKET_LINKS[0], "31/10/2026", True)
        await test_nova_data(TICKET_LINKS[1], "30/10/2026", True)
        await test_blue(BLUE_LINKS[0], "25/04/2026", True)
        await test_agenda({"date": "25/04/2026", "city": "Seoul", "country": "Coreia do Sul"})

    elif "/painel" in text:
        await update_panel()


# =========================
# 6. LOOPS
# =========================

async def monitor():
    global check_ticket, check_blue, last_ticket_check, last_blue_check
    while True:
        if not boot_lock:
            check_ticket += 1
            check_blue += 1
            last_ticket_check = time.time()
            last_blue_check = time.time()
        await asyncio.sleep(30)

async def panel_loop():
    while True:
        if not boot_lock: await update_panel()
        await asyncio.sleep(5)


# =========================
# 7. MAIN
# =========================

async def main():
    global bot_ticket
    keep_alive()

    token = os.getenv("BOT_TOKEN_TICKET")
    if not token:
        print("ERRO: Variável BOT_TOKEN_TICKET não encontrada!")
        return

    app = ApplicationBuilder().token(token).build()
    bot_ticket = app.bot

    # Handler mais abrangente para capturar mensagens no PV
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT, handle_commands))

    await app.initialize()
    await app.start()
    await bot_ticket.delete_webhook(drop_pending_updates=True)
    await send_boot()

    asyncio.create_task(monitor())
    asyncio.create_task(panel_loop())

    await app.updater.start_polling()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
