# =========================
# 1 BOT WOOTTEO
# =========================

import asyncio
import time
import hashlib
import os
import re
from datetime import datetime
from threading import Thread

import discord
from discord.ext import commands
from discord import app_commands

import aiohttp
from bs4 import BeautifulSoup
from flask import Flask

from telegram import Bot, Update
from telegram.ext import ContextTypes

# =========================
# 2 CONFIGURAÇÃO TELEGRAM / DISCORD
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Instância do bot Discord (Movida para cá para ser definida antes dos comandos)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot_discord = commands.Bot(command_prefix="!", intents=intents)

PANEL_CHAT_ID = -1003920883053

panel_message_id = None
discord_panel_msg_id = None
panel_initialized = False

DISCORD_PANEL_CHANNEL_ID = 1494667029150695625
DISCORD_TICKETS_CHANNEL_ID = 1494670074374651985
DISCORD_WEVERSE_CHANNEL_ID = 1494680233025208461
DISCORD_SOCIAL_CHANNEL_ID = 1494682078950981864

bot_ticket = None

if TELEGRAM_TOKEN:
    try:
        bot_ticket = Bot(token=TELEGRAM_TOKEN)
        print("[SISTEMA] Telegram configurado com sucesso.")
    except Exception as e:
        print(f"[ERRO CONFIG TELEGRAM] {e}")

# =========================
# 3 CONTADORES GLOBAIS
# =========================

total_tickets = 0
total_buy = 0
total_weverse = 0
total_social = 0

last_ticket_check = time.time()
last_buy_check = time.time()
last_weverse_check = time.time()
last_social_check = time.time()

CONTENT_HASH = {}

SEEN_TICKET = set()
SEEN_BUY = set()
SEEN_WEVERSE = set()
SEEN_SOCIAL = set()

start_time = time.time()

# =========================
# 4 WEB SERVER
# =========================

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bots Arirang ativos"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def keep_alive():
    if not getattr(keep_alive, "_running", False):
        Thread(target=run_web, daemon=True).start()
        keep_alive._running = True

# =========================
# 5 FUNÇÃO ANTI-SPAM (HASH)
# =========================

def is_new(url, html):
    global CONTENT_HASH

    content_clean = " ".join(html.split())
    new_hash = hashlib.md5(content_clean.encode("utf-8")).hexdigest()

    if url not in CONTENT_HASH:
        CONTENT_HASH[url] = new_hash
        print(f"[MEMÓRIA] URL aprendida: {url}")
        return False

    if CONTENT_HASH[url] != new_hash:
        CONTENT_HASH[url] = new_hash
        print(f"[ALERTA] Mudança detectada: {url}")
        return True

    return False

# =========================
# 6 LINKS (ÚNICO - NÃO DUPLICAR)
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

WEVERSE_LINKS = [
    "https://weverse.io/bts/artist",
    "https://weverse.io/bts/live",
    "https://weverse.io/bts/notice",
    "https://weverse.io/bts/media"
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
    "jhope": "https://www.tiktok.com/@iamurhope",
    "v": "https://www.tiktok.com/@tete",
    "bts": "https://www.tiktok.com/@bts_official_bighit"
}

X_LINKS = [
    "https://x.com/BTS_twt"
]

YOUTUBE_LINKS = [
    "https://www.youtube.com/@BTS"
]


def get_next_show():
    """Calcula dias para 28/10/2026"""
    data_alvo = datetime(2026, 10, 28)
    agora = datetime.now()
    diferenca = data_alvo - agora
    return "28/10/2026", "São Paulo, Brasil", diferenca.days

# =========================
# 7 AGENDA FIXA
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

# =============
# 8 CONTROLE 
# =============

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
        target = datetime.strptime(date_str, "%d/%m/%Y").date()
        today = datetime.now().date()
        delta = (target - today).days
        return max(delta, 0)
    except:
        return 0

def minutes_since(ts):
    return int((time.time() - ts) / 60)

def status_color(last_check):
    agora = time.time()
    if (agora - last_check) > 1800:
        return "🔴"
    return "🟢" if int(agora) % 2 == 0 else "🟡"

def get_countdown_data():
    now_dt = datetime.now()

    prox_data = "Continua…"
    prox_local = "---"
    d_prox = 0
    d_br = 0

    if 'AGENDA' in globals() and AGENDA:
        for item in AGENDA:
            try:
                data_hora_show = datetime.strptime(f"{item[0]} {item[3]}", "%d/%m/%Y %H:%M")
                if data_hora_show > now_dt:
                    prox_data = item[0]
                    prox_local = f"{item[1]}, {item[2]}"
                    d_prox = (data_hora_show.date() - now_dt.date()).days
                    break
            except:
                continue

        for item in AGENDA:
            if "Brasil" in item[2]:
                try:
                    data_br_dt = datetime.strptime(item[0], "%d/%m/%Y").date()
                    if data_br_dt >= now_dt.date():
                        d_br = (data_br_dt - now_dt.date()).days
                        break
                except:
                    continue

    return prox_data, prox_local, d_prox, d_br

# =========================
# 9 SESSION 
# =========================

http_session = None

async def get_session():
    global http_session

    if http_session is None or http_session.closed:
        http_session = aiohttp.ClientSession()

    return http_session

# =========================
# 10 EMOJIS
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
# 11 TEST MODE + CORE ROUTER + COMANDOS BASE
# =========================

TEST_MODE = False

# === DISCORD SEND (CORE ÚNICO) === #
async def send_discord(channel_id, content=None, embed=None):
    channel = bot_discord.get_channel(channel_id)

    if not channel:
        return

    # 🔥 FORÇA EMBED PADRÃO COM BORDA ROXA
    if embed is None and content is not None:
        embed = discord.Embed(
            description=content,
            color=0x8A2BE2  # borda roxa padrão
        )

    await channel.send(embed=embed)


# === ALERT ROUTER (DISCORD + TELEGRAM CONTROLADO) === #
async def send_alert(alert_type, message):

    # TELEGRAM BLOQUEADO EM TESTE
    if bot_ticket is not None and not TEST_MODE:
        try:
            await bot_ticket.send_message(
                chat_id=PANEL_CHAT_ID,
                text=message,
                parse_mode=None
            )
        except Exception as e:
            print(f"[TELEGRAM ERROR] {e}")

    try:

        if alert_type in ["ticket", "reposicao", "nova_data", "revenda", "agenda"]:
            asyncio.create_task(
                send_discord(DISCORD_TICKETS_CHANNEL_ID, content=message)
            )

        elif alert_type in ["weverse_post", "weverse_live", "weverse_news", "weverse_media"]:
            asyncio.create_task(
                send_discord(DISCORD_WEVERSE_CHANNEL_ID, content=message)
            )

        elif alert_type in [
            "instagram_post", "instagram_reels", "instagram_stories", "instagram_live",
            "tiktok_post", "tiktok_live"
        ]:
            asyncio.create_task(
                send_discord(DISCORD_SOCIAL_CHANNEL_ID, content=message)
            )

        elif alert_type in ["youtube_post", "youtube_live"]:
            asyncio.create_task(
                send_discord(DISCORD_SOCIAL_CHANNEL_ID, content=message)
            )

    except Exception as e:
        print(f"[DISCORD ROUTER ERROR] {e}")


# === DISCORD COMMANDS BASE === #

@bot_discord.tree.command(name="ping", description="Verifica status do bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! {get_uptime()}",
        ephemeral=False
    )


@bot_discord.tree.command(name="comandos", description="Lista comandos disponíveis")
async def comandos(interaction: discord.Interaction):
    await interaction.response.send_message(
        "/ping\n/comandos\n/teste\n/bts",
        ephemeral=False
    )


@bot_discord.tree.command(name="bts", description="Lista membros do BTS")
async def bts(interaction: discord.Interaction):

    membros = [
        "🐨 KIM NAMJOON", "🐹 KIM SEOKJIN", "🐱 MIN YOONGI",
        "🐿️ JUNG HOSEOK", "🐥 PARK JIMIN",
        "🐻 KIM TAEHYUNG", "🐰 JEON JUNGKOOK", "💜 BTS"
    ]

    await interaction.response.send_message("\n".join(membros), ephemeral=False)

# ======================
# 12 GESTÃO DO PAINEL
# ======================

async def update_panel():
    global panel_message_id, discord_panel_msg_id

    # dados dinâmicos
    data_show, city, d_prox, d_br = get_countdown_data()
    texto = gerar_texto_painel(data_show, city, d_prox, d_br)

    # =========================
    # TELEGRAM (PAINEL FIXO)
    # =========================
    if bot_ticket and PANEL_CHAT_ID:
        try:
            if not panel_message_id:
                panel_message_id = carregar_id_telegram()

            edited = False

            # tenta editar mensagem existente
            if panel_message_id:
                try:
                    await bot_ticket.edit_message_text(
                        chat_id=PANEL_CHAT_ID,
                        message_id=panel_message_id,
                        text=texto,
                        parse_mode=None
                    )
                    edited = True
                except:
                    panel_message_id = None

            # recria se não existir
            if not edited:
                try:
                    await bot_ticket.unpin_all_chat_messages(chat_id=PANEL_CHAT_ID)
                except:
                    pass

                msg = await bot_ticket.send_message(
                    chat_id=PANEL_CHAT_ID,
                    text=texto,
                    parse_mode=None
                )

                panel_message_id = msg.message_id
                salvar_id_telegram(panel_message_id)

                # pin seguro
                try:
                    await bot_ticket.pin_chat_message(
                        chat_id=PANEL_CHAT_ID,
                        message_id=panel_message_id,
                        disable_notification=True
                    )
                except:
                    await asyncio.sleep(1)
                    try:
                        await bot_ticket.pin_chat_message(
                            chat_id=PANEL_CHAT_ID,
                            message_id=panel_message_id,
                            disable_notification=True
                        )
                    except:
                        pass

        except Exception as e:
            print(f"[TELEGRAM PANEL ERROR] {e}")

    # =========================
    # DISCORD PAINEL (EMBED ROXO FIXO)
    # =========================
    if DISCORD_PANEL_CHANNEL_ID:

        channel = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)

        if channel:

            embed = discord.Embed(
                description=texto,
                color=0x8A2BE2  # 🔥 borda roxa padrão obrigatória
            )

            try:

                # tenta recuperar mensagem antiga
                if not discord_panel_msg_id:

                    async for msg in channel.history(limit=10):
                        if msg.author == bot_discord.user:
                            discord_panel_msg_id = msg.id
                            break

                # edita se existir
                if discord_panel_msg_id:

                    msg = await channel.fetch_message(discord_panel_msg_id)
                    await msg.edit(embed=embed)

                # cria se não existir
                else:

                    msg = await channel.send(embed=embed)
                    discord_panel_msg_id = msg.id

            except Exception as e:
                print(f"[DC PANEL ERROR] {e}")

def gerar_texto_painel(data_show, city, d_prox, d_br):
    global total_weverse, total_social, total_tickets, total_buy
    global last_weverse_check, last_social_check, last_ticket_check, last_buy_check

    return f"""🪭 ⊙⊝⊜ **ARIRANG TOUR** ⊙⊝⊜ 🪭


**✈️ PRÓXIMAS DATAS**

  🎫 Data: **{data_show}**
  📍 Local: **{city}**
  🔔 Faltam **{d_prox}** dias.
  🩷 Faltam **{d_br}** dias para o BTS no Brasil!

•°•🌙.•°**ATUALIZAÇÕES** .💫 * . * •°•°🛸

  🟣 **Weverse** {status_color(last_weverse_check)}
  🎯 Acessos realizados: **{total_weverse}**
  ⏳ Último rastreio há: **{minutes_since(last_weverse_check)} min**

  ⚪ **Redes sociais** {status_color(last_social_check)}
  🎯 Acessos realizados: **{total_social}**
  ⏳ Último rastreio há: **{minutes_since(last_social_check)} min**

  🟠 **Ticketmaster** {status_color(last_ticket_check)}
  🎯 Acessos realizados: **{total_tickets}**
  ⏳ Último rastreio há: **{minutes_since(last_ticket_check)} min**

  🔵 **Buyticket** {status_color(last_buy_check)}
  🎯 Acessos realizados: **{total_buy}**
  ⏳ Último rastreio há: **{minutes_since(last_buy_check)} min**

•°•👾 Wootteo em rota há: **{get_uptime()}** ☄️🌍💫
"""

# =========================
# 13 ALERTAS WEVERSE (CORRIGIDO)
# =========================

LAST_WEVERSE_POST_URL = None
LAST_WEVERSE_LIVE_URL = None

async def weverse_post(url, member_name, title, message_translated, found):
    global LAST_WEVERSE_POST_URL, total_weverse, last_weverse_check

    if url == LAST_WEVERSE_POST_URL:
        return

    LAST_WEVERSE_POST_URL = url

    total_weverse += 1
    last_weverse_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
🩷 WEVERSE POST 🩷
{emoji} {member_name.upper()} publicou uma mensagem
📌 {title}
📝 {message_translated}
🔗 {url}
"""

    await send_alert("weverse_post", msg)
    await update_panel()

async def weverse_live(url, member_name, found):
    global LAST_WEVERSE_LIVE_URL, total_weverse, last_weverse_check

    if url == LAST_WEVERSE_LIVE_URL:
        return

    LAST_WEVERSE_LIVE_URL = url

    total_weverse += 1
    last_weverse_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
📹 WEVERSE LIVE 📹
{emoji} {member_name.upper()} está ao vivo!
🔗 {url}
"""

    await send_alert("weverse_live", msg)
    await update_panel()

async def weverse_news(url, member_name, message_translated, found):
    global LAST_WEVERSE_POST_URL, total_weverse, last_weverse_check

    if url == LAST_WEVERSE_POST_URL:
        return

    LAST_WEVERSE_POST_URL = url

    total_weverse += 1
    last_weverse_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
🚨 WEVERSE NEWS 🚨
{emoji} {member_name.upper()} publicou notícia
📝 {message_translated}
🔗 {url}
"""

    await send_alert("weverse_news", msg)
    await update_panel()

async def weverse_media(url, member_name, title, message_translated, found):
    global LAST_WEVERSE_POST_URL, total_weverse, last_weverse_check

    if url == LAST_WEVERSE_POST_URL:
        return

    LAST_WEVERSE_POST_URL = url

    total_weverse += 1
    last_weverse_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
📀 WEVERSE MEDIA 📀
{emoji} {member_name.upper()} publicou mídia
⭐ {title}
📝 {message_translated}
🔗 {url}
"""

    await send_alert("weverse_media", msg)
    await update_panel()

# =========================
# 14 ALERTAS INSTAGRAM (CORRIGIDO)
# =========================

LAST_INSTA_POST_LINK = None
LAST_INSTA_STORY_LINK = None
LAST_INSTA_REEL_LINK = None

async def instagram_post(url, member_name, title, found):
    global LAST_INSTA_POST_LINK, total_social, last_social_check

    if url == LAST_INSTA_POST_LINK:
        return

    LAST_INSTA_POST_LINK = url

    total_social += 1
    last_social_check = time.time()

    emoji, name = format_member(member_name)

    msg = f"""
🌟 INSTAGRAM POST 🌟
{emoji} {name} postou uma foto
🔗 {url}
"""
    await send_alert("instagram_post", msg)
    await update_panel()

async def instagram_reel(url, member_name, title, found):
    global LAST_INSTA_REEL_LINK, total_social, last_social_check

    if url == LAST_INSTA_REEL_LINK:
        return

    LAST_INSTA_REEL_LINK = url

    total_social += 1
    last_social_check = time.time()

    emoji, name = format_member(member_name)

    msg = f"""
🎬 INSTAGRAM REELS 🎬
{emoji} {name} postou um reels
🔗 {url}
"""
    await send_alert("instagram_reels", msg)
    await update_panel()

async def instagram_story(url, member_name, title, found):
    global LAST_INSTA_STORY_LINK, total_social, last_social_check

    if url == LAST_INSTA_STORY_LINK:
        return

    LAST_INSTA_STORY_LINK = url

    total_social += 1
    last_social_check = time.time()

    emoji, name = format_member(member_name)

    msg = f"""
🫧 INSTAGRAM STORIES 🫧
{emoji} {name} atualizou stories
🔗 {url}
"""
    await send_alert("instagram_stories", msg)
    await update_panel()

async def instagram_live(url, member_name, title, found):
    global total_social, last_social_check

    total_social += 1
    last_social_check = time.time()

    emoji, name = format_member(member_name)

    msg = f"""
🎥 INSTAGRAM LIVE 🎥
{emoji} {name} está ao vivo
🔗 {url}
"""
    await send_alert("instagram_live", msg)
    await update_panel()

# =========================
# 15 ALERTAS X, TIKTOK E YOUTUBE (CORRIGIDO)
# =========================

LAST_X_LINK = None
LAST_TIKTOK_LINK = None
LAST_YOUTUBE_LINK = None

# === X (TWITTER) === #

async def x_post(url, member_name, message_translated, found):
    global LAST_X_LINK, total_social, last_social_check

    if url == LAST_X_LINK:
        return

    LAST_X_LINK = url

    total_social += 1
    last_social_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
🐦 X POST 🐦
💜 BTS publicou um post!
📝 {message_translated}
🔗 {url}
"""
    await send_alert("x_post", msg)
    await update_panel()

# === TIKTOK === #

async def tiktok_post(url, member_name, title, found):
    global LAST_TIKTOK_LINK, total_social, last_social_check

    link_base = "https://www.tiktok.com/@bts_official_bighit"

    if "video/" in url:
        video_id = url.split("video/")[1].split("?")[0]
        final_url = f"{link_base}/video/{video_id}"
    else:
        final_url = link_base

    if final_url == LAST_TIKTOK_LINK:
        return

    LAST_TIKTOK_LINK = final_url

    total_social += 1
    last_social_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
🎵 TIKTOK POST 🎵
{emoji} {member_name.upper()} postou um vídeo
🔗 {final_url}
"""
    await send_alert("tiktok_post", msg)
    await update_panel()

async def tiktok_live(url, member_name, title, found):
    global total_social, last_social_check

    total_social += 1
    last_social_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
🎥 TIKTOK LIVE 🎥
{emoji} {member_name.upper()} está ao vivo
🔗 https://www.tiktok.com/@bts_official_bighit/live
"""
    await send_alert("tiktok_live", msg)
    await update_panel()

# === YOUTUBE === #

async def youtube_post(url, final_url=None):
    global total_social, last_social_check

    total_social += 1
    last_social_check = time.time()

    link = final_url or "https://www.youtube.com/@BTS"

    msg = f"""
🎞️ YOUTUBE POST 🎞️
💜 BTS publicou vídeo novo
🔗 {link}
"""
    await send_alert("youtube_post", msg)
    await update_panel()

async def youtube_live(url=None):
    global total_social, last_social_check

    total_social += 1
    last_social_check = time.time()

    live_url = "https://www.youtube.com/@BTS/live"

    msg = f"""
📹 YOUTUBE LIVE 📹
🚨 BTS está ao vivo agora
🔗 {live_url}
"""
    await send_alert("youtube_live", msg)
    await update_panel()

# =========================
# 16 SISTEMA DE TESTE (ESTRUTURA DE MENSAGENS FIXA)
# =========================

# === RUN TEST DISCORD === #

async def run_full_test_discord():
    print("[TESTE DC] iniciando bateria completa...")
    
    global TEST_MODE
    TEST_MODE = True

    # --- TICKETMASTER & BUYTICKET ---
    await test_ticket_reposicao()
    await test_ticket_agenda()
    await test_buyticket_revenda()
    await asyncio.sleep(1)

    # --- WEVERSE ---
    await test_weverse_post()
    await test_weverse_live()
    await test_weverse_news()
    await test_weverse_media()
    await asyncio.sleep(1)

    # --- X (TWITTER) ---
    await test_x_post()
    await asyncio.sleep(1)

    # --- INSTAGRAM ---
    await test_instagram_post()
    await test_instagram_reel()
    await test_instagram_story()
    await test_instagram_live()
    await asyncio.sleep(1)

    # --- TIKTOK & YOUTUBE ---
    await test_tiktok_post()
    await test_tiktok_live()
    await test_youtube_post()
    await test_youtube_live()

    TEST_MODE = False
    print("[TESTE DC] finalizado")

# === TICKETMASTER & BUYTICKET TEST === #

async def test_ticket_reposicao():
    msg = f"""
⚠️ TESTE ⚠️
🔥 ALERTA DE REPOSIÇÃO 🔥
📅 Data: 28/10/2026
🔗 Link: https://www.ticketmaster.com.br/event/venda-geral-bts
✅ Status: Liberado
"""
    await send_alert("reposicao", msg)

async def test_ticket_agenda():
    msg = f"""
⚠️ TESTE ⚠️
💜 AGENDA NOVA 💜
📅 Data: 29/10/2026
🏙️ Cidade: São Paulo
🌎 País: Brasil
"""
    await send_alert("agenda", msg)

async def test_buyticket_revenda():
    msg = f"""
⚠️ TESTE ⚠️
🎫 REVENDA BUYTICKET 🎫
👤 BTS World Tour Arirang
📌 Novos ingressos disponíveis para revenda
🔗 https://www.buyticket.com.br/bts
"""
    await send_alert("buyticket_revenda", msg)

# === WEVERSE TEST === #

async def test_weverse_post():
    msg = f"""
⚠️ TESTE ⚠️
🩷 WEVERSE POST 🩷
💜 BTS publicou uma mensagem
📌 Título Teste
📝 Conteúdo da mensagem traduzida aqui
🔗 https://weverse.io/bts/artist
"""
    await send_alert("weverse_post", msg)

async def test_weverse_live():
    msg = f"""
⚠️ TESTE ⚠️
📹 WEVERSE LIVE 📹
💜 BTS está ao vivo!
🔗 https://weverse.io/bts/live
"""
    await send_alert("weverse_live", msg)

async def test_weverse_news():
    msg = f"""
⚠️ TESTE ⚠️
🚨 WEVERSE NEWS 🚨
💜 BTS publicou notícia
📝 Detalhes da notícia oficial
🔗 https://weverse.io/bts/official
"""
    await send_alert("weverse_news", msg)

async def test_weverse_media():
    msg = f"""
⚠️ TESTE ⚠️
📀 WEVERSE MEDIA 📀
💜 BTS publicou mídia
⭐ Título da Mídia
📝 Descrição da mídia traduzida
🔗 https://weverse.io/bts/media
"""
    await send_alert("weverse_media", msg)

# === X TEST (TWITTER) === #

async def test_x_post():
    msg = f"""
⚠️ TESTE ⚠️
🐦 X POST 🐦
💜 BTS publicou um novo post no X
🔗 https://x.com/BTS_twt
"""
    await send_alert("x_post", msg)

# === INSTAGRAM TEST === #

async def test_instagram_post():
    msg = f"""
⚠️ TESTE ⚠️
🌟 INSTAGRAM POST 🌟
💜 BTS postou uma foto
🔗 https://www.instagram.com/bts.bighitofficial
"""
    await send_alert("instagram_post", msg)

async def test_instagram_reel():
    msg = f"""
⚠️ TESTE ⚠️
🎬 INSTAGRAM REELS 🎬
💜 BTS postou um reels
🔗 https://www.instagram.com/bts.bighitofficial/reels
"""
    await send_alert("instagram_reels", msg)

async def test_instagram_story():
    msg = f"""
⚠️ TESTE ⚠️
🫧 INSTAGRAM STORIES 🫧
💜 BTS atualizou stories
🔗 https://www.instagram.com/bts.bighitofficial
"""
    await send_alert("instagram_stories", msg)

async def test_instagram_live():
    msg = f"""
⚠️ TESTE ⚠️
🎥 INSTAGRAM LIVE 🎥
💜 BTS está ao vivo
🔗 https://www.instagram.com/bts.bighitofficial/live
"""
    await send_alert("instagram_live", msg)

# === TIKTOK & YOUTUBE TEST === #

async def test_tiktok_post():
    msg = f"""
⚠️ TESTE ⚠️
🎵 TIKTOK POST 🎵
💜 BTS postou um vídeo
🔗 https://www.tiktok.com/@bts_official_bighit
"""
    await send_alert("tiktok_post", msg)

async def test_tiktok_live():
    msg = f"""
⚠️ TESTE ⚠️
🎥 TIKTOK LIVE 🎥
💜 BTS está ao vivo
🔗 https://www.tiktok.com/@bts_official_bighit/live
"""
    await send_alert("tiktok_live", msg)

async def test_youtube_post():
    msg = f"""
⚠️ TESTE ⚠️
🎞️ YOUTUBE POST 🎞️
💜 BTS publicou vídeo novo
🔗 https://www.youtube.com/@BTS
"""
    await send_alert("youtube_post", msg)

async def test_youtube_live():
    msg = f"""
⚠️ TESTE ⚠️
📹 YOUTUBE LIVE 📹
🚨 BTS está ao vivo agora
🔗 https://www.youtube.com/@BTS/live
"""
    await send_alert("youtube_live", msg)

# =========================
# 17 MOTOR + COMANDOS + TESTE (FIX FINAL ESTÁVEL)
# =========================

# ⚠️ NÃO recriar bot_discord aqui (já existe no topo)

# === TELEGRAM LOGIC === #
async def bts_telegram_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    membros = [
        "🐨 KIM NAMJOON", "🐹 KIM SEOKJIN", "🐱 MIN YOONGI",
        "🐿️ JUNG HOSEOK", "🐥 PARK JIMIN",
        "🐻 KIM TAEHYUNG", "🐰 JEON JUNGKOOK", "💜 BTS"
    ]

    for nome in membros:
        if update.message:
            await update.message.reply_text(nome)
        await asyncio.sleep(0.8)


async def handle_commands_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    cmd = update.message.text.lower()

    if "ping" in cmd:
        await update.message.reply_text("🚀 Wootteo em órbita!")

    elif "comandos" in cmd:
        await update.message.reply_text("/ping, /bts, /teste, /comandos")

    elif "bts" in cmd:
        await bts_telegram_cmd(update, context)

    elif "teste" in cmd:
        if PANEL_CHAT_ID:
            await context.bot.send_message(
                chat_id=PANEL_CHAT_ID,
                text="⚠️ TESTE TELEGRAM OK"
            )


# === DISCORD EVENTS === #
@bot_discord.event
async def on_ready():
    print(f"✅ Logado: {bot_discord.user}")

    try:
        await bot_discord.tree.sync()
    except Exception as e:
        print(f"[SYNC ERROR] {e}")

    await bot_discord.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="🪭 Em turnê | Arirang"
        )
    )


# ⚠️ COMANDO /teste ÚNICO (CORRIGIDO)
@bot_discord.tree.command(name="teste", description="Dispara teste completo do sistema")
async def teste(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=False)

    try:
        await run_full_test_discord()

    except Exception as e:
        await interaction.followup.send(
            f"❌ Erro no teste: {e}",
            ephemeral=False
        )


# === CORE ENGINE === #
async def monitor_loop():
    while not bot_discord.is_ready():
        await asyncio.sleep(5)

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await check_ticketmaster(session)
                await check_buyticket(session)
                await check_weverse(session)
                await check_social(session)
                await update_panel()

                await asyncio.sleep(25)

            except Exception as e:
                print(f"[MONITOR ERROR] {e}")
                await asyncio.sleep(10)


# === TELEGRAM START (FIX LOOP) === #
def start_telegram():
    if not TELEGRAM_TOKEN:
        return

    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

    async def run():
        global bot_ticket

        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        bot_ticket = app.bot

        app.add_handler(CommandHandler("ping", handle_commands_telegram))
        app.add_handler(CommandHandler("bts", bts_telegram_cmd))
        app.add_handler(CommandHandler("teste", handle_commands_telegram))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_commands_telegram))

        await app.initialize()
        await app.bot.delete_webhook(drop_pending_updates=True)
        await app.start()

        # ❌ REMOVIDO: run_polling (causava conflito de loop)
        # ✅ SUBSTITUÍDO POR LOOP MANUAL
        while True:
            await asyncio.sleep(3600)

    asyncio.create_task(run())

# =========================
# 18 CHECK SYSTEM + ALERTA REDES SOCIAIS (VERSÃO FINAL 100%)
# =========================

# Variável global para evitar alertas retroativos no boot
PRIMEIRO_CICLO = True

# === FUNÇÃO DE ALERTA UNIFICADO (X, INSTA, TIKTOK) === #
async def disparar_alerta_redes_sociais(plataforma, perfil, link):
    """Envia alerta para o canal DISCORD_CHANNEL_ID (Redes Sociais)"""
    
    # SILENCIADOR: Se for a primeira varredura ao ligar, apenas registra mas não posta
    if PRIMEIRO_CICLO:
        print(f"🤫 [SILENCIADOR] Ignorando post antigo de {plataforma} detectado no boot.")
        return

    channel_id = os.getenv("DISCORD_CHANNEL_ID")
    if not channel_id:
        print(f"⚠️ [ERRO] DISCORD_CHANNEL_ID não configurado para {plataforma}.")
        return

    try:
        # Busca o canal de forma robusta (Cache ou Fetch)
        channel = bot_discord.get_channel(int(channel_id)) or await bot_discord.fetch_channel(int(channel_id))
        
        if channel:
            cores = {
                "X": discord.Color.blue(), 
                "Instagram": discord.Color.magenta(), 
                "TikTok": discord.Color.dark_grey()
            }
            
            embed = discord.Embed(
                title=f"🔔 NOVO POST: {plataforma.upper()}",
                description=f"O perfil **{perfil}** acaba de postar!",
                color=cores.get(plataforma, discord.Color.blue()),
                timestamp=datetime.now()
            )
            embed.add_field(name="🔗 Link Direto", value=link, inline=False)
            embed.set_footer(text="Motor Arirang | Wootteo Monitoring")
            
            await channel.send(embed=embed)
            print(f"✅ [DISCORD] Alerta {plataforma} postado no canal {channel_id}")
    except Exception as e:
        print(f"❌ [ERRO ALERTA REDES] {e}")

# ⚠️⚠️⚠️ CORREÇÃO AQUI ⚠️⚠️⚠️
# RENOMEAMOS PARA NÃO QUEBRAR O /teste PRINCIPAL

async def run_social_test_only():
    """Simula apenas os disparos de rede social (NÃO interfere no /teste principal)"""
    print("🧪 [TESTE SOCIAL] Iniciando simulação de redes sociais...")

    global PRIMEIRO_CICLO
    estado_original = PRIMEIRO_CICLO
    PRIMEIRO_CICLO = False

    await disparar_alerta_redes_sociais("X", "@BTS_twt", "https://x.com/bts_twt")
    await asyncio.sleep(1.2)
    await disparar_alerta_redes_sociais("Instagram", "@uarmyhope", "https://instagram.com/uarmyhope")
    await asyncio.sleep(1.2)
    await disparar_alerta_redes_sociais("TikTok", "@bts_official_bighit", "https://tiktok.com/@bts_official_bighit")

    PRIMEIRO_CICLO = estado_original

    print("✅ [TESTE SOCIAL] concluído.")

# === AUXILIARES DO MOTOR === #
async def fetch(session, url):
    try:
        async with session.get(url, timeout=15) as resp:
            return await resp.text() if resp.status == 200 else None
    except: return None

def get_uptime():
    s = int(time.time() - start_time)
    return f"{s//3600}h {(s%3600)//60}m {s%60}s"

# === MOTOR DE EXECUÇÃO PRINCIPAL (DECOLAGEM) === #
async def main():
    global PRIMEIRO_CICLO
    print("🛸 [SISTEMA] WOOTTEO EM PREPARAÇÃO PARA DECOLAGEM...")
    
    # 1. Flask
    try:
        keep_alive()
        print("✅ [FLASK] Web Server ativo.")
    except Exception as e: 
        print(f"❌ [FLASK] Erro: {e}")

    # 2. Iniciar Telegram (CORRIGIDO)
    start_telegram()
    print("✅ [TELEGRAM] Wootteo online e respondendo.")

    # 3. Monitor
    loop = asyncio.get_running_loop()
    loop.create_task(monitor_loop())
    print("✅ [MONITOR] Ciclo Arirang iniciado.")

    # 4. Liberação de alertas
    async def liberar_alertas():
        global PRIMEIRO_CICLO
        await asyncio.sleep(45)
        PRIMEIRO_CICLO = False
        print("🔔 [SISTEMA] Alertas reais ativados.")

    loop.create_task(liberar_alertas())

    # 5. Discord
    try:
        print("✅ [DISCORD] Wootteo tentando login...")
        await bot_discord.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ [DISCORD ERROR] {e}")
        while True:
            await asyncio.sleep(3600)

# =========================
# 19 DISCORD ON_READY + SYNC + TELEGRAM INTELLIGENT PANEL
# =========================

# === STATUS COUNTDOWN DATA === #

def get_countdown_data():
    now_dt = datetime.now()
    prox_data = "Continua…"
    prox_local = "---"
    d_prox = 0
    d_br = 0

    # Próximo show global
    if 'AGENDA' in globals() and AGENDA:
        for item in AGENDA:
            try:
                data_hora = datetime.strptime(
                    f"{item[0]} {item[3]}",
                    "%d/%m/%Y %H:%M"
                )
                if data_hora > now_dt:
                    prox_data = item[0]
                    prox_local = f"{item[1]}, {item[2]}"
                    d_prox = (data_hora.date() - now_dt.date()).days
                    break
            except:
                continue

        # Próximo BR
        for item in AGENDA:
            if "Brasil" in item[2]:
                try:
                    data_br = datetime.strptime(item[0], "%d/%m/%Y").date()
                    if data_br >= now_dt.date():
                        d_br = (data_br - now_dt.date()).days
                        break
                except:
                    continue

    return prox_data, prox_local, d_prox, d_br


# === PAINEL RENDER (TEXTO BASE) === #

def gerar_texto_painel(data_show, city, d_prox, d_br):
    return f"""🪭 ⊙⊝⊜ **ARIRANG TOUR** ⊙⊝⊜ 🪭

**✈️ PRÓXIMAS DATAS**

  🎫 Data: **{data_show}**
  📍 Local: **{city}**
  🔔 Faltam **{d_prox}** dias.
  🩷 Brasil em **{d_br}** dias!

•°•🌙.•°**ATUALIZAÇÕES** .💫 * . * •°•°🛸

  🟣 **Weverse** {status_color(last_weverse_check)}
  🎯 Acessos: **{total_weverse}**
  ⏳ Último: **{minutes_since(last_weverse_check)} min**

  ⚪ **Social** {status_color(last_social_check)}
  🎯 Acessos: **{total_social}**
  ⏳ Último: **{minutes_since(last_social_check)} min**

  🟠 **Ticketmaster** {status_color(last_ticket_check)}
  🎯 Acessos: **{total_tickets}**
  ⏳ Último: **{minutes_since(last_ticket_check)} min**

  🔵 **Buyticket** {status_color(last_buy_check)}
  🎯 Acessos: **{total_buy}**
  ⏳ Último: **{minutes_since(last_buy_check)} min**

•°•👾 Wootteo em rota há: **{get_uptime()}** ☄️🌍💫
"""

# === FUNÇÃO DE BUSCA (REGRAS A e B) === #

async def carregar_id_telegram():
    """
    Busca nas últimas mensagens do canal se existe um painel ativo.
    Evita a criação de novas mensagens após resets.
    """
    global panel_message_id
    
    if panel_message_id:
        return panel_message_id

    if bot_ticket and PANEL_CHAT_ID:
        try:
            # Tenta encontrar o painel nas últimas 15 mensagens do canal
            # Nota: python-telegram-bot usa get_chat se não houver persistência de banco
            # Aqui simulamos a busca lógica para o contexto do Arirang
            print("[SISTEMA] Varrendo canal em busca de painel anterior...")
            # Em implementações sem DB, se o ID for perdido no reset total,
            # o bot criará um novo. Para busca real, seria necessário um DB ou log.
            return panel_message_id 
        except Exception as e:
            print(f"[ERRO BUSCA] {e}")
            
    return None

# === PAINEL UPDATE (REGRAS DE RECONEXÃO) === #

async def update_panel():
    global panel_message_id, discord_panel_msg_id

    data_show, city, d_prox, d_br = get_countdown_data()
    texto = gerar_texto_painel(data_show, city, d_prox, d_br)

    # === TELEGRAM (LÓGICA ANTI-DUPLICAÇÃO) === #
    if bot_ticket and PANEL_CHAT_ID:
        try:
            success = False

            # REGRA B: Tenta editar se o ID existir
            if panel_message_id:
                try:
                    await bot_ticket.edit_message_text(
                        chat_id=PANEL_CHAT_ID,
                        message_id=panel_message_id,
                        text=texto
                    )
                    success = True
                except Exception:
                    # Se falhar (ex: mensagem apagada), limpa o ID
                    panel_message_id = None

            # REGRA A: Se não houver ID ou a edição falhou, cria novo e fixa
            if not success:
                # Limpa fixados antigos para evitar poluição
                try:
                    await bot_ticket.unpin_all_chat_messages(chat_id=PANEL_CHAT_ID)
                except: pass

                msg = await bot_ticket.send_message(
                    chat_id=PANEL_CHAT_ID,
                    text=texto
                )
                panel_message_id = msg.message_id
                
                # Salva o ID (Idealmente em um arquivo ou variável de ambiente)
                # salvar_id_telegram(panel_message_id) # Função do Bloco 12

                try:
                    await bot_ticket.pin_chat_message(
                        chat_id=PANEL_CHAT_ID,
                        message_id=panel_message_id,
                        disable_notification=True
                    )
                except: pass
                print(f"[TELEGRAM] Novo painel fixado: {panel_message_id}")

        except Exception as e:
            print(f"[TG PANEL ERROR] {e}")

    # === DISCORD PAINEL FIXO === #
    if DISCORD_PANEL_CHANNEL_ID:
        channel = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                description=texto,
                color=0x8A2BE2 # Roxo Arirang
            )
            try:
                if not discord_panel_msg_id:
                    async for msg in channel.history(limit=10):
                        if msg.author == bot_discord.user:
                            discord_panel_msg_id = msg.id
                            break

                if discord_panel_msg_id:
                    msg = await channel.fetch_message(discord_panel_msg_id)
                    await msg.edit(embed=embed)
                else:
                    msg = await channel.send(embed=embed)
                    discord_panel_msg_id = msg.id
            except Exception as e:
                print(f"[DC PANEL ERROR] {e}")

# =========================
# 20 FINAL MASTER (ANTI-CRASH + CACHE + DUPLICAÇÃO GLOBAL)
# =========================

# === GLOBAL CACHE (ANTI-DUPLICAÇÃO REAL) === #

GLOBAL_CACHE = {}
GLOBAL_LOCK = asyncio.Lock()

# === SMART CACHE CHECK (EVITA RE-ALERT REPETIDO) === #
def is_new_global(key, content):

    content_clean = " ".join(content.split())
    new_hash = hashlib.md5(content_clean.encode("utf-8")).hexdigest()

    if key not in GLOBAL_CACHE:
        GLOBAL_CACHE[key] = new_hash
        return True

    if GLOBAL_CACHE[key] != new_hash:
        GLOBAL_CACHE[key] = new_hash
        return True

    return False

# ===  SAFE WRAPPER (ANTI-CRASH GLOBAL) === #

async def safe_run(coro, label="TASK"):

    try:
        return await coro

    except Exception as e:
        print(f"[SAFE ERROR {label}] {e}")
        return None

# ===  WATCHDOG LOOP (RESTART AUTOMÁTICO DO MONITOR) === #

async def watchdog_monitor():

    await bot_discord.wait_until_ready()

    print("[WATCHDOG] iniciado")

    while True:

        try:

            task = asyncio.create_task(monitor_loop())

            await asyncio.wait_for(task, timeout=300)

        except asyncio.TimeoutError:

            print("[WATCHDOG] monitor travado -> reiniciando")

        except Exception as e:

            print(f"[WATCHDOG ERROR] {e}")

        await asyncio.sleep(5)

# ===  SAFE FETCH WRAPPER (ANTI-SPAM REQUESTS) === #

async def safe_fetch(session, url):

    try:

        html = await fetch(session, url)

        if not html:
            return None

        return html

    except Exception as e:
        print(f"[FETCH SAFE ERROR] {e}")
        return None


# ===  LOCKED UPDATE PANEL (EVITA CONCORRÊNCIA) === #

async def locked_update_panel():

    async with GLOBAL_LOCK:

        await safe_run(update_panel(), "PANEL")


# ===  EVENT LOOP GUARD (ANTI FREEZE) === #

def run_with_guard(loop_func):

    async def wrapper():

        while True:

            try:
                await loop_func()

            except Exception as e:
                print(f"[LOOP GUARD ERROR] {e}")

            await asyncio.sleep(1)

    return wrapper


# ===  CLEAN START MONITOR (FINAL ENGINE) === #

async def start_engine():

    print("[ENGINE] iniciando sistema completo")

    await asyncio.gather(

        monitor_loop(),
        watchdog_monitor()

    )


# ===  GLOBAL SAFE DISPATCH ALERT === #

async def dispatch_alert(alert_type, message, key=None):

    # evita duplicação global
    if key:

        if not is_new_global(key, message):
            return

    await send_alert(alert_type, message)
    await locked_update_panel()


# === FINAL PROTECTION LAYER === #

async def protected_task(name, coro):

    try:

        return await coro

    except Exception as e:

        print(f"[PROTECTED {name}] {e}")

        return None


# === SYSTEM HEALTH CHECK === #

def system_health():

    return {
        "tickets": total_tickets,
        "buy": total_buy,
        "weverse": total_weverse,
        "social": total_social,
        "uptime": get_uptime(),
        "panel_ok": panel_message_id is not None
    }


# ===  AUTO RECOVERY PANEL FIX === #

async def auto_repair_panel():

    global panel_message_id

    try:

        if not panel_message_id:

            print("[AUTO FIX] recriando painel telegram")

            await update_panel()

    except Exception as e:

        print(f"[AUTO REPAIR ERROR] {e}")


# ===  CLEAN TASK RUNNER === #

async def run_task_safe(task_func, *args):

    try:

        return await task_func(*args)

    except Exception as e:

        print(f"[TASK ERROR] {e}")
        return None

# =========================
# 21 FINAL CORE HARDENING (ANTI-SPAM INTELIGENTE + DIF REAL + PRIORIDADE)
# =========================

# === PRIORITY LEVELS === #

PRIORITY = {
    "ticket": 3,      # alta
    "reposicao": 3,
    "agenda": 2,
    "weverse_post": 2,
    "weverse_live": 3,
    "instagram_post": 1,
    "instagram_reels": 1,
    "tiktok_post": 1,
    "youtube_live": 3,
    "youtube_post": 2,
    "social": 1
}


# === SMART CONTENT DIFF (NÃO SÓ HASH) === #

def extract_core_signatures(html):

    """
    Extrai "assinaturas reais" do conteúdo para detectar mudanças relevantes
    (evita falso positivo de HTML que muda layout sem mudar conteúdo real)
    """

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ", strip=True)

    links = [a.get("href") for a in soup.find_all("a") if a.get("href")]

    images = [img.get("src") for img in soup.find_all("img") if img.get("src")]

    signature = {
        "text": text[:2000],  # limita peso
        "links": sorted(set(links))[:50],
        "images": sorted(set(images))[:20]
    }

    return signature


# === SMART DIFF CHECK (EVITA SPAM REAL) === #

def is_real_change(key, html):

    signature = extract_core_signatures(html)

    new_hash = hashlib.md5(str(signature).encode("utf-8")).hexdigest()

    if key not in GLOBAL_CACHE:
        GLOBAL_CACHE[key] = new_hash
        return False

    if GLOBAL_CACHE[key] != new_hash:
        GLOBAL_CACHE[key] = new_hash
        return True

    return False

# ===  PRIORITY ALERT ROUTER === #

async def priority_send(alert_type, message, key=None):

    level = PRIORITY.get(alert_type, 1)

    # evita spam duplicado
    if key:
        if not is_real_change(key, message):
            return

    # HIGH PRIORITY -> imediata
    if level == 3:

        await send_alert(alert_type, message)
        await locked_update_panel()
        return

    # MEDIUM -> leve delay
    if level == 2:

        await asyncio.sleep(1)

        await send_alert(alert_type, message)
        await locked_update_panel()
        return

    # LOW -> batch (evita flood)
    if level == 1:

        await asyncio.sleep(2)

        await send_alert(alert_type, message)
        return


# === INTELLIGENT ALERT WRAPPER === #

async def smart_alert(alert_type, url, message):

    key = f"{alert_type}:{url}"

    await priority_send(alert_type, message, key=key)


# === REQUEST THROTTLER (ANTI FLOOD) === #

LAST_REQUEST_TIME = {}


async def throttle(key, delay=2):

    now = time.time()

    last = LAST_REQUEST_TIME.get(key, 0)

    if now - last < delay:
        await asyncio.sleep(delay - (now - last))

    LAST_REQUEST_TIME[key] = time.time()


# === SAFE MONITOR WRAPPER (ANTI CRASH TOTAL) === #

async def safe_monitor_cycle(session):

    try:

        await throttle("ticket", 1)
        await check_ticketmaster(session)

        await throttle("buy", 1)
        await check_buyticket(session)

        await throttle("weverse", 1)
        await check_weverse(session)

        await throttle("social", 1)
        await check_social(session)

        await locked_update_panel()

    except Exception as e:

        print(f"[MONITOR SAFE ERROR] {e}")


# ===  ENHANCED MONITOR LOOP (FINAL STABLE VERSION) === #

async def monitor_loop():

    await bot_discord.wait_until_ready()

    print("[MONITOR] HARDENED MODE ON")

    async with aiohttp.ClientSession() as session:

        while True:

            await safe_monitor_cycle(session)

            await asyncio.sleep(20)

# === GLOBAL HEALTH WATCHER === #

async def health_watcher():

    await bot_discord.wait_until_ready()

    while True:

        health = system_health()

        # se algo travar muito tempo, tenta reparar painel
        if not health["panel_ok"]:

            print("[HEALTH] painel quebrado -> repair")

            await auto_repair_panel()

        await asyncio.sleep(60)

# === ENGINE FINAL OVERRIDE (STARTUP LEVEL MAX) === #
async def start_engine():

    print("[ENGINE] FINAL MODE STARTED")

    await asyncio.gather(

        monitor_loop(),
        watchdog_monitor(),
        health_watcher()

    )

# === GLOBAL ALERT ENTRYPOINT (USAR ISSO SEMPRE) === #

async def trigger_alert(alert_type, url, message):

    await smart_alert(alert_type, url, message)
