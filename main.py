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

# Ajuste nos imports do Telegram para evitar NameError
from telegram import Bot, Update
from telegram.ext import ContextTypes

# ==========================================
# 2 CONFIGURAÇÃO DE CREDENCIAIS & TELEGRAM
# ==========================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

PANEL_CHAT_ID = -1003920883053

# Variáveis de Controle de Persistência
panel_message_id = None
discord_panel_msg_id = None
panel_initialized = False

# IDs dos Canais do Discord (DEFINIDOS AQUI)
DISCORD_PANEL_CHANNEL_ID = 1494667029150695625
DISCORD_TICKETS_CHANNEL_ID = 1494670074374651985
DISCORD_WEVERSE_CHANNEL_ID = 1494680233025208461
DISCORD_SOCIAL_CHANNEL_ID = 1494682078950981864

# Inicialização do Bot Telegram
bot_ticket = None

if TELEGRAM_TOKEN:
    try:
        bot_ticket = Bot(token=TELEGRAM_TOKEN)
        print("[SISTEMA] Telegram configurado com sucesso.")
    except Exception as e:
        print(f"[ERRO CONFIG TELEGRAM] {e}")

# ==========================================
# 3 CONTADORES GLOBAIS E PERSISTÊNCIA
# ==========================================

# Contadores de acesso (🎯 Acessos realizados)
total_tickets = 0
total_buy = 0
total_weverse = 0
total_social = 0

# Timestamps dos últimos rastreios (⏳ Último rastreio há...)
last_ticket_check = time.time()
last_buy_check = time.time()
last_weverse_check = time.time()
last_social_check = time.time()

# IDs das mensagens dos painéis (ESSENCIAL para evitar novos posts e permitir a edição)
panel_message_id = None
# Armazena o ID da mensagem no Telegram

discord_panel_msg_id = None
# Armazena o ID da mensagem no Discord

# Tempo de início para o cálculo de Uptime
start_time = time.time()

# Rastreamento de mudanças e duplicatas
CONTENT_HASH = {}
SEEN_TICKET = set()
SEEN_BUY = set()
SEEN_WEVERSE = set()
SEEN_SOCIAL = set()

# =========================
# 4 WEB SERVER (KEEP ALIVE)
# =========================
app_web = Flask(__name__)

@app_web.route('/')
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
# 5 LÓGICA DE COMPARAÇÃO (ANTI-SPAM)
# =========================
def is_new(url, html):
    """
    Verifica se o conteúdo mudou e evita o spam de inicialização.
    """
    global CONTENT_HASH

    content_clean = " ".join(html.split())
    new_hash = hashlib.md5(content_clean.encode('utf-8')).hexdigest()

    if url not in CONTENT_HASH:
        CONTENT_HASH[url] = new_hash
        print(f"[MEMÓRIA] URL aprendida: {url}")
        return False

    if CONTENT_HASH[url] != new_hash:
        CONTENT_HASH[url] = new_hash
        print(f"[ALERTA] Mudança real detectada em: {url}")
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

# =============================================================
# 8 CONTROLE (CÁLCULO PRECISO E STATUS PULSANTE)
# =============================================================
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
    """
    Retorna Status Pulsante:
    Alterna entre Verde e Amarelo a cada segundo.
    Retorna Vermelho apenas se o rastreio parar por mais de 30 minutos.
    """
    agora = time.time()

    if (agora - last_check) > 1800:
        return "🔴"

    return "🟢" if int(agora) % 2 == 0 else "🟡"

def get_countdown_data():
    """
    Varre a AGENDA e retorna o próximo show baseado na data e hora local.
    O painel pula para a próxima data assim que o horário do show passa.
    """
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
# 9 SESSION (FIX: CLIENT SESSION ÚNICA)
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
# 11 ROTEAMENTO E LINKS (CORRIGIDO)
# =========================
async def send_alert(alert_type, message):
    if bot_ticket is not None:
        try:
            await bot_ticket.send_message(
                chat_id=PANEL_CHAT_ID,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"[TELEGRAM ERROR] {e}")

    try:
        loop = asyncio.get_running_loop()

        if alert_type in ["ticket", "reposicao", "nova_data", "revenda", "agenda"]:
            loop.create_task(send_discord(DISCORD_TICKETS_CHANNEL_ID, message))

        elif alert_type in ["weverse_post", "weverse_live", "weverse_news", "weverse_media"]:
            loop.create_task(send_discord(DISCORD_WEVERSE_CHANNEL_ID, message))

        elif alert_type in [
            "instagram_post",
            "instagram_reels",
            "instagram_stories",
            "instagram_live",
            "tiktok_post",
            "tiktok_live"
        ]:
            loop.create_task(send_discord(DISCORD_SOCIAL_CHANNEL_ID, message))

    except Exception as e:
        print(f"[DISCORD ROUTING ERROR] {e}")


# --- LINKS DE MONITORAMENTO ---
TICKET_LINKS = [
    "https://www.ticketmaster.com.br/event/bts-sp"
]

BUY_LINKS = [
    "https://www.buyticket.com.br/bts"
]

WEVERSE_LINKS = [
    "https://weverse.io/bts/feed"
]

INSTAGRAM_LINKS = {
    "bts": "https://www.instagram.com/bts.bighitofficial/"
}

TIKTOK_LINKS = {
    "bts": "https://www.tiktok.com/@bts_official_bighit"
}


# === PERSISTÊNCIA TELEGRAM === #

def carregar_id_telegram():
    try:
        with open("panel_id.txt", "r") as f:
            return int(f.read().strip())
    except:
        return None

def salvar_id_telegram(message_id):
    try:
        with open("panel_id.txt", "w") as f:
            f.write(str(message_id))
    except:
        pass

# =============================================================
# 12 GESTÃO DO PAINEL (FIXO E ÚNICO)
# =============================================================

async def update_panel():
    global panel_message_id, discord_panel_msg_id

    # Obtém os dados variáveis (datas e cidades)
    data_show, city, d_prox, d_br = get_countdown_data()

    # Gera o texto formatado com o contador de uptime incluso
    texto = gerar_texto_painel(data_show, city, d_prox, d_br)

    # =========================
    # TELEGRAM (PAINEL FIXO)
    # =========================
    if bot_ticket and PANEL_CHAT_ID:
        try:
            # restaura ID salvo
            if not panel_message_id:
                panel_message_id = carregar_id_telegram()

            edited = False

            # 1 - tenta editar mensagem existente
            if panel_message_id:
                try:
                    await bot_ticket.edit_message_text(
                        chat_id=PANEL_CHAT_ID,
                        message_id=panel_message_id,
                        text=texto,
                        parse_mode="Markdown"
                    )
                    edited = True
                except Exception as e:
                    panel_message_id = None

            # 2 - recria caso não exista
            if not edited:
                try:
                    await bot_ticket.unpin_all_chat_messages(chat_id=PANEL_CHAT_ID)
                except:
                    pass

                msg = await bot_ticket.send_message(
                    chat_id=PANEL_CHAT_ID,
                    text=texto,
                    parse_mode="Markdown"
                )

                panel_message_id = msg.message_id
                salvar_id_telegram(panel_message_id)

                # 3 - PIN FORÇADO COM PROTEÇÃO
                try:
                    await bot_ticket.pin_chat_message(
                        chat_id=PANEL_CHAT_ID,
                        message_id=panel_message_id,
                        disable_notification=True
                    )
                except Exception:
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
            print(f"[DEBUG] Falha update TG: {e}")

    # =========================
    # DISCORD PAINEL
    # =========================
    if DISCORD_PANEL_CHANNEL_ID:
        channel = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)

        if channel:
            embed = discord.Embed(description=texto, color=0x8A2BE2)

            try:
                if not discord_panel_msg_id:
                    async for message in channel.history(limit=10):
                        if message.author == bot_discord.user:
                            discord_panel_msg_id = message.id
                            break

                if discord_panel_msg_id:
                    msg = await channel.fetch_message(discord_panel_msg_id)
                    await msg.edit(content=None, embed=embed)
                else:
                    msg = await channel.send(embed=embed)
                    discord_panel_msg_id = msg.id

            except Exception as e:
                print(f"[DEBUG] Falha update Discord: {e}")


def gerar_texto_painel(data_show, city, d_prox, d_br):
    global total_weverse, total_social, total_tickets, total_buy
    global last_weverse_check, last_social_check, last_ticket_check, last_buy_check

    return f"""🪭 ⊙⊝⊜ **ARIRANG TOUR** ⊙⊝⊜ 🪭


**✈️ PRÓXIMAS DATAS**

  🎫 Data: **{data_show}**
  📍 Local: **{city}**
  🔔 Faltam **{d_prox}** dias.
  🩷 Faltam **{d_br}** dias para o BTS no Brasil!

•°•👾.  * .🌙  **ATUALIZAÇÕES**  .💫 *  . *  •°•°🛸

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
"""

texto = f"""
•°•👾 Wootteo em rota há: **{get_uptime()}** ☄️🌍💫
•°•°🛸
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
🩷*WEVERSE POST*🩷
{emoji} {member_name.upper()} publicou uma mensagem:

📌 {title}
{message_translated}

🔗 {url}
"""

    await send_alert("weverse_post", msg)
    await update_panel()


async def test_weverse_live(url, member_name, found):
    global LAST_WEVERSE_LIVE_URL, total_weverse, last_weverse_check

    if url == LAST_WEVERSE_LIVE_URL:
        return

    LAST_WEVERSE_LIVE_URL = url

    total_weverse += 1
    last_weverse_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
📹*WEVERSE LIVE*📹
{emoji} {member_name.upper()} está ao vivo!

🔗 {url}
"""

    await send_alert("weverse_live", msg)
    await update_panel()


async def test_weverse_news(url, member_name, message_translated, found):
    global LAST_WEVERSE_POST_URL, total_weverse, last_weverse_check

    if url == LAST_WEVERSE_POST_URL:
        return

    LAST_WEVERSE_POST_URL = url

    total_weverse += 1
    last_weverse_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
🚨*WEVERSE NEWS*🚨
{emoji} {member_name.upper()} publicou uma notícia:

📌 {message_translated}

🔗 {url}
"""

    await send_alert("weverse_news", msg)
    await update_panel()


async def test_weverse_media(url, member_name, title, message_translated, found):
    global LAST_WEVERSE_POST_URL, total_weverse, last_weverse_check

    if url == LAST_WEVERSE_POST_URL:
        return

    LAST_WEVERSE_POST_URL = url

    total_weverse += 1
    last_weverse_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
📀 WEVERSE MÍDIA📀
{emoji} {member_name.upper()} publicou uma nova mídia!

⭐️ {title}
{message_translated}

🔗 {url}
"""

    await send_alert("weverse_media", msg)
    await update_panel()

# =========================
# 14 ALERTAS INSTAGRAM 
# =========================

LAST_INSTA_POST_LINK = None

LAST_INSTA_STORY_LINK = None

async def instagram_post(url, member_name, title, found):
    global LAST_INSTA_POST_LINK, total_social, last_social_check

    if url == LAST_INSTA_POST_LINK:
        return

    LAST_INSTA_POST_LINK = url

    total_social += 1
    last_social_check = time.time()

    emoji, name = format_member(member_name)

    msg = f"""
🌟*INSTAGRAM POST*🌟
{emoji} {name} postou uma foto!

🔗 {url}
"""

    await send_alert("instagram_post", msg)
    await update_panel()


async def instagram_reel(url, member_name, title, found):
    global LAST_INSTA_POST_LINK, total_social, last_social_check

    if url == LAST_INSTA_POST_LINK:
        return

    LAST_INSTA_POST_LINK = url

    total_social += 1
    last_social_check = time.time()

    emoji, name = format_member(member_name)

    msg = f"""
🎬*INSTAGRAM REELS*🎬
{emoji} {name} postou um reels!

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
🫧*INSTAGRAM STORIES*🫧
{emoji} {name} atualizou os stories!

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
🎥*INSTAGRAM LIVE*🎥
{emoji} {name} está ao vivo!

🔗 {url}
"""

    await send_alert("instagram_live", msg)
    await update_panel()

# =========================
# 15 ALERTAS TIKTOK E YOUTUBE
# =========================

LAST_TIKTOK_LINK = None

async def tiktok_post(url, member_name, title, found):
    global LAST_TIKTOK_LINK, total_social, last_social_check

    link_correto = "https://www.tiktok.com/@bts_official_bighit"

    if "video/" in url:
        video_id = url.split("video/")[1].split("?")[0]
        final_url = f"{link_correto}/video/{video_id}"
    else:
        final_url = link_correto

    if final_url == LAST_TIKTOK_LINK:
        return

    LAST_TIKTOK_LINK = final_url

    total_social += 1
    last_social_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
🎵*TIKTOK POST*🎵
{emoji} {member_name.upper()} postou um vídeo!

🔗 *Link:* {final_url}
"""

    await send_alert("tiktok_post", msg)
    await update_panel()


async def tiktok_live(url, member_name, title, found):
    global total_social, last_social_check

    total_social += 1
    last_social_check = time.time()

    emoji = get_member_emoji(member_name)

    msg = f"""
🎥*TIKTOK LIVE*🎥
{emoji} {member_name.upper()} está ao vivo no TikTok!

🔗 *Link:* https://www.tiktok.com/@bts_official_bighit/live
"""

    await send_alert("tiktok_live", msg)
    await update_panel()


async def youtube_post(url, final_url):
    global total_youtube, last_youtube_check

    total_youtube += 1
    last_youtube_check = time.time()

    msg = f"""
🎞️*YOUTUBE POST*🎞️
💜 **BTS** postou um vídeo novo!

🔗 *Link:* {final_url}
"""

    await send_alert("youtube_post", msg)
    await update_panel()


async def youtube_live(url):
    global total_youtube, last_youtube_check

    total_youtube += 1
    last_youtube_check = time.time()

    live_url = "https://www.youtube.com/@BTS/live"

    msg = f"""
📹*YOUTUBE LIVE*📹
🚨 **BTS** está ao vivo agora no YouTube!

🔗 *Link:* {live_url}
"""

    await send_alert("youtube_live", msg)
    await update_panel()

# =============================================================
# 16 SISTEMA DE TESTE (ROTEADO PARA AS SALAS CERTAS)
# =============================================================
TEST_HEADER = "⚠️ TESTE ⚠️"

async def run_full_test(platform="both"):
    """
    Executa a sequência de testes enviando para os canais específicos.
    """

    await test_ticket_reposicao(TICKET_LINKS[0], "28/10/2026", True, platform)

    await asyncio.sleep(1)

    await test_agenda(
        {
            "date": "28/10/2026",
            "city": "São Paulo",
            "country": "Brasil"
        },
        platform
    )

    await asyncio.sleep(1)

    await test_weverse_post(
        WEVERSE_LINKS[0],
        "bts",
        "Update",
        "Conteúdo Teste",
        True,
        platform
    )

    await asyncio.sleep(1)

    await test_instagram_post(
        INSTAGRAM_LINKS["bts"],
        "bts",
        "post",
        True,
        platform
    )

    await test_tiktok_post(
        TIKTOK_LINKS["bts"],
        "bts",
        "video",
        True,
        platform
    )

    try:
        await update_panel()
        await update_discord_panel()
    except:
        pass


async def test_ticket_reposicao(url, key, found, platform="both"):
    msg = f"""
{TEST_HEADER}

🔥*ALERTA DE REPOSIÇÃO*🔥

📅 *Data:* 28/10/2026
🔗 *Link:* https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-28-10
✅ *Status:* Liberado
"""

    await send_alert("reposicao", msg)


async def test_agenda(data, platform="both"):
    msg = f"""
{TEST_HEADER}

💜*AGENDA NOVAS DATAS*💜

📅 *Data:* 28/10/2026
🏙️ *Cidade:* São Paulo
🌎 *País:* Brasil
🔗 *Link:* https://ibighit.com/en/bts/tour/
"""

    await send_alert("agenda", msg)


async def test_weverse_post(url, member_name, title, message_translated, found, platform="both"):
    msg = f"""
{TEST_HEADER}

🩷*WEVERSE POST*🩷

👤 BTS publicou uma mensagem!
🔗 *Link:* https://weverse.io/bts/artist
"""

    await send_alert("weverse_post", msg)


async def test_instagram_post(url, member_name, title, found, platform="both"):
    msg = f"""
{TEST_HEADER}
🌟*INSTAGRAM POST*🌟
👤 BTS postou uma foto!
🔗 *Link:* https://www.instagram.com/bts.bighitofficial/
"""

    await send_alert("instagram_post", msg)


async def test_tiktok_post(url, member_name, title, found, platform="both"):
    msg = f"""
{TEST_HEADER}

🎵*TIKTOK POST*🎵

👤 {member_name.upper()} postou um vídeo!
🔗 *Link:* https://www.tiktok.com/@bts_official_bighit
"""

    await send_alert("tiktok_post", msg)


async def test_youtube_post(url="https://www.youtube.com/@BTS", platform="both"):
    msg = f"""
{TEST_HEADER}

🎞️*YOUTUBE POST*🎞️

💜 **BTS** postou um vídeo novo!
🔗 *Link:* https://www.youtube.com/@BTS
"""

    await send_alert("youtube_post", msg)


async def test_youtube_live(url="https://www.youtube.com/@BTS/live", platform="both"):
    msg = f"""
{TEST_HEADER}

📹*YOUTUBE LIVE*📹

🚨 **BTS** está ao vivo agora no YouTube!
🔗 *Link:* https://www.youtube.com/@BTS/streams
"""

    await send_alert("youtube_live", msg)

# =============================================================
# 17 MOTOR DE MONITORAMENTO + COMANDOS + TESTE (UNIFICADO)
# =============================================================

# =========================
# MONITOR PRINCIPAL
# =========================
async def monitor_loop():
    """
    Motor principal:
    Controla scraping + painel + ciclos
    """
    await bot_discord.wait_until_ready()

    print("[SISTEMA] Motor Arirang operando. Aguardando ciclos...")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await check_ticketmaster(session)
                await check_buyticket(session)
                await check_weverse(session)
                await check_social(session)

                # painel atualizado UMA vez por ciclo
                await update_panel()

                await asyncio.sleep(25)

            except Exception as e:
                print(f"[MONITOR ERROR] {e}")
                await asyncio.sleep(10)


# =========================
# COMANDOS TELEGRAM
# =========================
async def handle_commands_telegram(update, context):
    if not update.message or not update.message.text:
        return

    cmd = update.message.text.lower()

    if "/ping" in cmd:
        await update.message.reply_text(
            f"🏓 Pong! Wootteo operando há {get_uptime()}"
        )

    elif "/teste" in cmd:
        try:
            await run_full_test_telegram()
            await update_panel()
        except Exception as e:
            await update.message.reply_text(f"❌ Erro no teste: {e}")

    elif "/comandos" in cmd:
        await update.message.reply_text(
            "/ping\n/teste\n/comandos"
        )


# =========================
# COMANDO DISCORD (APENAS 1 CAMADA)
# =========================
@bot_discord.tree.command(
    name="teste",
    description="Dispara alertas reais do sistema"
)
async def teste_discord(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        await run_full_test_discord()
        await update_panel()

        await interaction.followup.send(
            "✅ Teste executado com sucesso.",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ Erro no teste: {e}",
            ephemeral=True
        )


# =========================
# TESTE TELEGRAM (REAL)
# =========================
async def run_full_test_telegram():
    try:
        print("[TESTE TG] Executando...")

        await test_ticket_reposicao(
            "TESTE",
            "https://www.ticketmaster.com.br/",
            True
        )

        await test_weverse_post(
            "https://weverse.io/bts/feed",
            "bts",
            "Update",
            "Teste real",
            True
        )

        await test_instagram_post(
            "https://instagram.com",
            "bts",
            "post",
            True
        )

        await test_tiktok_post(
            "https://tiktok.com",
            "bts",
            "video",
            True
        )

        print("[TESTE TG] Finalizado.")

    except Exception as e:
        print(f"[DEBUG TG] {e}")


# =========================
# TESTE DISCORD (REAL)
# =========================
async def run_full_test_discord():
    try:
        print("[TESTE DC] Executando...")

        await test_ticket_reposicao(
            "TESTE DISCORD",
            "https://www.ticketmaster.com.br/",
            True
        )

        await test_weverse_post(
            "https://weverse.io/bts/feed",
            "bts",
            "Update",
            "Teste Discord",
            True
        )

        print("[TESTE DC] Finalizado.")

    except Exception as e:
        print(f"[DEBUG DC] {e}")

# =========================
# 18 FETCH UNIVERSAL
# =========================
async def fetch(session, url):
    if session is None:
        return None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        async with session.get(url, headers=headers, timeout=20) as response:
            if response.status != 200:
                return None

            return await response.text()

    except:
        return None

# =========================
# 19 FUNÇÕES DE CHECK (RASTREIO E CONTADORES)
# =========================

async def check_ticketmaster(session):
    global last_ticket_check, total_tickets
    if 'TICKET_LINKS' not in globals() or not TICKET_LINKS:
        return
    last_ticket_check = time.time()
    total_tickets += 1
    for url in TICKET_LINKS:
        try:
            html = await fetch(session, url)
            if html and is_new(url, html):
                found = "esgotado" not in html.lower()
                await ticket_reposicao(url, url, found)
        except Exception as e:
            print(f"[ERR TICKET] {e}")

async def check_buyticket(session):
    global last_buy_check, total_buy
    if 'BUY_LINKS' not in globals() or not BUY_LINKS:
        return
    last_buy_check = time.time()
    total_buy += 1
    for url in BUY_LINKS:
        try:
            html = await fetch(session, url)
            if html and is_new(url, html):
                pass
        except Exception as e:
            print(f"[ERR BUY] {e}")

async def check_weverse(session):
    global last_weverse_check, total_weverse
    if 'WEVERSE_LINKS' not in globals() or not WEVERSE_LINKS:
        return
    last_weverse_check = time.time()
    total_weverse += 1
    for url in WEVERSE_LINKS:
        try:
            html = await fetch(session, url)
            if html and is_new(url, html):
                pass
        except Exception as e:
            print(f"[ERR WEVERSE] {e}")

async def check_social(session):
    global last_social_check, total_social
    last_social_check = time.time()
    total_social += 1
    if 'SOCIAL_LINKS' in globals() and SOCIAL_LINKS:
        for url in SOCIAL_LINKS:
            try:
                html = await fetch(session, url)
                if html and is_new(url, html):
                    pass
            except Exception as e:
                print(f"[ERR SOCIAL] {e}")
    await check_youtube(session)

async def check_youtube(session):
    global last_social_check, total_social
    youtube_url = "https://www.youtube.com/@BTS"
    try:
        html = await fetch(session, f"{youtube_url}/videos")
        if html:
            is_live = '{"text":"AO VIVO"}' in html or '"style":"LIVE"' in html or "watch?v=" in html and "live" in html.lower()
            if is_live:
                if is_new(youtube_url + "/live", "LIVE"):
                    await youtube_live(youtube_url)
            elif is_new(youtube_url, html):
                await youtube_post(youtube_url, youtube_url)
    except Exception as e:
        print(f"[ERR YOUTUBE] {e}")

# =======================
# 19.1 AUXILIAR DE ALERTA SOCIAL
# =======================

async def enviar_alerta_social(mensagem):
    if bot_ticket and PANEL_CHAT_ID:
        try:
            await bot_ticket.send_message(chat_id=PANEL_CHAT_ID, text=mensagem, parse_mode="Markdown")
        except:
            pass
    channel = bot_discord.get_channel(DISCORD_SOCIAL_CHANNEL_ID)
    if channel:
        try:
            await channel.send(content=mensagem)
        except:
            pass

# =========================
# 20 DISCORD ON_READY + SYNC (CLEAN FIX)
# =========================

@bot_discord.event
async def on_ready():

    print(f"✅ Logado no Discord como {bot_discord.user}")

    await bot_discord.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="Em tournê - Arirang 🪭"
        ),
        status=discord.Status.online
    )

    try:
        # garante registro único antes do sync
        if hasattr(bot_discord, "COMMANDS_LOADED") and not bot_discord.COMMANDS_LOADED:
            await register_discord_commands()

        synced = await bot_discord.tree.sync()
        print(f"[DISCORD] Slash commands sincronizados: {len(synced)}")

    except Exception as e:
        print(f"[DISCORD ERROR SYNC] {e}")

# =========================
# 21 INICIALIZAÇÃO FINAL (MAIN) - TELEGRAM + DISCORD FIX
# =========================

async def main():

    keep_alive()

    # =========================
    # TELEGRAM START
    # =========================
    if TELEGRAM_TOKEN:

        from telegram.ext import (
            ApplicationBuilder,
            CommandHandler,
            MessageHandler,
            filters
        )

        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        application.add_handler(CommandHandler("ping", handle_commands_telegram))
        application.add_handler(CommandHandler("teste", handle_commands_telegram))
        application.add_handler(CommandHandler("comandos", handle_commands_telegram))

        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_commands_telegram)
        )

        print("[SISTEMA] Telegram operativo e ouvindo comandos.")

        from threading import Thread

        def run_telegram():
            application.run_polling(drop_pending_updates=True)

        Thread(target=run_telegram, daemon=True).start()

    # =========================
    # MONITOR LOOP
    # =========================
    asyncio.create_task(monitor_loop())
    print("[SISTEMA] Motor de monitoramento iniciado.")

    # =========================
    # DISCORD START (FIX REAL)
    # =========================
    token = os.getenv('DISCORD_TOKEN') or DISCORD_TOKEN

    if token:
        print("[DISCORD] Iniciando bot...")
        await bot_discord.start(token)
    else:
        print("[ERRO] Token Discord não encontrado.")


# =========================
# 22 DISCORD COMMAND REGISTRY (ANTI DUPLICAÇÃO + TESTE FIX)
# =========================

import discord
from discord import app_commands

# =========================
# FLAG GLOBAL
# =========================
if not hasattr(bot_discord, "COMMANDS_LOADED"):
    bot_discord.COMMANDS_LOADED = False


# =========================
# REGISTRO ÚNICO DE COMANDOS
# =========================
async def register_discord_commands():

    if bot_discord.COMMANDS_LOADED:
        return

    # evita duplicação de tree já existente
    if bot_discord.tree.get_command("ping") or bot_discord.tree.get_command("teste"):
        bot_discord.COMMANDS_LOADED = True
        return


    # =========================
    # /ping
    # =========================
    @bot_discord.tree.command(name="ping", description="Verifica status do bot")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message(
            "🏓 Pong! Bot ativo.",
            ephemeral=True
        )


    # =========================
    # /comandos
    # =========================
    @bot_discord.tree.command(name="comandos", description="Lista comandos disponíveis")
    async def comandos(interaction: discord.Interaction):
        await interaction.response.send_message(
            "/ping\n/comandos\n/teste",
            ephemeral=True
        )


    # =========================
    # /teste (EXECUTA APENAS BLOCO 16 - SEM DUPLICAR ALERTAS)
    # =========================
    @bot_discord.tree.command(name="teste", description="Executa todos os alertas de teste")
    async def teste(interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        try:
            # EXECUÇÃO ÚNICA DO FLUXO COMPLETO DE TESTE
            await run_full_test_discord()

            await interaction.followup.send(
                "✅ Teste executado com sucesso.",
                ephemeral=True
            )

        except Exception as e:
            await interaction.followup.send(
                f"❌ Erro no teste: {e}",
                ephemeral=True
            )


    bot_discord.COMMANDS_LOADED = True
    print("[DISCORD] Comandos registrados com sucesso.")
