import asyncio
import time
import requests
import hashlib
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
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
    app_web.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run_web).start()


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

BTS_URL = "https://ibighit.com/en/bts/tour/"


# =========================
# AGENDA FIXA
# =========================

BTS_TOUR = [
    {"date": "18/04/2026", "city": "Tóquio", "country": "Japão"},
    {"date": "25/04/2026", "city": "Tampa", "country": "USA"},
    {"date": "26/04/2026", "city": "Tampa", "country": "USA"},
    {"date": "28/04/2026", "city": "Tampa", "country": "USA"},
    {"date": "28/10/2026", "city": "São Paulo", "country": "Brasil"},
    {"date": "30/10/2026", "city": "São Paulo", "country": "Brasil"},
    {"date": "31/10/2026", "city": "São Paulo", "country": "Brasil"}
]


# =========================
# CONTROLE
# =========================

boot_done = False
boot_lock = True

blink_state = True


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

def days_left(date_obj):
    return max((date_obj - datetime.now()).days, 0)

def minutes_since(ts):
    return int((time.time() - ts) / 60)


def get_next_shows():
    now = datetime.now()

    eventos = []
    for e in BTS_TOUR:
        dt = datetime.strptime(e["date"], "%d/%m/%Y")
        eventos.append({**e, "dt": dt})

    eventos.sort(key=lambda x: x["dt"])

    futuros = [e for e in eventos if e["dt"] >= now]

    proximo = futuros[0] if futuros else None
    brasil = next((e for e in eventos if e["country"] == "Brasil"), None)

    return proximo, brasil


def get_alert_text(dias):
    global blink_state

    if dias <= 3:
        blink_state = not blink_state
        return "🚨" if blink_state else "⚠️"

    return ""


# =========================
# 1. RESET / RECONNECT
# =========================

async def send_boot():

    global boot_done, boot_lock, panel_message_id, panel_chat_id

    boot_lock = True

    await bot_ticket.send_message(
        chat_id=CHAT_ID,
        text="🛸•°•Wootteo entrando em rota°•°🛸"
    )

    msg = await bot_ticket.send_message(
        chat_id=CHAT_ID,
        text="👾 CENTRAL WOOTTEO 👾\n\nInicializando painel..."
    )

    panel_message_id = msg.message_id
    panel_chat_id = CHAT_ID

    boot_done = True
    boot_lock = False

    await update_panel()


# =========================
# 2. PAINEL
# =========================

async def update_panel():

    global panel_message_id

    if not panel_message_id:
        return

    proximo, brasil = get_next_shows()

    if proximo:
        data = proximo["date"]
        city = proximo["city"]
        dias = days_left(proximo["dt"])
        alerta = get_alert_text(dias)
    else:
        data = "..."
        city = "..."
        dias = "..."
        alerta = ""

    if brasil:
        dias_br = days_left(datetime.strptime(brasil["date"], "%d/%m/%Y"))
    else:
        dias_br = "..."

    text = f"""👾*PAINEL DE CONTROLE*👾

🔴*⊙⊝⊜ ARIRANG TOUR ⊙⊝⊜*🔴

✈️ *PRÓXIMAS DATAS*

🎫 *Data:* {data} {alerta}
📍 *Local:* {city}
🔔 Faltam {dias} dias.

⏳Faltam {dias_br} dias para o BTS no Brasil.

🟡 *Ticket:* {check_ticket} | último rastreio há {minutes_since(last_ticket_check)} min
🔵 *Blue:* {check_blue} | último rastreio há {minutes_since(last_blue_check)} min
"""

    try:
        await bot_ticket.edit_message_text(
            chat_id=panel_chat_id,
            message_id=panel_message_id,
            text=text,
            parse_mode="Markdown"
        )
    except:
        pass


# =========================
# 3. ALERTAS OFICIAIS
# =========================

async def ticket_reposicao(url, key, found):
    msg = f"""🔥*ALERTA DE REPOSIÇÃO*🔥
📅 *Data:* {clean(key)}
🔗 *Link:* {url}
📍 *Setor:* ESGOTADO
🎫 *Categoria:* ESGOTADO
🛡️ *Tipo:* ESGOTADO
✅ *Status:* {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def ticket_nova_data(url, key, found):
    msg = f"""🎁*ALERTA DE NOVA DATA*🎁
📅 *Data:* {clean(key)}
🔗 *Link:* {url}
📍 *Setor:* ESGOTADO
🎫 *Categoria:* ESGOTADO
🛡️ *Tipo:* ESGOTADO
📊 *Quantidade:* ESGOTADO
✅ *Status:* {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def blue_revenda(url, key, found):
    msg = f"""🔵*REVENDA BLUE*🔵
📅 *Data:* {clean(key)}
🔗 *Link:* {url}
📍 *Setor:* ESGOTADO
💰 *Valor:* ESGOTADO
🎫 *Categoria:* ESGOTADO
🛡️ *Tipo:* ESGOTADO
✅ *Status:* {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def agenda_update(data):
    msg = f"""💜*AGENDA NOVAS DATAS*💜
📅 *Data:* {clean(data.get('date'))}
🏙️ *Cidade:* {clean(data.get('city'))}
🌎 *País:* {clean(data.get('country'))}
⚠️*Mais informações em breve!*
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


# =========================
# 4. ALERTAS DE TESTE
# =========================

async def test_reposicao(url, key, found):
    msg = f"""⚠️**TESTE**⚠️

🔥*ALERTA DE REPOSIÇÃO*🔥
📅 *Data:* {clean(key)}
🔗 *Link:* {url}
📍 *Setor:* ESGOTADO
🎫 *Categoria:* ESGOTADO
🛡️ *Tipo:* ESGOTADO
✅ *Status:* {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def test_nova_data(url, key, found):
    msg = f"""⚠️**TESTE**⚠️

🎁*ALERTA DE NOVA DATA*🎁
📅 *Data:* {clean(key)}
🔗 *Link:* {url}
📍 *Setor:* ESGOTADO
🎫 *Categoria:* ESGOTADO
🛡️ *Tipo:* ESGOTADO
📊 *Quantidade:* ESGOTADO
✅ *Status:* {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def test_blue(url, key, found):
    msg = f"""⚠️**TESTE**⚠️

🔵*REVENDA BLUE*🔵
📅 *Data:* {clean(key)}
🔗 *Link:* {url}
📍 *Setor:* ESGOTADO
💰 *Valor:* ESGOTADO
🎫 *Categoria:* ESGOTADO
🛡️ *Tipo:* ESGOTADO
✅ *Status:* {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def test_agenda(data):
    msg = f"""⚠️**TESTE**⚠️

💜*AGENDA NOVAS DATAS*💜
📅 *Data:* {clean(data.get('date'))}
🏙️ *Cidade:* {clean(data.get('city'))}
🌎 *País:* {clean(data.get('country'))}
⚠️*Mais informações em breve!*
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


# =========================
# 5. COMANDOS
# =========================

async def teste(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await test_reposicao(TICKET_LINKS[0], "31/10/2026", True)
    await test_nova_data(TICKET_LINKS[1], "30/10/2026", True)
    await test_blue(BLUE_LINKS[0], "25/04/2026", True)
    await test_agenda({"date": "25/04/2026", "city": "Seoul", "country": "Coreia do Sul"})


async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update_panel()


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_message(f"UPTIME: {get_uptime()}")


# =========================
# 6. LOOPS
# =========================

async def monitor():

    global check_ticket, check_blue, last_ticket_check, last_blue_check

    while True:

        if boot_lock:
            await asyncio.sleep(5)
            continue

        check_ticket += 1
        check_blue += 1

        last_ticket_check = time.time()
        last_blue_check = time.time()

        await asyncio.sleep(30)


async def panel_loop():
    while True:
        if not boot_lock:
            await update_panel()
        await asyncio.sleep(5)


# =========================
# 7. MAIN
# =========================

async def main():

    global bot_ticket

    keep_alive()

    bot_ticket = Bot(os.getenv("BOT_TOKEN_TICKET"))

    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN_TICKET")).build()

    app.add_handler(CommandHandler("teste", teste))
    app.add_handler(CommandHandler("painel", painel))
    app.add_handler(CommandHandler("status", status))

    await app.initialize()
    await app.start()

    await bot_ticket.delete_webhook(drop_pending_updates=True)

    await send_boot()

    asyncio.create_task(monitor())
    asyncio.create_task(panel_loop())

    await app.run_polling(close_loop=False)


if __name__ == "__main__":
    asyncio.run(main())