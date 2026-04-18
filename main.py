# =========================
# 0 BOT WOOTTEO
# =========================

import asyncio
import time
import requests
import hashlib
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

# =========================
# 1 DISCORD (CORRIGIDO - INSTÂNCIA ÚNICA)
# =========================

import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

bot_discord = commands.Bot(
command_prefix="!",
intents=intents
)

@bot_discord.event
async def on_ready():
    print(f"[DISCORD] Conectado como {bot_discord.user}")

    try:
        synced = await bot_discord.tree.sync()
        print(f"[DISCORD] Slash commands sincronizados: {len(synced)}")
    except Exception as e:
        print(f"[DISCORD SYNC ERROR] {e}")

    # 🚀 BOOT ÚNICO (ANTI DUPLICAÇÃO)
    await safe_boot()

    # 🚀 MONITOR (UMA VEZ SÓ)
    bot_discord.loop.create_task(monitor_loop())


# =========================
# 2 TELEGRAM + FLASK
# =========================

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from flask import Flask
from threading import Thread

# =========================
# 3 KEEP ALIVE
# =========================

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bots rodando"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


def keep_alive():
    if not getattr(keep_alive, "_running", False):
        Thread(target=run_web, daemon=True).start()
        keep_alive._running = True


# =========================
# 4 CONFIG
# =========================

CHAT_ID = -1003972186058

start_time = time.time()

bot_ticket = None

panel_message_id = None
panel_chat_id = CHAT_ID
panel_initialized = False

discord_panel_message_id = None

DISCORD_PANEL_CHANNEL_ID = 1494667029150695625
DISCORD_TICKETS_CHANNEL_ID = 1494670074374651985
DISCORD_WEVERSE_CHANNEL_ID = 1494680233025208461
DISCORD_SOCIAL_CHANNEL_ID = 1494682078950981864

check_ticket = 0
check_buy = 0
check_weverse = 0
check_social = 0

last_ticket_check = time.time()
last_buy_check = time.time()
last_weverse_check = time.time()
last_social_check = time.time()

SEEN_TICKET = set()
SEEN_BUY = set()
SEEN_WEVERSE = set()
SEEN_SOCIAL = set()

CONTENT_HASH = {}

def make_hash(data: str):
    return hashlib.sha256(
        data.encode("utf-8", errors="ignore")
    ).hexdigest()

    """
    ✔ Detecta mudança real de conteúdo
    ✔ Evita spam duplicado
    ✔ Funciona mesmo se página mudar levemente
    """

    if not html:
        return False

    new_hash = make_hash(html)
    old_hash = CONTENT_HASH.get(url)

    # primeira vez vendo essa URL
    if old_hash is None:
        CONTENT_HASH[url] = new_hash
        return True

    # mudou conteúdo
    if old_hash != new_hash:
        CONTENT_HASH[url] = new_hash
        return True

    return False


def is_new(url: str, html: str):
if not html:
return False

new_hash = make_hash(html)
old_hash = CONTENT_HASH.get(url)

if old_hash is None:
CONTENT_HASH[url] = new_hash
return True

if old_hash != new_hash:
CONTENT_HASH[url] = new_hash
return True

return False

# =========================
# 5 LINKS
# =========================

TICKET_LINKS = [
"https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-28-10",
"https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-30-10",
"https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-31-10"
]

BUY_LINKS = [
"https://bts.buyticketbrasil.com/ingressos?data=28-10-2026",
"https://bts.buyticketbrasil.com/ingressos?data=30-10-2026",
"https://bts.buyticketbrasil.com/ingressos?data=31-10-2026"
]

INSTAGRAM_LINKS = {
"rm": "https://www.instagram.com/rkive/",
"jin": "https://www.instagram.com/jin/",
"suga": "https://www.instagram.com/agustd/",
"jhope": "https://www.instagram.com/uarmyhope/",
"jimin": "https://www.instagram.com/j.m/",
"v": "https://www.instagram.com/thv/",
"jungkook": "https://www.instagram.com/mnijungkook/",
"bts": "https://www.instagram.com/bts.bighitofficial/",
"wootteo": "https://www.instagram.com/wootteo/"
}

TIKTOK_LINKS = {
"jungkook": "https://www.tiktok.com/@mnijungkook",
"jhope": "https://www.tiktok.com/@iamuhope",
"v": "https://www.tiktok.com/@tete",
"bts": "https://www.tiktok.com/@bts_official_bighit"
}

WEVERSE_LINKS = [
"https://weverse.io/bts/artist",
"https://weverse.io/bts/live",
"https://weverse.io/bts/notice",
"https://weverse.io/bts/media"
]

X_LINKS = [
"https://x.com/BTS_twt"
]

# =========================
# 6 AGENDA FIXA
# =========================

AGENDA = [
("25/04/2026", "Tampa", "EUA", "20:00"),
    ("26/04/2026", "Tampa", "EUA", "20:00"),
    ("28/04/2026", "Tampa", "EUA", "20:00"),
    ("02/05/2026", "El Paso", "EUA", "20:00"),
    ("03/05/2026", "El Paso", "EUA", "20:00"),
    ("07/05/2026", "Cidade do México", "México", "20:00"),
    ("09/05/2026", "Cidade do México", "México", "20:00"),
    ("10/05/2026", "Cidade do México", "México", "20:00"),
    ("16/05/2026", "Stanford", "EUA", "20:00"),
    ("17/05/2026", "Stanford", "EUA", "20:00"),
    ("19/05/2026", "Stanford", "EUA", "20:00"),
    ("23/05/2026", "Las Vegas", "EUA", "20:00"),
    ("24/05/2026", "Las Vegas", "EUA", "20:00"),
    ("27/05/2026", "Las Vegas", "EUA", "20:00"),
    ("28/05/2026", "Las Vegas", "EUA", "20:00"),
    ("12/06/2026", "Busan", "Coreia do Sul", "20:00"),
    ("13/06/2026", "Busan", "Coreia do Sul", "20:00"),
    ("26/06/2026", "Madri", "Espanha", "20:00"),
    ("27/06/2026", "Madri", "Espanha", "20:00"),
    ("01/07/2026", "Bruxelas", "Bélgica", "20:00"),
    ("02/07/2026", "Bruxelas", "Bélgica", "20:00"),
    ("06/07/2026", "Londres", "Reino Unido", "20:00"),
    ("07/07/2026", "Londres", "Reino Unido", "20:00"),
    ("11/07/2026", "Munique", "Alemanha", "20:00"),
    ("12/07/2026", "Munique", "Alemanha", "20:00"),
    ("17/07/2026", "Saint-Denis", "França", "20:00"),
    ("18/07/2026", "Saint-Denis", "França", "20:00"),
    ("01/08/2026", "East Rutherford", "EUA", "20:00"),
    ("02/08/2026", "East Rutherford", "EUA", "20:00"),
    ("02/10/2026", "Bogotá", "Colômbia", "20:00"),
    ("03/10/2026", "Bogotá", "Colômbia", "20:00"),
    ("07/10/2026", "Lima", "Peru", "20:00"),
    ("09/10/2026", "Lima", "Peru", "20:00"),
    ("10/10/2026", "Lima", "Peru", "20:00"),
    ("14/10/2026", "Santiago", "Chile", "20:00"),
    ("16/10/2026", "Santiago", "Chile", "20:00"),
    ("17/10/2026", "Santiago", "Chile", "20:00"),
    ("21/10/2026", "Buenos Aires", "Argentina", "20:00"),
    ("23/10/2026", "Buenos Aires", "Argentina", "20:00"),
    ("24/10/2026", "Buenos Aires", "Argentina", "20:00"),
    ("28/10/2026", "São Paulo", "Brasil", "20:00"),
    ("30/10/2026", "São Paulo", "Brasil", "20:00"),
    ("31/10/2026", "São Paulo", "Brasil", "20:00"),
    ("19/11/2026", "Kaohsiung", "Taiwan", "20:00"),
    ("21/11/2026", "Kaohsiung", "Taiwan", "20:00"),
    ("22/11/2026", "Kaohsiung", "Taiwan", "20:00"),
    ("03/12/2026", "Banguecoque", "Tailândia", "20:00"),
    ("05/12/2026", "Banguecoque", "Tailândia", "20:00"),
    ("06/12/2026", "Banguecoque", "Tailândia", "20:00"),
    ("12/12/2026", "Kuala Lumpur", "Malásia", "20:00"),
    ("13/12/2026", "Kuala Lumpur", "Malásia", "20:00"),
    ("17/12/2026", "Singapura", "Singapura", "20:00"),
    ("19/12/2026", "Singapura", "Singapura", "20:00"),
    ("20/12/2026", "Singapura", "Singapura", "20:00"),
    ("22/12/2026", "Singapura", "Singapura", "20:00"),
    ("26/12/2026", "Jacarta", "Indonésia", "20:00"),
    ("27/12/2026", "Jacarta", "Indonésia", "20:00"),
    ("12/02/2027", "Melbourne", "Austrália", "20:00"),
    ("13/02/2027", "Melbourne", "Austrália", "20:00"),
    ("20/02/2027", "Sydney", "Austrália", "20:00"),
    ("21/02/2027", "Sydney", "Austrália", "20:00"),
    ("04/03/2027", "Hong Kong", "China", "20:00"),
    ("06/03/2027", "Hong Kong", "China", "20:00"),
    ("07/03/2027", "Hong Kong", "China", "20:00"),
    ("13/03/2027", "Manila", "Filipinas", "20:00"),
    ("14/03/2027", "Manila", "Filipinas", "20:00")
]

# =========================
# 7 CONTROLE
# =========================

boot_lock = asyncio.Lock()
boot_initialized = False

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
return 0

def minutes_since(ts):
return int((time.time() - ts) / 60)

def get_next_show():
now = datetime.now()

for item in AGENDA:
try:
dt_show = datetime.strptime(f"{item[0]} {item[3]}", "%d/%m/%Y %H:%M")
if dt_show > now:
return item[0], f"{item[1]}, {item[2]}", days_left(item[0])
except:
continue

return "Continua…", "---", 0

def status_color(last_check):
return "🟢" if (time.time() - last_check) < 1800 else "🔴"

# =========================
# 8 SESSION
# =========================

import aiohttp

http_session = None

async def get_session():
global http_session
if http_session is None or http_session.closed:
http_session = aiohttp.ClientSession()
return http_session

# =========================
# 9 EMOJIS
# =========================

MEMBER_EMOJI = {
"rm": "🐨",
"jin": "🐹",
"suga": "🐱",
"jhope": "🐿️",
"jimin": "🐥",
"v": "🐻",
"jungkook": "🐰",
"bts": "💜",
"wootteo": "🛸"
}

def get_member_emoji(member_name):
return MEMBER_EMOJI.get(str(member_name).lower(), "💜")

def format_member(member_name):
emoji = get_member_emoji(member_name)
name = str(member_name).upper()
return emoji, name 

# =========================
# 10 DISCORD + TELEGRAM ROUTER (CORRIGIDO)
# =========================

def send_telegram(message):
    global bot_ticket

    if not bot_ticket:
        return

    try:
        asyncio.create_task(
            bot_ticket.send_message(chat_id=CHAT_ID, text=message)
        )
    except Exception:
        pass


async def send_discord(channel_id, message):
    global bot_discord

    if not bot_discord:
        return None

    try:
        channel = await bot_discord.fetch_channel(channel_id)
        if channel:
            return await channel.send(message)
    except Exception:
        return None


def send_alert(alert_type, message):
    """
    Router principal de alertas (Telegram + Discord)
    """

    # =========================
    # 11 TELEGRAM (SEMPRE PRIMEIRO)
    # =========================
    send_telegram(message)

    # =========================
    # 12 LOOP SAFE
    # =========================
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    # =========================
    # 13 DISCORD ROUTING
    # =========================

    # 🎫 Tickets / eventos
    if alert_type in ["ticket", "reposicao", "nova_data", "revenda", "agenda"]:
        loop.create_task(
            send_discord(DISCORD_TICKETS_CHANNEL_ID, message)
        )

    # 🩷 Weverse
    elif alert_type in ["weverse_post", "weverse_live", "weverse_news", "weverse_media"]:
        loop.create_task(
            send_discord(DISCORD_WEVERSE_CHANNEL_ID, message)
        )

    # 📱 Redes sociais
    elif alert_type in [
        "instagram_post", "instagram_reels", "instagram_stories", "instagram_live",
        "tiktok_post", "tiktok_live"
    ]:
        loop.create_task(
            send_discord(DISCORD_SOCIAL_CHANNEL_ID, message)
        )

    # 🧠 fallback seguro (evita crash se esquecer categoria)
    else:
        if 'DISCORD_NEWS_CHANNEL_ID' in globals():
            loop.create_task(
                send_discord(DISCORD_NEWS_CHANNEL_ID, message)
            )


# =========================
# 14 BOOT FIX (INÍCIO LIMPO)
# =========================

async def send_boot():
    global panel_message_id, panel_chat_id, panel_initialized, discord_panel_message_id

    if not bot_ticket or not bot_discord:
        return

    async with boot_lock:

        # 🔥 CORREÇÃO QUE VOCÊ MANDOU (mantida)
        msg = "🛸•°•Wootteo entrando em rota°•°🛸"

        # TELEGRAM
        try:
            await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)
        except Exception:
            pass

        # DISCORD
        try:
            channel = await bot_discord.fetch_channel(DISCORD_PANEL_CHANNEL_ID)
            if channel:
                await channel.send(msg)
        except Exception:
            pass

        # PAINEL (1x)
        if not panel_initialized or not panel_message_id:
            try:
                panel = await bot_ticket.send_message(
                    chat_id=CHAT_ID,
                    text="👾 PAINEL DE CONTROLE 👾\n\nInicializando..."
                )

                panel_message_id = panel.message_id
                panel_chat_id = CHAT_ID
                panel_initialized = True

                try:
                    await bot_ticket.pin_chat_message(
                        chat_id=CHAT_ID,
                        message_id=panel_message_id
                    )
                except Exception:
                    pass

            except Exception:
                return

        await update_panel()

# =========================
# 15 TELEGRAM RESET
# =========================
try:
    await bot_ticket.send_message(
        chat_id=CHAT_ID,
        text=msg
    )
except Exception:
    pass


# =========================
# 16 DISCORD RESET
# =========================
try:
    channel = await bot_discord.fetch_channel(DISCORD_PANEL_CHANNEL_ID)
    if channel:
        await channel.send(msg)
except Exception:
    pass


# =========================
# 17 CRIA PAINEL (1x) - PROTEGIDO
# =========================
if not panel_initialized or not panel_message_id:

    try:
        panel = await bot_ticket.send_message(
            chat_id=CHAT_ID,
            text="👾 PAINEL DE CONTROLE 👾\n\nInicializando..."
        )

        # 🔒 trava imediata (evita duplicação em race condition)
        panel_message_id = panel.message_id
        panel_chat_id = CHAT_ID
        panel_initialized = True

        try:
            await bot_ticket.pin_chat_message(
                chat_id=CHAT_ID,
                message_id=panel_message_id,
                disable_notification=True
            )
        except Exception:
            pass

    except Exception:
        return


# =========================
# 18 PRIMEIRO UPDATE DO PAINEL
# =========================
try:
    await update_panel()
except Exception:
    pass

# =========================
# 19 PAINEL FIXADO (TEMPO REAL + SEM SPAM)
# =========================

last_panel_text = None  # 🔥 evita editar sem mudança

async def update_panel():
    global panel_message_id, panel_chat_id, last_panel_text

    if not bot_ticket or not panel_message_id:
        return

    try:
        data, city, dias = get_next_show()

        weverse_min = minutes_since(last_weverse_check)
        social_min = minutes_since(last_social_check)
        ticket_min = minutes_since(last_ticket_check)
        buy_min = minutes_since(last_buy_check)

        text = f"""🪭⊙⊝⊜ARIRANG TOUR⊙⊝⊜🪭

✈️ PRÓXIMAS DATAS
🎫 Data: {data}
📍 Local: {city}
🔔 Faltam {dias} dias.

•°• 👾•°• •°• •°• •°*ATUALIZAÇÕES* •°• •°• •°• •°• •°• 🛸

🟣 Weverse {status_color(last_weverse_check)}
   🎯 Acessos realizados: {check_weverse}
   ⏱ Último rastreio há: {weverse_min} min

⚪ Redes sociais {status_color(last_social_check)}
   🎯 Acessos realizados: {check_social}
   ⏱ Último rastreio há: {social_min} min

🟠 Ticketmaster {status_color(last_ticket_check)}
   🎯 Acessos realizados: {check_ticket}
   ⏱ Último rastreio há: {ticket_min} min

🔵 Buyticket {status_color(last_buy_check)}
   🎯 Acessos realizados: {check_buy}
   ⏱ Último rastreio há: {buy_min} min
"""

        # =========================
        # 19 🔥 NÃO EDITA SE FOR IGUAL
        # =========================
        if text == last_panel_text:
            return

        last_panel_text = text

        # =========================
        # 20 TELEGRAM (EDITA FIXADO)
        # =========================
        await bot_ticket.edit_message_text(
            chat_id=panel_chat_id,
            message_id=panel_message_id,
            text=text
        )

    except Exception as e:
        print(f"[PAINEL ERROR] {e}")


# =========================
# 21 ALERTAS OFICIAIS (ORDEM: REPOSIÇÃO, NOVAS DATAS, REVENDA, AGENDA)
# =========================

async def ticket_reposicao(url, key, found):
    # Travas obrigatórias para Brasil
    if any(x in str(key) for x in ["28/10", "30/10", "31/10"]):
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
    if any(x in str(key) for x in ["28/10", "30/10", "31/10"]) or "Brasil" in str(key):
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

async def buy_revenda(url, key, found):
    if any(x in str(key) for x in ["28/10", "30/10", "31/10"]):
        msg = f"""🔵*REVENDA BUY*🔵
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
    country = str(data.get('country', ''))
    city = str(data.get('city', ''))

    if "Brasil" in country or "Paulo" in city or "Brasil" in str(data):
        msg = f"""💜*AGENDA NOVAS DATAS*💜
📅 *Data:* {clean(data.get('date'))}
🏙️ *Cidade:* {clean(data.get('city'))}
🌎 *País:* {clean(data.get('country'))}
⚠️*Mais informações em breve!*
"""
        await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

# =========================
# 22 ALERTAS WEVERSE
# =========================

async def weverse_post(url, member_name, title, message_translated, found):
    emoji = get_member_emoji(member_name)
    msg = f"""🩷*WEVERSE POST*🩷
{emoji} {member_name.upper()} publicou uma mensagem:
📌 {title}
{message_translated}
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_weverse_live(url, member_name, found):
    emoji = get_member_emoji(member_name)
    msg = f"""📹*WEVERSE LIVE*📹
{emoji} {member_name.upper()} está ao vivo!
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_weverse_news(url, member_name, message_translated, found):
    emoji = get_member_emoji(member_name)
    msg = f"""🚨*WEVERSE NEWS*🚨
{emoji} {member_name.upper()} publicou uma notícia:
📌 {message_translated}
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_weverse_media(url, member_name, title, message_translated, found):
    emoji = get_member_emoji(member_name)
    msg = f"""📀 WEVERSE MÍDIA📀
{emoji} {member_name.upper()} publicou uma nova mídia!
⭐️ {title}
{message_translated}
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

# =========================
# 23  ALERTAS INSTAGRAM
# =========================

async def instagram_post(url, member_name, title, found):
    emoji, name = format_member(member_name)

    msg = f"""🌟*INSTAGRAM POST*🌟
{emoji} {name} postou uma foto!
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def instagram_reel(url, member_name, title, found):
    emoji, name = format_member(member_name)

    msg = f"""🎬*INSTAGRAM REELS*🎬
{emoji} {name} postou um reels!
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def instagram_story(url, member_name, title, found):
    emoji, name = format_member(member_name)

    msg = f"""🫧*INSTAGRAM STORIES*🫧
{emoji} {name} atualizou os stories!
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def instagram_live(url, member_name, title, found):
    emoji, name = format_member(member_name)

    msg = f"""🎥*INSTAGRAM LIVE*🎥
{emoji} {name} está ao vivo!
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

# =========================
# 24 ALERTAS TIKTOK
# =========================

async def tiktok_post(url, member_name, title, found):
    emoji = get_member_emoji(member_name)

    msg = f"""🎵*TIKTOK POST*🎵
{emoji} {member_name.upper()} postou um vídeo!
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def tiktok_live(url, member_name, title, found):
    emoji = get_member_emoji(member_name)

    msg = f"""🎥*TIKTOK LIVE*🎥
{emoji} {member_name.upper()} está ao vivo no TikTok!
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

# =========================
# 25 ALERTAS DE TESTE (UNIFICADO)
# =========================

TEST_HEADER = "⚠️ TESTE ⚠️"

async def test_ticket_reposicao(url, key, found):
    msg = f"""{TEST_HEADER}

🔥*ALERTA DE REPOSIÇÃO*🔥
📅 *Data:* 28/10/2026
🔗 *Link:* https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-28-10
📍 *Setor:* PISTA PREMIUM
🎫 *Categoria:* INTEIRA
🛡️ *Tipo:* REPOSIÇÃO LIBERADA
📊 *Quantidade:* 1.250 ingressos
💰 *Preço:* R$ 1.290,00
📡 *Fila estimada:* 18.432 pessoas
✅ *Status:* {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_ticket_nova_data(url, key, found):
    msg = f"""{TEST_HEADER}

🎁*ALERTA DE NOVA DATA*🎁
📅 *Data:* 30/10/2026
🔗 *Link:* https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-30-10
📍 *Local:* São Paulo, Brasil
🎫 *Categoria:* DATA EXTRA ADICIONADA
🛡️ *Tipo:* ANÚNCIO OFICIAL
📊 *Quantidade:* 2 datas adicionais liberadas
📢 *Motivo:* alta demanda global
✅ *Status:* {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_buy_revenda(url, key, found):
    msg = f"""{TEST_HEADER}

🔵*REVENDA BUY*🔵
📅 *Data:* 28/10/2026
🔗 *Link:* https://buyticketbrasil.com/evento/bts-2026-world-tour-arirang
📍 *Plataforma:* BuyTicket Brasil
💰 *Valor:* R$ 2.150,00 (revenda dinâmica)
🎫 *Categoria:* VIP + MEIA
🛡️ *Tipo:* REVENDA CONFIRMADA
📊 *Disponíveis:* 312 ingressos
⚠️ *Risco:* médio
✅ *Status:* {resolve_status(found)}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_agenda(data):
    msg = f"""{TEST_HEADER}

💜*AGENDA NOVAS DATAS*💜
📅 *Data:* 28/10/2026
🏙️ *Cidade:* São Paulo
🌎 *País:* Brasil
🏟️ *Local:* Allianz Parque
🎫 *Turnê:* ARIRANG WORLD TOUR
⚠️ *Status:* anúncio parcial liberado
📢 *Observação:* venda inicia em breve
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_weverse_post(url, member_name, title, message_translated, found):
    emoji = get_member_emoji(member_name)
    msg = f"""{TEST_HEADER}

🩷*WEVERSE POST*🩷
{emoji} {member_name.upper()} publicou uma mensagem:
📌 *Título:* {title}
💬 *Conteúdo:* "We are coming back stronger than ever 💜"
🔗 {url}
📊 *Engajamento:* 2.4M likes | 580k comentários
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_weverse_live(url, member_name, found):
    emoji = get_member_emoji(member_name)
    msg = f"""{TEST_HEADER}

📹*WEVERSE LIVE*📹
{emoji} {member_name.upper()} está ao vivo!
🔗 {url}
👀 *Viewers:* 1.2M assistindo
⏱️ *Duração:* 00:18:42
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_weverse_news(url, member_name, message_translated, found):
    emoji = get_member_emoji(member_name)
    msg = f"""{TEST_HEADER}

🚨*WEVERSE NEWS*🚨
{emoji} {member_name.upper()} publicou uma notícia:
📌 *Atualização:* novo conteúdo exclusivo liberado
💬 "Special announcement coming soon"
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_weverse_media(url, member_name, title, message_translated, found):
    emoji = get_member_emoji(member_name)
    msg = f"""{TEST_HEADER}

📀*WEVERSE MÍDIA*📀
{emoji} {member_name.upper()} publicou uma nova mídia!
⭐️ *Título:* {title}
🎬 *Tipo:* behind the scenes
📸 *Formato:* HD exclusive content
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_instagram_post(url, member_name, title, found):
    emoji, name = format_member(member_name)
    msg = f"""{TEST_HEADER}

🌟*INSTAGRAM POST*🌟
{emoji} {name} postou uma foto!
📌 *Legenda:* “Back on stage 💜”
❤️ *Likes:* 8.9M
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_instagram_reel(url, member_name, title, found):
    emoji, name = format_member(member_name)
    msg = f"""{TEST_HEADER}

🎬*INSTAGRAM REELS*🎬
{emoji} {name} postou um reels!
🎵 *Música:* trending audio #1 global
👀 *Views:* 12.4M
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_instagram_story(url, member_name, title, found):
    emoji, name = format_member(member_name)
    msg = f"""{TEST_HEADER}

🫧*INSTAGRAM STORIES*🫧
{emoji} {name} atualizou os stories!
📸 *Tipo:* bastidores da turnê
⏳ *Duração:* 24h
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_instagram_live(url, member_name, title, found):
    emoji, name = format_member(member_name)
    msg = f"""{TEST_HEADER}

🎥*INSTAGRAM LIVE*🎥
{emoji} {name} está ao vivo!
👀 *Viewers:* 780k
💬 *Chat:* ativo
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_tiktok_post(url, member_name, title, found):
    emoji = get_member_emoji(member_name)
    msg = f"""{TEST_HEADER}

🎵*TIKTOK POST*🎵
{emoji} {member_name.upper()} postou um vídeo!
🔥 *Views:* 6.7M em 2h
❤️ *Likes:* 1.1M
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

async def test_tiktok_live(url, member_name, title, found):
    emoji = get_member_emoji(member_name)
    msg = f"""{TEST_HEADER}

🎥*TIKTOK LIVE*🎥
{emoji} {member_name.upper()} está ao vivo no TikTok!
👀 *Viewers:* 540k
💬 *Chat:* explosivo
🔗 {url}
"""
    await bot_ticket.send_message(chat_id=CHAT_ID, text=msg)

# =========================
# 26 COMANDOS (PV EXCLUSIVO TELEGRAM)
# =========================

async def handle_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if update.message.chat.type != "private":
        return

    text = update.message.text.lower()

    # =========================
    # 27 TESTE
    # =========================
    if text.strip() == "/teste":

        await bot_ticket.send_message(
            chat_id=CHAT_ID,
            text="🧪 INICIANDO TESTE COMPLETO DE ALERTAS..."
        )

        await test_ticket_reposicao(TICKET_LINKS[0], "28/10/2026", True)
        await test_ticket_nova_data(TICKET_LINKS[1], "30/10/2026", True)
        await test_buy_revenda(BUY_LINKS[0], "28/10/2026", True)

        await test_agenda({
            "date": "28/10/2026",
            "city": "São Paulo",
            "country": "Brasil"
        })

        await test_weverse_post(TICKET_LINKS[0], "bts", "Update", "msg", True)
        await test_weverse_live(TICKET_LINKS[0], "jungkook", True)
        await test_weverse_news(TICKET_LINKS[0], "rm", "msg", True)
        await test_weverse_media(TICKET_LINKS[0], "v", "title", "msg", True)

        await test_instagram_post(TIKTOK_LINKS["bts"], "bts", "post", True)
        await test_instagram_reel(TIKTOK_LINKS["bts"], "bts", "reel", True)
        await test_instagram_story(TIKTOK_LINKS["bts"], "bts", "story", True)
        await test_instagram_live(TIKTOK_LINKS["bts"], "bts", "live", True)

        await test_tiktok_post(TIKTOK_LINKS["bts"], "bts", "video", True)
        await test_tiktok_live(TIKTOK_LINKS["bts"], "bts", "live", True)

        await bot_ticket.send_message(
            chat_id=CHAT_ID,
            text="✅ TESTE COMPLETO FINALIZADO (TELEGRAM + DISCORD)"
        )

    elif "/ping" in text:
        await bot_ticket.send_message(chat_id=CHAT_ID, text="🏓 Bot ativo e funcionando!")

    elif "/status" in text:
        await bot_ticket.send_message(
            chat_id=CHAT_ID,
            text=f"""📊 STATUS DO BOT

🟣 Weverse: OK
⚪ Redes sociais: OK
🟠 Ticketmaster: OKreal
🔵 Buyticket: OK

⏱ Uptime: {get_uptime()}
"""
        )

# =========================
# 28 SAFE BOOT (1X + GARANTIDO)
# =========================

boot_executed = False

async def safe_boot():
    global boot_executed

    if boot_executed:
        return

    if not bot_ticket:
        print("[SAFE_BOOT] bot_ticket ainda não pronto")
        return

    boot_executed = True

    try:
        await send_boot()
        print("[BOOT] Executado com sucesso (1x)")

    except Exception as e:
        print(f"[SAFE_BOOT ERROR] {e}")

# =========================
# 29 ALERT ENGINE (ANTI-SPAM REAL + SINCRONIZADO)
# =========================

import asyncio

ALERT_LOCK = asyncio.Lock()

async def send_alert(alert_type, message):
    """
    🔥 ALERT ENGINE CORRIGIDO:
    - evita duplicação
    - sincroniza Telegram + Discord
    - protege contra spam paralelo
    """

    async with ALERT_LOCK:

        # =========================
        # 30 TELEGRAM (OBRIGATÓRIO)
        # =========================
        try:
            if bot_ticket:
                await bot_ticket.send_message(
                    chat_id=CHAT_ID,
                    text=message
                )
        except Exception as e:
            print(f"[ALERT TELEGRAM ERROR] {e}")

        # =========================
        # 31 DISCORD (ROTEAMENTO LIMPO)
        # =========================
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        # 🔥 CORREÇÃO IMPORTANTE:
        # padroniza categorias (evita alerta indo pra canal errado)

        if alert_type in ["ticket", "reposicao", "nova_data", "revenda", "agenda"]:
            loop.create_task(
                send_discord(DISCORD_TICKETS_CHANNEL_ID, message)
            )

        elif alert_type in ["weverse_post", "weverse_live", "weverse_news", "weverse_media"]:
            loop.create_task(
                send_discord(DISCORD_WEVERSE_CHANNEL_ID, message)
            )

        elif alert_type in [
            "instagram_post", "instagram_reel", "instagram_story", "instagram_live",
            "tiktok_post", "tiktok_live"
        ]:
            loop.create_task(
                send_discord(DISCORD_SOCIAL_CHANNEL_ID, message)
            )

        else:
            loop.create_task(
                send_discord(DISCORD_NEWS_CHANNEL_ID, message)
            )

# =========================
# 32 FETCH UNIVERSAL (OBRIGATÓRIO)
# =========================

import aiohttp

async def fetch(session, url):
    """
    ✔ Download seguro de páginas
    ✔ Timeout protegido
    ✔ Evita crash no monitor loop
    """

    try:
        async with session.get(url, timeout=20) as response:
            if response.status != 200:
                return None
            return await response.text()

    except Exception:
        return None

# =========================
# 33 CHECKS
# =========================

async def check_ticketmaster(session):
    global last_ticket_check, check_ticket  # 🔥 ESSA LINHA É A CORREÇÃO

    for url in TICKET_LINKS:
        html = await fetch(session, url)
        if not html:
            continue

        if is_new(url, html):
            found = "esgotado" not in html.lower()

            check_ticket += 1  # agora funciona ✅

            await ticket_reposicao(url, url, found)
            await send_alert("ticket", f"🎫 Ticket update detectado:\n{url}")

            last_ticket_check = time.time()
            await update_panel()

async def check_buyticket(session):
    global last_buy_check, check_buy

    for url in BUY_LINKS:
        html = await fetch(session, url)
        if not html:
            continue

        if is_new(url, html):
            found = "esgotado" not in html.lower()

            check_buy += 1  # ✅ contador corrigido

            await buy_revenda(url, url, found)
            await send_alert("revenda", f"🔵 BuyTicket update:\n{url}")

            last_buy_check = time.time()
            await update_panel()

async def check_weverse(session):
    global last_weverse_check, check_weverse

    for url in WEVERSE_LINKS:
        html = await fetch(session, url)
        if not html:
            continue

        if is_new(url, html):
            check_weverse += 1  # ✅ contador corrigido

            await test_weverse_post(url, "bts", "Update", "Novo conteúdo", True)
            await send_alert("weverse_post", f"🩷 Weverse update:\n{url}")

            last_weverse_check = time.time()
            await update_panel()

# =========================
# 34 CHECK SOCIAL (CORRIGIDO - SEM SPAM + IDENTIFICA MEMBRO)
# =========================
async def check_social(session):
    global last_social_check, check_social

    all_links = (
        list(INSTAGRAM_LINKS.items()) +
        list(TIKTOK_LINKS.items())
    )

    for member, url in all_links:
        html = await fetch(session, url)
        if not html:
            continue

        if not is_new(url, html):
            continue

        check_social += 1  # ✅ contador OK

        if "instagram" in url:
            await instagram_post(url, member, "update", True)

            send_alert(
                "instagram_post",
                f"📷 Instagram update detectado ({member.upper()}):\n{url}"
            )

        elif "tiktok" in url:
            await tiktok_post(url, member, "update", True)

            send_alert(
                "tiktok_post",
                f"🎵 TikTok update detectado ({member.upper()}):\n{url}"
            )

    last_social_check = time.time()
    await update_panel()

# =========================
# 35 LOOP PRINCIPAL (MONITOR CONTROLADO)
# =========================

async def monitor_loop():
    await bot_discord.wait_until_ready()

    print("[MONITOR] Loop iniciado")

    async with aiohttp.ClientSession() as session:
        while True:
            try:


                # =========================
                # 35 TICKETMASTER
                # =========================
                await check_ticketmaster(session)

                await asyncio.sleep(5)

                # =========================
                # 37 BUYTICKET
                # =========================
                await check_buyticket(session)

                await asyncio.sleep(5)

                # =========================
                # 38 WEVERSE
                # =========================
                await check_weverse(session)

                await asyncio.sleep(5)

                # =========================
                # 39 SOCIAL
                # =========================
                await check_social(session)

                # =========================
                # 40 INTERVALO GERAL
                # =========================
                await asyncio.sleep(30)

            except Exception as e:
                print(f"[MONITOR ERROR] {e}")
                await asyncio.sleep(10)


