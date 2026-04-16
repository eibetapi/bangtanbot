import asyncio
import time
import requests
import hashlib
from bs4 import BeautifulSoup
import os

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

CHAT_ID = -1003972186058

start_time = time.time()

bot_ticket = None

panel_message_id = None
panel_chat_id = None

check_ticket = 0
check_blue = 0


# =========================
# LINKS OFICIAIS
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
# CONTROLES
# =========================

boot_done = False
boot_lock = True
commands_ready = False
app_ready = False   # 🔥 FIX CRÍTICO

ticket_state = {}
blue_state = {}
bts_state = None


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


def hash_core(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    text = soup.get_text(" ", strip=True)
    return hashlib.md5(" ".join(text.split()).encode()).hexdigest()


# =========================
# 1. RESET / RECONNECT
# =========================

async def send_boot():
    global boot_done, boot_lock

    boot_lock = True

    await bot_ticket.send_message(
        chat_id=CHAT_ID,
        text="🛸•°•Wootteo entrando em rota°•°🛸"
    )

    await bot_ticket.send_message(
        chat_id=CHAT_ID,
        text="🛰️•°• Rota localizada°•°🛰️"
    )

    boot_done = True
    boot_lock = False

    await update_panel()


# =========================
# 2. PAINEL
# =========================

async def update_panel(tour_data=None):
    global panel_message_id, panel_chat_id

    if not app_ready or not panel_message_id:
        return

    text = f"""👾 CENTRAL WOOTTEO 👾

⏰ Uptime: {get_uptime()}

✈️ PRÓXIMAS DATAS:
🎫 Data: {tour_data['date'] if tour_data else 'ESGOTADO'}
📍 Local: {tour_data['city'] if tour_data else 'ESGOTADO'}

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
# 3. ALERTAS REAIS
# =========================

async def ticket_alert(url, key, found):
    msg = f"""🔥ALERTA DE REPOSIÇÃO 🔥
📅 Data: {clean(key)}
🔗Link: {url}
📍Setor: ESGOTADO
🎫Categoria: ESGOTADO
🛡️Tipo: ESGOTADO
✅Status: {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def ticket_new_date(url, key, found):
    msg = f"""🎁ALERTA DE NOVA DATA🎁
📅Data: {clean(key)}
🔗Link: {url}
📍Setor: ESGOTADO
🎫Categoria: ESGOTADO
🛡️Tipo: ESGOTADO
📊Quantidade: ESGOTADO
✅Status: {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def blue_alert(url, key, found):
    msg = f"""🔵REVENDA BLUE🔵
📅Data: {clean(key)}
🔗Link: {url}
📍Setor: ESGOTADO
💰Valor: ESGOTADO
🎫Categoria: ESGOTADO
🛡️Tipo: ESGOTADO
✅Status: {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def bts_alert(data):
    msg = f"""💜AGENDA NOVAS DATAS💜
📅 Data: {clean(data.get('date'))}
🏙️ Cidade: {clean(data.get('city'))}
🌎 País: USA
⚠️Mais informações em breve!
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


# =========================
# 4. ALERTAS DE TESTE
# =========================

async def ticket_alert_test(url, key, found):
    msg = f"""⚠️**TESTE**⚠️

🔥ALERTA DE REPOSIÇÃO 🔥
📅 Data: {key}
🔗Link: {url}
📍Setor: ESGOTADO
🎫Categoria: ESGOTADO
🛡️Tipo: ESGOTADO
✅Status: {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def ticket_new_date_test(url, key, found):
    msg = f"""⚠️**TESTE**⚠️

🎁ALERTA DE NOVA DATA🎁
📅Data: {key}
🔗Link: {url}
📍Setor: ESGOTADO
🎫Categoria: ESGOTADO
🛡️Tipo: ESGOTADO
📊Quantidade: ESGOTADO
✅Status: {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def blue_alert_test(url, key, found):
    msg = f"""⚠️**TESTE**⚠️

🔵REVENDA BLUE🔵
📅Data: {key}
🔗Link: {url}
📍Setor: ESGOTADO
💰Valor: ESGOTADO
🎫Categoria: ESGOTADO
🛡️Tipo: ESGOTADO
✅Status: {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


async def bts_alert_test(data):
    msg = f"""⚠️**TESTE**⚠️

💜AGENDA NOVAS DATAS💜
📅 Data: {data['date']}
🏙️ Cidade: {data['city']}
🌎 País: USA
⚠️Mais informações em breve!
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)


# =========================
# 5. COMANDOS
# =========================

async def teste(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not app_ready:
        return

    await ticket_alert_test("https://ticketmaster.com/teste", "31/10/2026", True)
    await ticket_new_date_test("https://ticketmaster.com/teste2", "30/10/2026", True)
    await blue_alert_test("https://blue.com/teste", "25/04/2026", True)
    await bts_alert_test({"date": "25/04/2026", "city": "Tampa"})

    await update.message.reply_text("⚠️ TESTE EXECUTADO")


async def painel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global panel_message_id, panel_chat_id

    if not app_ready:
        return

    msg = await context.bot.send_message(
        chat_id=CHAT_ID,
        text="👾 PAINEL ATIVADO"
    )

    panel_message_id = msg.message_id
    panel_chat_id = CHAT_ID


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not app_ready:
        return

    await update.message.reply_text(f"UPTIME: {get_uptime()}")


# =========================
# 6. MONITOR
# =========================

async def monitor():
    global check_ticket, check_blue

    while True:

        if boot_lock:
            await asyncio.sleep(5)
            continue

        check_ticket += 1
        check_blue += 1

        await asyncio.sleep(30)


# =========================
# 7. MAIN (FIX DEFINITIVO)
# =========================

async def main():
    global bot_ticket, commands_ready, app_ready

    keep_alive()

    bot_ticket = Bot(os.getenv("BOT_TOKEN_TICKET"))

    application = ApplicationBuilder().token(os.getenv("BOT_TOKEN_TICKET")).build()

    application.add_handler(CommandHandler("teste", teste))
    application.add_handler(CommandHandler("painel", painel))
    application.add_handler(CommandHandler("status", status))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()   # 🔥 FIX CRÍTICO REAL

    commands_ready = True
    app_ready = True

    await send_boot()

    asyncio.create_task(monitor())

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())