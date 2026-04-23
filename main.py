# =========================
# HEALTH CHECK (MUST BE FIRST LEVEL)
# =========================

def system_health():

    try:
        return {
            "panel_ok": bool(globals().get("panel_message_id") or globals().get("discord_panel_msg_id")),
            "boot_done": globals().get("BOOT_DONE", False),
            "panel_loop": globals().get("PANEL_LOOP_RUNNING", False)
        }

    except Exception as e:
        print(f"[HEALTH ERROR] {e}")
        return {
            "panel_ok": False,
            "boot_done": False,
            "panel_loop": False
        }


# =========================
# AUTO REPAIR SAFE (FIX OBRIGATÓRIO DO LOG)
# =========================

async def auto_repair_panel():
    try:
        await update_panel()
    except Exception as e:
        print(f"[AUTO REPAIR ERROR] {e}")

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
# 2 CONFIGURAÇÃO TELEGRAM / DISCORD (FIX ANTI-DUPLICAÇÃO)
# =========================

import os
import discord
from discord.ext import commands
from telegram import Bot

# =========================
# TOKENS
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# DISCORD BOT
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot_discord = commands.Bot(command_prefix="!", intents=intents)

# =========================
# SETUP HOOK (ÚNICO - REMOVIDA DUPLICAÇÃO)
# =========================

@bot_discord.event
async def setup_hook():
    try:
        await bot_discord.tree.sync()
        print("[SYNC] Slash commands sincronizados no setup_hook")
    except Exception as e:
        print(f"[SYNC HOOK ERROR] {e}")

# =========================
# IDS DO SISTEMA
# =========================

PANEL_CHAT_ID = -1003920883053

panel_message_id = None
discord_panel_msg_id = None
panel_initialized = False

DISCORD_PANEL_CHANNEL_ID = 1494667029150695625
DISCORD_TICKETS_CHANNEL_ID = 1494670074374651985
DISCORD_WEVERSE_CHANNEL_ID = 1494680233025208461
DISCORD_SOCIAL_CHANNEL_ID = 1494682078950981864

# =========================
# TELEGRAM (CORRIGIDO - SEM DUPLO RUNTIME AQUI)
# =========================

bot_ticket = None
telegram_app = None  # mantido só como placeholder (não iniciar aqui)

# =========================
# TELEGRAM LEGACY INIT
# =========================

if TELEGRAM_TOKEN:
    try:
        bot_ticket = Bot(token=TELEGRAM_TOKEN)

        print("[SISTEMA] Telegram configurado com sucesso.")
        print("[SISTEMA] Modo legacy ativo")

    except Exception as e:
        print(f"[ERRO CONFIG TELEGRAM] {e}")

# =========================
# PANEL LOCK (ÚNICO)
# =========================

import asyncio

PANEL_BOOT_LOCK = asyncio.Lock()
PANEL_BOOT_DONE = False

# =========================
# 2.1 TELEGRAM START (PRODUÇÃO - FIX DEFINITIVO)
# =========================

async def start_telegram():

    print("[TELEGRAM] inicializando...")

    try:

        # =========================
        # MODO LEGACY (SEU ATUAL)
        # =========================
        if bot_ticket is not None:
            print("[TELEGRAM] pronto (modo Bot básico)")
            return

        # =========================
        # MODO APPLICATION (FUTURO)
        # =========================
        if telegram_app is not None:
            await telegram_app.initialize()
            await telegram_app.start()
            print("[TELEGRAM] online (Application)")
            return

        # =========================
        # NÃO CONFIGURADO
        # =========================
        print("[TELEGRAM] não configurado — ignorado")

    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")

# =========================
# 3 CONTROLE / CONTADORES GLOBAIS (FIX ESTÁVEL)
# =========================

import asyncio
import time

# =========================
# CONTADORES GLOBAIS
# =========================

total_tickets = 0
total_buy = 0
total_weverse = 0
total_social = 0

last_ticket_check = time.time()
last_buy_check = time.time()
last_weverse_check = time.time()
last_social_check = time.time()

SEEN_TICKET = set()
SEEN_BUY = set()
SEEN_WEVERSE = set()
SEEN_SOCIAL = set()

start_time = time.time()

# 🔒 lock leve para proteger updates concorrentes
COUNTER_LOCK = asyncio.Lock()

# =========================
# FUNÇÕES SEGURAS PARA ATUALIZAR CONTADORES
# =========================

async def increment_ticket():
    global total_tickets
    async with COUNTER_LOCK:
        total_tickets += 1
        return total_tickets

async def increment_buy():
    global total_buy
    async with COUNTER_LOCK:
        total_buy += 1
        return total_buy

async def increment_weverse():
    global total_weverse
    async with COUNTER_LOCK:
        total_weverse += 1
        return total_weverse

async def increment_social():
    global total_social
    async with COUNTER_LOCK:
        total_social += 1
        return total_social

# =========================
# 4 WEB SERVER (PRODUÇÃO BLINDADA)
# =========================

from flask import Flask
from threading import Thread, Lock
import os
import time

app_web = Flask(__name__)

# =========================
# HEALTH CHECK (CORRIGIDO)
# =========================
@app_web.route("/")
def home():
    return {
        "status": "online",
        "service": "Bots Arirang",
        "uptime": int(time.time() - start_time)
    }

@app_web.route("/health")
def health():
    return {
        "status": "ok",
        "uptime": int(time.time() - start_time)
    }

# =========================
# THREAD CONTROL (ANTI-DUPLICAÇÃO REAL)
# =========================

_web_lock = Lock()
_web_started = False


def run_web():
    port = int(os.environ.get("PORT", 8080))

    while True:
        try:
            app_web.run(
                host="0.0.0.0",
                port=port,
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            print(f"[WEB SERVER ERROR] {e}")
            time.sleep(5)  # tenta reiniciar automaticamente


def keep_alive():
    """
    🔒 Garante apenas UMA instância do Flask rodando
    com proteção real contra corrida de threads
    """

    global _web_started

    with _web_lock:

        if _web_started:
            return

        _web_started = True

        thread = Thread(
            target=run_web,
            daemon=True
        )

        thread.start()

        print("[WEB SERVER] iniciado com segurança")

# =========================
# 5 FUNÇÃO ANTI-SPAM (HASH INTELIGENTE)
# =========================

import hashlib
import os
import json
import asyncio
import time

CONTENT_HASH = {}

CACHE_FILE = "content_hash_cache.json"

# 🔒 lock para acesso concorrente
CONTENT_LOCK = asyncio.Lock()

# controle de save otimizado
_last_save_time = 0
SAVE_INTERVAL = 10  # segundos


# =========================
# LOAD CACHE (PERSISTÊNCIA)
# =========================
def load_content_cache():
    global CONTENT_HASH

    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                CONTENT_HASH = json.load(f)
                print("[CACHE] carregado com sucesso")
    except Exception as e:
        print(f"[CACHE LOAD ERROR] {e}")
        CONTENT_HASH = {}


# =========================
# SAVE CACHE (OTIMIZADO)
# =========================
def _save_now():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(CONTENT_HASH, f)
    except Exception as e:
        print(f"[CACHE SAVE ERROR] {e}")


async def save_content_cache():
    global _last_save_time

    now = time.time()

    # evita salvar toda hora
    if now - _last_save_time < SAVE_INTERVAL:
        return

    async with CONTENT_LOCK:
        _save_now()
        _last_save_time = now


# =========================
# NORMALIZAÇÃO INTELIGENTE (MELHORADA)
# =========================
def normalize_html(html):

    if not html:
        return ""

    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        return " ".join(text.split())

    except Exception:
        return " ".join(html.split())


# =========================
# HASH DE CONTEÚDO
# =========================
def generate_hash(content):
    return hashlib.md5(content.encode("utf-8")).hexdigest()


# =========================
# DETECTOR DE MUDANÇA REAL (THREAD SAFE)
# =========================
async def is_new(url, html):

    global CONTENT_HASH

    clean_content = normalize_html(html)
    new_hash = generate_hash(clean_content)

    async with CONTENT_LOCK:

        old_hash = CONTENT_HASH.get(url)

        # primeira vez vendo a URL
        if not old_hash:
            CONTENT_HASH[url] = new_hash
            await save_content_cache()
            return False

        # mudou de verdade
        if old_hash != new_hash:
            CONTENT_HASH[url] = new_hash
            await save_content_cache()
            print(f"[CHANGE DETECTED] {url}")
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

# =========================
# 8 CONTROLE (VERSÃO PRODUÇÃO)
# =========================

from datetime import datetime
import time

# =========================
# UPTIME
# =========================
def get_uptime():
    try:
        s = int(time.time() - start_time)
        return f"{s//3600}h {(s%3600)//60}m {s%60}s"
    except Exception as e:
        print(f"[UPTIME ERROR] {e}")
        return "0h 0m 0s"


# =========================
# STATUS REAL
# =========================
def resolve_status(last_check_time):
    try:
        if not isinstance(last_check_time, (int, float)):
            print(f"[STATUS WARNING] valor inválido: {last_check_time}")
            return "🔴"

        agora = time.time()
        diff = agora - last_check_time

        if diff > 1800:
            return "🔴"
        elif diff > 600:
            return "🟡"
        else:
            return "🟢"

    except Exception as e:
        print(f"[STATUS ERROR] {e}")
        return "🔴"


# =========================
# CLEAN SAFE VALUE
# =========================
def clean(v):
    try:
        return v if v and str(v).strip() else "ESGOTADO"
    except Exception as e:
        print(f"[CLEAN ERROR] {e}")
        return "ESGOTADO"


# =========================
# DAYS LEFT
# =========================
def days_left(date_str):
    try:
        if not date_str or not isinstance(date_str, str):
            return 0

        target = datetime.strptime(date_str, "%d/%m/%Y").date()
        today = datetime.now().date()

        return max((target - today).days, 0)

    except Exception as e:
        print(f"[DATE PARSE ERROR] {date_str} -> {e}")
        return 0


# =========================
# TIME UTILS
# =========================
def minutes_since(ts):
    try:
        if not isinstance(ts, (int, float)):
            return 0
        return int((time.time() - ts) / 60)
    except Exception as e:
        print(f"[TIME ERROR] {e}")
        return 0


# =========================
# COUNTDOWN DATA (ROBUSTO + LOG)
# =========================
def get_countdown_data():

    now_dt = datetime.now()

    prox_data = "Continua…"
    prox_local = "---"
    d_prox = 0
    d_br = 0

    if not isinstance(AGENDA, list):
        print("[AGENDA ERROR] formato inválido")
        return prox_data, prox_local, d_prox, d_br

    for item in AGENDA:

        if not isinstance(item, (list, tuple)) or len(item) < 4:
            print(f"[AGENDA WARNING] item inválido ignorado: {item}")
            continue

        try:
            show_dt = datetime.strptime(
                f"{item[0]} {item[3]}",
                "%d/%m/%Y %H:%M"
            )

            # próximo show global
            if show_dt > now_dt and prox_data == "Continua…":
                prox_data = item[0]
                prox_local = f"{item[1]}, {item[2]}"
                d_prox = (show_dt.date() - now_dt.date()).days

            # Brasil separado
            if "Brasil" in str(item[2]) and d_br == 0:
                br_date = datetime.strptime(item[0], "%d/%m/%Y").date()

                if br_date >= now_dt.date():
                    d_br = (br_date - now_dt.date()).days

        except Exception as e:
            print(f"[AGENDA PARSE ERROR] {item} -> {e}")
            continue

    return prox_data, prox_local, d_prox, d_br


# =========================
# STATUS COLOR
# =========================
def status_color(last_check):
    return resolve_status(last_check)

# =========================
# 9 SESSION HTTP (PRODUÇÃO SEGURA)
# =========================

import aiohttp
import asyncio
import time

http_session = None
_session_lock = asyncio.Lock()


# =========================
# GET SESSION (THREAD SAFE)
# =========================
async def get_session():

    global http_session

    async with _session_lock:

        if http_session is None or http_session.closed:

            http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
                    )
                }
            )

            print("[SESSION] nova sessão HTTP criada")

    return http_session


# =========================
# FETCH COM RETRY
# =========================
async def fetch(url, retries=2):

    for attempt in range(retries + 1):

        try:
            session = await get_session()

            async with session.get(url) as resp:

                if resp.status != 200:
                    print(f"[HTTP WARNING] {url} status={resp.status}")
                    return None

                return await resp.text()

        except asyncio.TimeoutError:
            print(f"[HTTP TIMEOUT] {url} tentativa {attempt+1}")

        except Exception as e:
            print(f"[FETCH ERROR] {url} -> {e}")

        await asyncio.sleep(1)  # pequeno backoff

    return None


# =========================
# CLOSE SEGURO (SHUTDOWN)
# =========================
async def close_session():

    global http_session

    try:
        if http_session and not http_session.closed:
            await http_session.close()
            print("[SESSION] fechada com segurança")

    except Exception as e:
        print(f"[SESSION CLOSE ERROR] {e}")

# =========================
# 10 EMOJIS (PRODUÇÃO LIMPA)
# =========================

import re

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


# =========================
# NORMALIZAÇÃO SEGURA
# =========================
def normalize_name(name: str) -> str:

    if not name:
        return ""

    name = name.lower().strip()

    # remove espaços e caracteres especiais leves
    name = re.sub(r"[^a-z0-9]", "", name)

    return name


# =========================
# GET EMOJI (VERSÃO FINAL)
# =========================
def get_member_emoji(member_name: str) -> str:

    key = normalize_name(member_name)

    return MEMBER_EMOJI.get(key, "💜")


# =========================
# FORMATADOR ÚNICO (SEM DUPLICAÇÃO)
# =========================
def format_member(member_name: str):

    emoji = get_member_emoji(member_name)

    name = str(member_name).upper().strip()

    return {
        "emoji": emoji,
        "name": name,
        "display": f"{emoji} {name}"
    }

# =========================
# 11 CORE ROUTER (PRODUÇÃO SEGURA)
# =========================

import asyncio
import discord


# =========================
# DISCORD SAFE SEND
# =========================
async def send_discord(channel_id, content=None, embed=None):

    try:
        channel = bot_discord.get_channel(channel_id)

        # fallback se cache falhar
        if channel is None:
            channel = await bot_discord.fetch_channel(channel_id)

        if not channel:
            print(f"[DISCORD] canal não encontrado: {channel_id}")
            return

        if embed is None and content is not None:
            embed = discord.Embed(
                description=content,
                color=0x8A2BE2
            )

        await channel.send(embed=embed)

    except Exception as e:
        print(f"[DISCORD SEND ERROR] {e}")


# =========================
# SAFE TASK WRAPPER
# =========================
def safe_task(coro, label="TASK"):

    async def wrapper():
        try:
            await coro
        except Exception as e:
            print(f"[TASK ERROR {label}] {e}")

    return asyncio.create_task(wrapper())


# =========================
# ALERT ROUTER (REFATORADO)
# =========================
async def send_alert(alert_type, message):

    try:

        # =========================
        # TELEGRAM (SAFE)
        # =========================
        test_mode = globals().get("TEST_MODE", False)

        if bot_ticket is not None and not test_mode:
            try:
                await bot_ticket.send_message(
                    chat_id=PANEL_CHAT_ID,
                    text=message
                )
            except Exception as e:
                print(f"[TELEGRAM ERROR] {e}")

        # =========================
        # DISCORD ROUTING MAP
        # =========================
        discord_map = {
            "ticket": DISCORD_TICKETS_CHANNEL_ID,
            "reposicao": DISCORD_TICKETS_CHANNEL_ID,
            "agenda": DISCORD_TICKETS_CHANNEL_ID,

            "weverse_post": DISCORD_WEVERSE_CHANNEL_ID,
            "weverse_live": DISCORD_WEVERSE_CHANNEL_ID,
            "weverse_news": DISCORD_WEVERSE_CHANNEL_ID,
            "weverse_media": DISCORD_WEVERSE_CHANNEL_ID,

            "instagram_post": DISCORD_SOCIAL_CHANNEL_ID,
            "instagram_reels": DISCORD_SOCIAL_CHANNEL_ID,
            "instagram_stories": DISCORD_SOCIAL_CHANNEL_ID,
            "instagram_live": DISCORD_SOCIAL_CHANNEL_ID,

            "tiktok_post": DISCORD_SOCIAL_CHANNEL_ID,
            "tiktok_live": DISCORD_SOCIAL_CHANNEL_ID,

            "youtube_post": DISCORD_SOCIAL_CHANNEL_ID,
            "youtube_live": DISCORD_SOCIAL_CHANNEL_ID,
        }

        channel_id = discord_map.get(alert_type)

        if channel_id:

            safe_task(
                send_discord(channel_id, content=message),
                label=alert_type
            )

    except Exception as e:
        print(f"[ALERT ROUTER ERROR] {e}")

# =========================
# 12 PAINEL (PRODUÇÃO ESTÁVEL)
# =========================

import asyncio
import time
import discord


# =========================
# LOCK GLOBAL DO PAINEL
# =========================
panel_lock = asyncio.Lock()
last_panel_update = 0


# =========================
# FUNÇÃO CENTRAL ÚNICA (SEM DUPLICAÇÃO)
# =========================
async def update_panel():

    global panel_message_id, discord_panel_msg_id, last_panel_update

    # 🔒 evita execução antes do bot estar pronto
    if bot_ticket is None or bot_discord is None:
        print("[PANEL] bots ainda não prontos")
        return

    async with panel_lock:

        now = time.time()

        # anti spam (mínimo 5s entre updates)
        if now - last_panel_update < 5:
            return

        last_panel_update = now

        try:
            data_show, city, d_prox, d_br = get_countdown_data()
            texto = gerar_texto_painel(data_show, city, d_prox, d_br)
        except Exception as e:
            print(f"[PANEL DATA ERROR] {e}")
            return

        # =========================
        # TELEGRAM SAFE UPDATE
        # =========================
        if bot_ticket and PANEL_CHAT_ID:

            try:
                if panel_message_id:

                    try:
                        await bot_ticket.edit_message_text(
                            chat_id=PANEL_CHAT_ID,
                            message_id=panel_message_id,
                            text=texto
                        )
                        return

                    except Exception as e:
                        print(f"[TELEGRAM EDIT FAIL] {e}")
                        panel_message_id = None

                msg = await bot_ticket.send_message(
                    chat_id=PANEL_CHAT_ID,
                    text=texto
                )

                panel_message_id = msg.message_id

                try:
                    await bot_ticket.pin_chat_message(
                        chat_id=PANEL_CHAT_ID,
                        message_id=panel_message_id,
                        disable_notification=True
                    )
                except Exception as e:
                    print(f"[TELEGRAM PIN FAIL] {e}")

            except Exception as e:
                print(f"[TELEGRAM PANEL ERROR] {e}")


        # =========================
        # DISCORD SAFE UPDATE
        # =========================
        if DISCORD_PANEL_CHANNEL_ID:

            try:
                channel = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)

                if channel is None:
                    channel = await bot_discord.fetch_channel(DISCORD_PANEL_CHANNEL_ID)

                if not channel:
                    print("[DISCORD PANEL] canal não encontrado")
                    return

                embed = discord.Embed(
                    description=texto,
                    color=0x8A2BE2
                )

                # 1) tenta mensagem salva
                if discord_panel_msg_id:
                    try:
                        msg = await channel.fetch_message(discord_panel_msg_id)
                        await msg.edit(embed=embed)
                        return
                    except Exception as e:
                        print(f"[DISCORD EDIT FAIL] {e}")
                        discord_panel_msg_id = None

                # 2) fallback histórico
                try:
                    async for m in channel.history(limit=25):
                        if m.author == bot_discord.user:
                            discord_panel_msg_id = m.id
                            await m.edit(embed=embed)
                            return
                except Exception as e:
                    print(f"[DISCORD HISTORY FAIL] {e}")

                # 3) cria nova mensagem
                msg = await channel.send(embed=embed)
                discord_panel_msg_id = msg.id

            except Exception as e:
                print(f"[DISCORD PANEL ERROR] {e}")


# =========================
# PAINEL BLINDADO (RECOVERY ROBUSTO)
# =========================
async def ensure_single_panel():

    global PANEL_BOOT_DONE
    global panel_message_id, discord_panel_msg_id

    async with PANEL_BOOT_LOCK:

        if PANEL_BOOT_DONE:
            return

        print("[12.1] iniciando recovery blindado...")

        # =========================
        # TELEGRAM RECOVERY
        # =========================
        try:
            saved_id = carregar_id_telegram()
            panel_message_id = saved_id if saved_id else None
        except Exception as e:
            print(f"[TELEGRAM RECOVERY ERROR] {e}")
            panel_message_id = None


        # =========================
        # DISCORD RECOVERY (VALIDADO)
        # =========================
        try:

            if bot_discord is None:
                print("[RECOVERY] bot discord ainda não pronto")
                discord_panel_msg_id = None
                return

            channel = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)

            if channel is None:
                channel = await bot_discord.fetch_channel(DISCORD_PANEL_CHANNEL_ID)

            if channel:

                async for msg in channel.history(limit=50):

                    if (
                        msg.author == bot_discord.user
                        and msg.embeds
                        and "ARIRANG TOUR" in msg.embeds[0].description
                    ):
                        discord_panel_msg_id = msg.id
                        break

        except Exception as e:
            print(f"[12.1 DISCORD RECOVERY ERROR] {e}")
            discord_panel_msg_id = None


        PANEL_BOOT_DONE = True
        print("[12.1] painel único garantido com validação real")


# =========================
# SAFE BOOT WRAPPER
# =========================
async def safe_boot():

    async with PANEL_BOOT_LOCK:

        if PANEL_BOOT_DONE:
            return

        try:
            await ensure_single_panel()
        except Exception as e:
            print(f"[BOOT ERROR] {e}")
            return

        await asyncio.sleep(2)

        print("[BOOT] sistema estabilizado com painel único")

# =========================
# 12.1 PAINEL BLINDADO (RECOVERY ROBUSTO)
# =========================

import asyncio

PANEL_BOOT_LOCK = asyncio.Lock()
PANEL_BOOT_DONE = False


async def ensure_single_panel():

    global PANEL_BOOT_DONE
    global panel_message_id, discord_panel_msg_id

    async with PANEL_BOOT_LOCK:

        if PANEL_BOOT_DONE:
            return

        print("[12.1] iniciando recovery blindado...")

        telegram_ok = False
        discord_ok = False

        # =========================
        # TELEGRAM RECOVERY
        # =========================
        try:
            saved_id = carregar_id_telegram()

            if saved_id:
                panel_message_id = saved_id
                telegram_ok = True
            else:
                panel_message_id = None

        except Exception as e:
            print(f"[TELEGRAM RECOVERY ERROR] {e}")
            panel_message_id = None


        # =========================
        # DISCORD RECOVERY (VALIDADO)
        # =========================
        try:

            if bot_discord is None:
                print("[RECOVERY] bot discord ainda não pronto")
                discord_panel_msg_id = None
            else:

                channel = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)

                if channel is None:
                    channel = await bot_discord.fetch_channel(DISCORD_PANEL_CHANNEL_ID)

                if channel:

                    async for msg in channel.history(limit=50):

                        if (
                            msg.author == bot_discord.user
                            and msg.embeds
                            and msg.embeds[0].description
                            and "ARIRANG TOUR" in msg.embeds[0].description
                        ):
                            discord_panel_msg_id = msg.id
                            discord_ok = True
                            break

        except Exception as e:
            print(f"[12.1 DISCORD RECOVERY ERROR] {e}")
            discord_panel_msg_id = None


        # =========================
        # SÓ FINALIZA SE PELO MENOS 1 OK
        # =========================
        if telegram_ok or discord_ok:
            PANEL_BOOT_DONE = True
            print("[12.1] painel único garantido com validação real")
        else:
            print("[12.1] recovery falhou - tentando novamente no próximo boot")
            PANEL_BOOT_DONE = False


# =========================
# SAFE BOOT WRAPPER (OBRIGATÓRIO NO STARTUP)
# =========================
async def safe_boot():

    async with PANEL_BOOT_LOCK:

        if PANEL_BOOT_DONE:
            return

        await ensure_single_panel()

        await asyncio.sleep(2)

        if PANEL_BOOT_DONE:
            print("[BOOT] sistema estabilizado com painel único")
        else:
            print("[BOOT] sistema ainda em recuperação")

# =========================
# 13 WEVERSE ALERTS (PRODUÇÃO SEGURA)
# =========================

import hashlib
import asyncio

# =========================
# CACHE GLOBAL POR TIPO + CONTEÚDO
# =========================
WEVERSE_CACHE = {}

# 🔒 lock para evitar race condition em concorrência
WEVERSE_LOCK = asyncio.Lock()


def is_new_weverse_event(event_type, url, content=""):

    """
    Evita duplicação REAL usando:
    - tipo do evento
    - URL
    - conteúdo
    """

    raw = f"{event_type}:{url}:{content}"
    new_hash = hashlib.md5(raw.encode("utf-8")).hexdigest()

    if WEVERSE_CACHE.get(event_type) == new_hash:
        return False

    WEVERSE_CACHE[event_type] = new_hash
    return True


# =========================
# POST
# =========================
async def weverse_post(url, member_name, title, message_translated, found):

    async with WEVERSE_LOCK:

        if not is_new_weverse_event("post", url, title + message_translated):
            return

        global total_weverse, last_weverse_check

        total_weverse += 1
        last_weverse_check = time.time()

        emoji = get_member_emoji(member_name)

        msg = f"""
🩷 WEVERSE POST 🩷
{emoji} {member_name.upper()} fez uma publicação 
📌 {title}
📝 {message_translated}
🔗 {url}
"""

        await send_alert("weverse_post", msg)
        await update_panel()


# =========================
# LIVE
# =========================
async def weverse_live(url, member_name, found):

    async with WEVERSE_LOCK:

        if not is_new_weverse_event("live", url):
            return

        global total_weverse, last_weverse_check

        total_weverse += 1
        last_weverse_check = time.time()

        emoji = get_member_emoji(member_name)

        msg = f"""
📹 WEVERSE LIVE 📹
{emoji} {member_name.upper()} está ao vivo
🔗 {url}
"""

        await send_alert("weverse_live", msg)
        await update_panel()


# =========================
# NEWS
# =========================
async def weverse_news(url, member_name, message_translated, found):

    async with WEVERSE_LOCK:

        if not is_new_weverse_event("news", url, message_translated):
            return

        global total_weverse, last_weverse_check

        total_weverse += 1
        last_weverse_check = time.time()

        emoji = get_member_emoji(member_name)

        msg = f"""
🚨 WEVERSE NEWS 🚨
{emoji} {member_name.upper()} fez uma publicação 
📝 {message_translated}
🔗 {url}
"""

        await send_alert("weverse_news", msg)
        await update_panel()


# =========================
# MEDIA
# =========================
async def weverse_media(url, member_name, title, message_translated, found):

    async with WEVERSE_LOCK:

        if not is_new_weverse_event("media", url, title + message_translated):
            return

        global total_weverse, last_weverse_check

        total_weverse += 1
        last_weverse_check = time.time()

        emoji = get_member_emoji(member_name)

        msg = f"""
📀 WEVERSE MEDIA 📀
{emoji} {member_name.upper()} fez uma publicação 
⭐ {title}
📝 {message_translated}
🔗 {url}
"""

        await send_alert("weverse_media", msg)
        await update_panel()

# =========================
# 14 INSTAGRAM ALERTS (PRODUÇÃO SEGURA)
# =========================

import hashlib
import asyncio

# =========================
# CACHE GLOBAL POR EVENTO
# =========================
INSTAGRAM_CACHE = {
    "post": None,
    "reel": None,
    "story": None,
    "live": None
}

# 🔒 lock global para evitar race condition
INSTAGRAM_LOCK = asyncio.Lock()


def is_new_instagram(event_type, url, extra=""):

    raw = f"{event_type}:{url}:{extra}"
    new_hash = hashlib.md5(raw.encode("utf-8")).hexdigest()

    if INSTAGRAM_CACHE.get(event_type) == new_hash:
        return False

    INSTAGRAM_CACHE[event_type] = new_hash
    return True


# =========================
# POST
# =========================
async def instagram_post(url, member_name, title, found):

    async with INSTAGRAM_LOCK:

        if not is_new_instagram("post", url, title):
            return

        global total_social, last_social_check

        total_social += 1
        last_social_check = time.time()

        emoji, name = format_member(member_name)

        msg = f"""
🌟 INSTAGRAM POST 🌟
{emoji} {name} fez uma publicação 
🔗 {url}
"""

        await send_alert("instagram_post", msg)
        await update_panel()


# =========================
# REEL
# =========================
async def instagram_reel(url, member_name, title, found):

    async with INSTAGRAM_LOCK:

        if not is_new_instagram("reel", url, title):
            return

        global total_social, last_social_check

        total_social += 1
        last_social_check = time.time()

        emoji, name = format_member(member_name)

        msg = f"""
🎬 INSTAGRAM REELS 🎬
{emoji} {name} publicou um reels 
🔗 {url}
"""

        await send_alert("instagram_reels", msg)
        await update_panel()


# =========================
# STORY
# =========================
async def instagram_story(url, member_name, title, found):

    async with INSTAGRAM_LOCK:

        if not is_new_instagram("story", url, title):
            return

        global total_social, last_social_check

        total_social += 1
        last_social_check = time.time()

        emoji, name = format_member(member_name)

        msg = f"""
🫧 INSTAGRAM STORY 🫧
{emoji} {name} publicou stories
🔗 {url}
"""

        await send_alert("instagram_stories", msg)
        await update_panel()


# =========================
# LIVE (CACHE CORRIGIDO)
# =========================
async def instagram_live(url, member_name, title, found):

    async with INSTAGRAM_LOCK:

        if not is_new_instagram("live", url):
            return

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
# 15 ALERTAS TIKTOK E YOUTUBE (PRODUÇÃO SEGURA)
# =========================

import asyncio
import hashlib

# =========================
# CACHE GLOBAL
# =========================
LAST_TIKTOK = {}
LAST_YOUTUBE = {}

# 🔒 lock global para evitar concorrência
SOCIAL_LOCK = asyncio.Lock()


def is_new_social(cache, key):
    if cache.get(key):
        return False
    cache[key] = True
    return True


# =========================
# TIKTOK POST
# =========================
async def tiktok_post(url, member_name, title, found):

    async with SOCIAL_LOCK:

        key = f"post:{member_name}:{url}"
        if not is_new_social(LAST_TIKTOK, key):
            return

        emoji = get_member_emoji(member_name)

        msg = f"""

🎵 TIKTOK POST 🎵
{emoji} {member_name.upper()} publicou um vídeo
🔗 {url}

"""

        await send_alert("tiktok_post", msg)
        await update_panel()


# =========================
# TIKTOK LIVE
# =========================
async def tiktok_live(url, member_name, title, found):

    async with SOCIAL_LOCK:

        key = f"live:{member_name}:{url}"
        if not is_new_social(LAST_TIKTOK, key):
            return

        emoji = get_member_emoji(member_name)

        msg = f"""

🎥 TIKTOK LIVE 🎥
{emoji} {member_name.upper()} está ao vivo
🔗 {url}

"""

        await send_alert("tiktok_live", msg)
        await update_panel()


# =========================
# YOUTUBE POST
# =========================
async def youtube_post(url, final_url=None):

    async with SOCIAL_LOCK:

        key = f"post:{url}"
        if not is_new_social(LAST_YOUTUBE, key):
            return

        link = final_url or "https://www.youtube.com/@BTS"

        msg = f"""

🎞️ YOUTUBE POST 🎞️
💜 BTS publicou vídeo novo
🔗 {link}

"""

        await send_alert("youtube_post", msg)
        await update_panel()


# =========================
# YOUTUBE LIVE
# =========================
async def youtube_live(url=None):

    async with SOCIAL_LOCK:

        key = "live:youtube"
        if not is_new_social(LAST_YOUTUBE, key):
            return

        live_url = "https://www.youtube.com/@BTS/live"

        msg = f"""

📹 YOUTUBE LIVE 📹
🚨 BTS está ao vivo agora
🔗 {live_url}

"""

        await send_alert("youtube_live", msg)
        await update_panel()

# =========================
# 15.1 TICKETMASTER & BUYTICKET (PRODUÇÃO SEGURA)
# =========================

import hashlib

EVENT_CACHE = {
    "reposicao": {},
    "agenda": {},
    "revenda": {}
}


def is_new_event(event_type, key):

    """
    key = assinatura única do evento (url + data + setor etc)
    """

    new_hash = hashlib.md5(key.encode("utf-8")).hexdigest()

    if EVENT_CACHE[event_type].get(key) == new_hash:
        return False

    EVENT_CACHE[event_type][key] = new_hash
    return True


# =========================
# REPOSIÇÃO TICKETMASTER
# =========================
async def ticket_reposicao(url, data, setor, categoria):
    global total_tickets, last_ticket_check

    key = f"{url}:{data}:{setor}:{categoria}"

    if not is_new_event("reposicao", key):
        return

    msg = f"""

🔥 ALERTA DE REPOSIÇÃO 🔥
📅 Data: {data}
🔗 Link: {url}

🎫 Setor: {setor}
🏷️ Categoria: {categoria}

"""

    await send_alert("reposicao", msg)
    await update_panel()


# =========================
# NOVAS DATAS (AGENDA OFICIAL BTS)
# =========================
async def ticket_agenda(url, data, cidade, pais):
    global total_tickets, last_ticket_check

    key = f"{url}:{data}:{cidade}:{pais}"

    if not is_new_event("agenda", key):
        return

    msg = f"""

💜 AGENDA - NOVAS DATAS 💜
📅 Data: {data}
🏙️ Cidade: {cidade}
🌎 País: {pais}
🔗 Link: {url}

ℹ️ Mais informações em breve

"""

    await send_alert("agenda", msg)
    await update_panel()


# =========================
# REVENDA BUYTICKET
# =========================
async def buyticket_revenda(url, data, valor, setor, categoria):
    global total_buy, last_buy_check

    key = f"{url}:{data}:{valor}:{setor}:{categoria}"

    if not is_new_event("revenda", key):
        return

    msg = f"""

🎫 REVENDA BUYTICKET 🎫
📅 Data: {data}
🔗 Link: {url}
💰 Valor: {valor}

🎫 Setor: {setor}
🏷️ Categoria: {categoria}

"""

    await send_alert("buyticket_revenda", msg)
    await update_panel()


# =========================
# 16 SISTEMA DE TESTE (ESTRUTURA FIXA E SEGURA)
# =========================

import os
import asyncio

# =========================
# AMBIENTE ISOLADO (PRODUÇÃO VS TESTE REAL)
# =========================

ENV_MODE = os.getenv("ENV_MODE", "production")
TEST_MODE = ENV_MODE == "test"
PROD_MODE = ENV_MODE == "production"


# =========================
# ROUTER SEGURO (NUNCA VAZA PARA PRODUÇÃO)
# =========================

async def safe_send_alert(alert_type, message):

    # TEST MODE: apenas log
    if TEST_MODE:
        print(f"[TEST MODE ALERT] {alert_type}")
        print(message)
        return

    # PRODUÇÃO REAL
    await send_alert(alert_type, message)


async def safe_update_panel():

    if TEST_MODE:
        print("[TEST MODE] painel ignorado")
        return

    await update_panel()


# =========================
# RUN TEST DISCORD (BATERIA COMPLETA)
# =========================
async def run_full_test_discord():

    print("[TESTE DC] iniciando bateria completa...")

    try:

        # =========================
        # TICKET + BUY
        # =========================
        await test_ticket_reposicao()
        await test_ticket_agenda()
        await test_buyticket_revenda()
        await asyncio.sleep(1)

        # =========================
        # WEVERSE
        # =========================
        await test_weverse_post()
        await test_weverse_live()
        await test_weverse_news()
        await test_weverse_media()
        await asyncio.sleep(1)

        # =========================
        # INSTAGRAM
        # =========================
        await test_instagram_post()
        await test_instagram_reel()
        await test_instagram_story()
        await test_instagram_live()
        await asyncio.sleep(1)

        # =========================
        # TIKTOK + YOUTUBE
        # =========================
        await test_tiktok_post()
        await test_tiktok_live()
        await test_youtube_post()
        await test_youtube_live()

    finally:
        print("[TESTE DC] finalizado")


# =========================
# TICKET + BUY TESTS
# =========================
async def test_ticket_reposicao():

    msg = f"""

⚠️ TESTE ⚠️
🔥 ALERTA DE REPOSIÇÃO 🔥
📅 Data: 28/10/2026
🔗 Link: https://www.ticketmaster.com.br/event/venda-geral-bts
🎫 Setor: TESTE
🏷️ Categoria: TESTE

"""

    await safe_send_alert("reposicao", msg)


async def test_ticket_agenda():

    msg = f"""

⚠️ TESTE ⚠️
💜 AGENDA - NOVAS DATAS 💜
📅 Data: 29/10/2026
🏙️ Cidade: São Paulo
🌎 País: Brasil
🔗 Link: https://www.bts-official.com/agenda

"""

    await safe_send_alert("agenda", msg)


async def test_buyticket_revenda():

    msg = f"""

⚠️ TESTE ⚠️
🎫 REVENDA BUYTICKET 🎫
📅 Data: 30/10/2026
🔗 Link: https://www.buyticket.com.br/bts
💰 Valor: TESTE
🎫 Setor: TESTE
🏷️ Categoria: TESTE

"""

    await safe_send_alert("buyticket_revenda", msg)


# =========================
# WEVERSE TESTS
# =========================
async def test_weverse_post():

    msg = f"""

⚠️ TESTE ⚠️
🩷 WEVERSE POST 🩷
💜 BTS publicou uma mensagem
📌 Título Teste
📝 Conteúdo teste
🔗 https://weverse.io/bts

"""

    await safe_send_alert("weverse_post", msg)


async def test_weverse_live():

    msg = f"""

⚠️ TESTE ⚠️
📹 WEVERSE LIVE 📹
💜 BTS está ao vivo
🔗 https://weverse.io/bts/live

"""

    await safe_send_alert("weverse_live", msg)


async def test_weverse_news():

    msg = f"""

⚠️ TESTE ⚠️
🚨 WEVERSE NEWS 🚨
💜 BTS publicou notícia
📝 Teste de notícia
🔗 https://weverse.io/bts/news

"""

    await safe_send_alert("weverse_news", msg)


async def test_weverse_media():

    msg = f"""

⚠️ TESTE ⚠️
📀 WEVERSE MEDIA 📀
💜 BTS publicou mídia
⭐ Teste mídia
📝 Descrição teste
🔗 https://weverse.io/bts/media

"""

    await safe_send_alert("weverse_media", msg)


# =========================
# INSTAGRAM TESTS
# =========================
async def test_instagram_post():

    msg = f"""

⚠️ TESTE ⚠️
🌟 INSTAGRAM POST 🌟
💜 BTS postou uma foto
🔗 https://instagram.com/bts

"""

    await safe_send_alert("instagram_post", msg)


async def test_instagram_reel():

    msg = f"""

⚠️ TESTE ⚠️
🎬 INSTAGRAM REELS 🎬
💜 BTS postou um reels
🔗 https://instagram.com/bts/reels

"""

    await safe_send_alert("instagram_reels", msg)


async def test_instagram_story():

    msg = f"""

⚠️ TESTE ⚠️
🫧 INSTAGRAM STORIES 🫧
💜 BTS atualizou stories
🔗 https://instagram.com/bts

"""

    await safe_send_alert("instagram_stories", msg)


async def test_instagram_live():

    msg = f"""

⚠️ TESTE ⚠️
🎥 INSTAGRAM LIVE 🎥
💜 BTS está ao vivo
🔗 https://instagram.com/bts/live

"""

    await safe_send_alert("instagram_live", msg)


# =========================
# TIKTOK + YOUTUBE TESTS
# =========================
async def test_tiktok_post():

    msg = f"""

⚠️ TESTE ⚠️
🎵 TIKTOK POST 🎵
💜 BTS postou vídeo
🔗 https://tiktok.com/@bts

"""

    await safe_send_alert("tiktok_post", msg)


async def test_tiktok_live():

    msg = f"""

⚠️ TESTE ⚠️
🎥 TIKTOK LIVE 🎥
💜 BTS ao vivo
🔗 https://tiktok.com/@bts/live

"""

    await safe_send_alert("tiktok_live", msg)


async def test_youtube_post():

    msg = f"""

⚠️ TESTE ⚠️
🎞️ YOUTUBE POST 🎞️
💜 BTS vídeo novo
🔗 https://youtube.com/@BTS

"""

    await safe_send_alert("youtube_post", msg)


async def test_youtube_live():

    msg = f"""

⚠️ TESTE ⚠️
📹 YOUTUBE LIVE 📹
🚨 BTS ao vivo
🔗 https://youtube.com/@BTS/live

"""

    await safe_send_alert("youtube_live", msg)

# =========================
# 17 COMMAND ENGINE FRAMEWORK FINAL
# =========================

COMMANDS = {}


# =========================
# REGISTRADOR DE COMANDOS
# =========================
def command(name):
    def wrapper(func):
        COMMANDS[name] = func
        return func
    return wrapper


# =========================
# CONTEXTO PADRÃO
# =========================
class CommandContext:

    def __init__(self, origin, interaction=None, chat_id=None):
        self.origin = origin
        self.interaction = interaction
        self.chat_id = chat_id

    @property
    def is_discord(self):
        return self.origin == "discord"

    @property
    def is_telegram(self):
        return self.origin == "telegram"


# =========================
# DISPATCHER CENTRAL
# =========================
async def execute_command(cmd, ctx):

    handler = COMMANDS.get(cmd)

    if not handler:
        return

    await handler(ctx)


# =========================
# SENDER UNIFICADO
# =========================
async def send(ctx, text):

    # =========================
    # DISCORD OUTPUT
    # =========================
    if ctx.is_discord and ctx.interaction:

        try:
            if ctx.interaction.response.is_done():
                await ctx.interaction.followup.send(text)
            else:
                await ctx.interaction.response.send_message(text)
        except Exception as e:
            print(f"[DISCORD SEND ERROR] {e}")


    # =========================
    # TELEGRAM OUTPUT
    # =========================
    elif ctx.is_telegram and ctx.chat_id:

        try:
            await bot_ticket.send_message(
                chat_id=ctx.chat_id,
                text=text
            )
        except Exception as e:
            print(f"[TELEGRAM SEND ERROR] {e}")


# =========================
# /PING
# =========================
@command("ping")
async def ping(ctx):
    await send(ctx, f"🏓 Pong! {get_uptime()}")


# =========================
# /COMANDOS
# =========================
@command("comandos")
async def comandos(ctx):
    await send(ctx, "/ping\n/comandos\n/teste\n/bts")


# =========================
# /BTS (MULTI OUTPUT CONTROLADO)
# =========================
@command("bts")
async def bts(ctx):

    membros = [
        "🐨 KIM NAMJOON",
        "🐹 KIM SEOKJIN",
        "🐱 MIN YOONGI",
        "🐿️ JUNG HOSEOK",
        "🐥 PARK JIMIN",
        "🐻 KIM TAEHYUNG",
        "🐰 JEON JUNGKOOK",
        "💜 BTS"
    ]

    texto_final = "\n".join(membros) + \
        "\n\n🪭Ouça Arirang no Spotify🪭\nhttps://open.spotify.com/intl-pt/album/3ukkRHDHbN8tNRPKsGZR1h"


    # =========================
    # DISCORD (MODO ANIMADO)
    # =========================
    if ctx.is_discord and ctx.interaction:

        await ctx.interaction.response.send_message(membros[0])

        for m in membros[1:]:
            await asyncio.sleep(1.2)
            await ctx.interaction.channel.send(m)

        await asyncio.sleep(1.2)
        await ctx.interaction.channel.send(
            "🪭Ouça Arirang no Spotify🪭\nhttps://open.spotify.com/intl-pt/album/3ukkRHDHbN8tNRPKsGZR1h"
        )

        return


    # =========================
    # TELEGRAM (VERSÃO LIMPA E EQUIVALENTE)
    # =========================
    await send(ctx, texto_final)


# =========================
# /TESTE
# =========================
@command("teste")
async def teste(ctx):

    await send(ctx, "⚠️ Iniciando teste completo...")

    try:
        await run_full_test_discord()
        await send(ctx, "✅ Teste finalizado")

    except Exception as e:
        await send(ctx, f"❌ Erro: {e}")


# =========================
# DISCORD HANDLER
# =========================
async def executar_discord(cmd, interaction):

    ctx = CommandContext(
        origin="discord",
        interaction=interaction
    )

    await execute_command(cmd, ctx)


# =========================
# TELEGRAM HANDLER
# =========================
async def executar_telegram(update, context):

    text = update.message.text.strip().lower()

    if not text.startswith("/"):
        return

    cmd = text.replace("/", "").split("@")[0]

    ctx = CommandContext(
        origin="telegram",
        chat_id=update.message.chat_id
    )

    await execute_command(cmd, ctx)

# =========================
# 18 DISCORD ON_READY + SYNC + TELEGRAM INTELLIGENT PANEL (FIX FINAL)
# =========================

import asyncio
import time
import aiohttp
import discord
from datetime import datetime
from bs4 import BeautifulSoup


# =========================
# STATUS COUNTDOWN DATA (CORRIGIDO DUPLICAÇÃO)
# =========================
def get_countdown_data():

    now_dt = datetime.now()

    next_global_date = "Continua…"
    next_global_local = "---"
    days_to_next_global = 0
    days_to_brazil = 0

    for item in AGENDA:
        try:
            show_dt = datetime.strptime(f"{item[0]} {item[3]}", "%d/%m/%Y %H:%M")

            if show_dt > now_dt:
                next_global_date = item[0]
                next_global_local = f"{item[1]}, {item[2]}"
                days_to_next_global = (show_dt.date() - now_dt.date()).days
                break
        except:
            continue

    for item in AGENDA:
        try:
            if "Brasil" in item[2]:
                br_date = datetime.strptime(item[0], "%d/%m/%Y").date()

                if br_date >= now_dt.date():
                    days_to_brazil = (br_date - now_dt.date()).days
                    break
        except:
            continue

    return next_global_date, next_global_local, days_to_next_global, days_to_brazil


# =========================
# PAINEL TEXTO (MANTIDO 100% IGUAL)
# =========================
def gerar_texto_painel(data_show, city, d_prox, d_br):

    return f"""🪭 ⊙⊝⊜ ARIRANG TOUR ⊙⊝⊜ 🪭

✈️ PRÓXIMAS DATAS

🎫 Data: {data_show}
📍 Local: {city}
🔔 Faltam {d_prox} dias.
🩷 Faltam {d_br} dias para o BTS no Brasil!

•°•🌙.•°ATUALIZAÇÕES •°.💫 * . * •°•°🛸

🟣 Weverse {status_color(last_weverse_check)}
🎯 Acessos realizados: {total_weverse}


🟠 Redes sociais {status_color(last_social_check)}
🎯 Acessos realizados: {total_social}


💷 Ticketmaster {status_color(last_ticket_check)}
🎯 Acessos realizados: {total_tickets}


💶 Buyticket {status_color(last_buy_check)}
🎯 Acessos realizados: {total_buy}


•°•👾 Wootteo em rota há: {get_uptime()} ✨
"""


# =========================
# UPDATE PANEL (BLINDADO SEM ALTERAR LAYOUT)
# =========================
panel_lock = asyncio.Lock()
last_panel_update = 0

async def update_panel():

    global panel_message_id, discord_panel_msg_id, last_panel_update

    async with panel_lock:

        try:
            now = time.time()

            # anti-spam leve (não quebra fluxo)
            if (now - last_panel_update) < 5:
                return

            last_panel_update = now

            data_show, city, d_prox, d_br = get_countdown_data()
            texto = gerar_texto_painel(data_show, city, d_prox, d_br)


            # =========================
            # TELEGRAM
            # =========================
            if bot_ticket and PANEL_CHAT_ID:

                try:
                    if panel_message_id:
                        try:
                            await bot_ticket.edit_message_text(
                                chat_id=PANEL_CHAT_ID,
                                message_id=panel_message_id,
                                text=texto
                            )
                            return
                        except:
                            panel_message_id = None

                    msg = await bot_ticket.send_message(
                        chat_id=PANEL_CHAT_ID,
                        text=texto
                    )

                    panel_message_id = msg.message_id

                except Exception as e:
                    print(f"[TELEGRAM PANEL ERROR] {e}")


            # =========================
            # DISCORD
            # =========================
            if DISCORD_PANEL_CHANNEL_ID:

                try:
                    channel = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)

                    if not channel:
                        return

                    embed = discord.Embed(
                        description=texto,
                        color=0x8A2BE2
                    )

                    # tenta editar mensagem existente
                    if discord_panel_msg_id:
                        try:
                            msg = await channel.fetch_message(discord_panel_msg_id)
                            await msg.edit(embed=embed)
                            return
                        except:
                            discord_panel_msg_id = None

                    # cria nova se necessário
                    msg = await channel.send(embed=embed)
                    discord_panel_msg_id = msg.id

                except Exception as e:
                    print(f"[DISCORD PANEL ERROR] {e}")


        except Exception as e:
            print(f"[UPDATE PANEL ERROR] {e}")


# =========================
# DISCORD READY (CORRIGIDO DUPLO EVENTO)
# =========================
@bot_discord.event
async def on_ready():

    print(f"Discord conectado: {bot_discord.user}")

    try:
        await bot_discord.tree.sync()
    except Exception as e:
        print(f"[SYNC ERROR] {e}")

    try:
        await bot_discord.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="🪭 Em tournê - Ouvindo Arirang🪭"
            )
        )
    except Exception as e:
        print(f"[STATUS ERROR] {e}")

# =========================
# 18.1 CHECK FUNCTIONS (VERSÃO REAL + SEGURA - BLINDADA)
# =========================

import aiohttp
from bs4 import BeautifulSoup
import time

# =========================
# SAFE THROTTLE LOCAL
# =========================
LAST_CALL = {}

async def throttle(key, delay=2):

    now = time.time()
    last = LAST_CALL.get(key, 0)

    if now - last < delay:
        await asyncio.sleep(delay - (now - last))

    LAST_CALL[key] = time.time()


# =========================
# SAFE HTML FETCH
# =========================
async def fetch_html(session, url):

    try:
        async with session.get(url, timeout=20) as resp:

            if resp.status != 200:
                return None

            return await resp.text(errors="ignore")

    except Exception as e:
        print(f"[FETCH ERROR] {url} -> {e}")
        return None


# =========================
# SAFE PANEL SYNC (ANTI FLOOD)
# =========================
_last_sync = 0

async def sync_panel():

    global _last_sync

    try:
        now = time.time()

        # 🔒 evita spam no Railway (upgrade importante)
        if now - _last_sync < 2:
            return

        _last_sync = now

        await update_panel()

    except Exception as e:
        print(f"[PANEL SYNC ERROR] {e}")


# =========================
# TICKETMASTER CHECK (BLINDADO)
# =========================
async def check_ticketmaster(session):

    global total_tickets, last_ticket_check

    try:

        for url in TICKET_LINKS:

            await throttle("ticket_" + url, 1)

            html = await fetch_html(session, url)

            if not html:
                continue

            # 🔒 só conta se teve resposta válida
            total_tickets += 1
            last_ticket_check = time.time()

            # evita update direto em loop
            await sync_panel()

            # valida mudança real
            if is_real_change(f"ticket:{url}", html):
                await trigger_alert("ticket", url, None)

    except Exception as e:
        print(f"[CHECK TICKET ERROR] {e}")


# =========================
# BUYTICKET CHECK (BLINDADO)
# =========================
async def check_buyticket(session):

    global total_buy, last_buy_check

    try:

        for url in BUY_LINKS:

            await throttle("buy_" + url, 1)

            html = await fetch_html(session, url)

            if not html:
                continue

            total_buy += 1
            last_buy_check = time.time()

            await sync_panel()

            if is_real_change(f"buy:{url}", html):
                await trigger_alert("buy", url, None)

    except Exception as e:
        print(f"[CHECK BUY ERROR] {e}")


# =========================
# WEVERSE CHECK (BLINDADO)
# =========================
async def check_weverse(session):

    global total_weverse, last_weverse_check

    try:

        for url in WEVERSE_LINKS:

            await throttle("weverse_" + url, 1)

            html = await fetch_html(session, url)

            if not html:
                continue

            total_weverse += 1
            last_weverse_check = time.time()

            await sync_panel()

            if is_real_change(f"weverse:{url}", html):
                await trigger_alert("weverse", url, None)

    except Exception as e:
        print(f"[CHECK WEVERSE ERROR] {e}")


# =========================
# SOCIAL CHECK (BLINDADO + ANTI FLOOD)
# =========================
async def check_social(session):

    global total_social, last_social_check

    try:

        all_links = list(INSTAGRAM_LINKS.values()) + YOUTUBE_LINKS

        for url in all_links:

            await throttle("social_" + url, 3)

            html = await fetch_html(session, url)

            # 🔒 só conta se respondeu algo
            if html:
                total_social += 1
                last_social_check = time.time()

            await sync_panel()

            if not html:
                continue

            if is_real_change(f"social:{url}", html):
                await trigger_alert("social", url, None)

    except Exception as e:
        print(f"[CHECK SOCIAL ERROR] {e}")


# =========================
# ALERT DISPATCH SAFE (DEDUP EXTRA)
# =========================
async def trigger_alert(alert_type, url, message):

    try:

        key = f"{alert_type}:{url}"

        # 🔒 evita dupla chamada por camada externa
        if not is_real_change(key, url):
            return

        await send_alert(alert_type, message or url)

        # sync leve (não força loop pesado)
        await sync_panel()

    except Exception as e:
        print(f"[TRIGGER ERROR] {e}")

# =========================
# 19 FINAL CORE UNIFICADO (PRODUÇÃO ESTÁVEL - BLINDADO)
# =========================

import asyncio
import time
import hashlib
from bs4 import BeautifulSoup

# =========================
# GLOBAL LOCKS (UNIFICADOS)
# =========================

MONITOR_LOCK = asyncio.Lock()
GLOBAL_LOCK = asyncio.Lock()
THROTTLE_LOCK = asyncio.Lock()

# =========================
# CACHE SYSTEM (UNIFICADO)
# =========================

CONTENT_CACHE = {}
ALERT_CACHE = {}
LAST_REQUEST_TIME = {}

# =========================
# SINGLE INSTANCE CONTROL (CRÍTICO RAILWAY)
# =========================

_ENGINE_STARTED = False
_PANEL_STARTED = False

# =========================
# PRIORIDADE DE ALERTAS
# =========================

PRIORITY = {
    "ticket": 3,
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

# =========================
# DETECÇÃO INTELIGENTE DE MUDANÇA
# =========================

def extract_core_signatures(html):

    soup = BeautifulSoup(html or "", "html.parser")

    text = soup.get_text(" ", strip=True)
    links = sorted(set(a.get("href") for a in soup.find_all("a") if a.get("href")))
    images = sorted(set(img.get("src") for img in soup.find_all("img") if img.get("src")))

    return {
        "text": text[:1500],
        "links": links[:30],
        "images": images[:15]
    }


def is_real_change(key, content):

    signature = extract_core_signatures(content)
    new_hash = hashlib.md5(str(signature).encode("utf-8")).hexdigest()

    old = CONTENT_CACHE.get(key)

    if old == new_hash:
        return False

    CONTENT_CACHE[key] = new_hash
    return True

# =========================
# BLOQUEIO DE ALERTA DUPLICADO
# =========================

def is_duplicate_alert(alert_type, message):

    raw = f"{alert_type}:{message}"
    h = hashlib.md5(raw.encode("utf-8")).hexdigest()

    if ALERT_CACHE.get(alert_type) == h:
        return True

    ALERT_CACHE[alert_type] = h
    return False

# =========================
# THROTTLE SEGURO
# =========================

async def throttle(key, delay=2):

    async with THROTTLE_LOCK:

        now = time.time()
        last = LAST_REQUEST_TIME.get(key, 0)

        if now - last < delay:
            await asyncio.sleep(delay - (now - last))

        LAST_REQUEST_TIME[key] = time.time()

# =========================
# PANEL SYNC (SINGLE SOURCE OF TRUTH)
# =========================

_PANEL_SYNC_LOCK = asyncio.Lock()
_last_panel_sync = 0

async def locked_update_panel():

    global _last_panel_sync

    async with _PANEL_SYNC_LOCK:

        now = time.time()

        if now - _last_panel_sync < 2:
            return

        _last_panel_sync = now

        await update_panel()

# =========================
# ALERT ROUTER (UNIFICADO)
# =========================

async def priority_send(alert_type, message, key=None):

    level = PRIORITY.get(alert_type, 1)

    if is_duplicate_alert(alert_type, message):
        return

    if key and not is_real_change(key, message):
        return

    if level == 3:
        await send_alert(alert_type, message)
        await locked_update_panel()
        return

    if level == 2:
        await asyncio.sleep(0.8)
        await send_alert(alert_type, message)
        await locked_update_panel()
        return

    if level == 1:
        await asyncio.sleep(1.5)
        await send_alert(alert_type, message)

# =========================
# ALERT ENTRYPOINT
# =========================

async def trigger_alert(alert_type, url, message):

    key = f"{alert_type}:{url}"
    await priority_send(alert_type, message, key=key)

# =========================
# MONITOR SEGURO
# =========================

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
        print(f"[MONITOR ERROR] {e}")

# =========================
# MONITOR LOOP (SINGLE INSTANCE)
# =========================

async def monitor_loop():

    global _ENGINE_STARTED

    await bot_discord.wait_until_ready()

    if _ENGINE_STARTED:
        return

    _ENGINE_STARTED = True

    print("[MONITOR] RUNNING (SINGLE INSTANCE)")

    async with aiohttp.ClientSession() as session:

        while True:
            await safe_monitor_cycle(session)
            await asyncio.sleep(20)

# =========================
# WATCHDOG
# =========================

async def watchdog():

    await bot_discord.wait_until_ready()

    print("[WATCHDOG] ativo")

    while True:

        await asyncio.sleep(60)

        if not panel_message_id:
            print("[WATCHDOG] painel perdido -> repair")
            await update_panel()

# =========================
# HEALTH WATCHER
# =========================

async def health_watcher():

    await bot_discord.wait_until_ready()

    while True:

        try:
            health = system_health()

            if not health["panel_ok"]:
                print("[HEALTH] repair triggered")
                await auto_repair_panel()

        except Exception as e:
            print(f"[HEALTH ERROR] {e}")

        await asyncio.sleep(60)

# =========================
# ENGINE START (SINGLE INSTANCE)
# =========================

async def start_engine():

    global _ENGINE_STARTED

    if _ENGINE_STARTED:
        return

    _ENGINE_STARTED = True

    print("[ENGINE] FINAL MODE STARTED (UNIFIED PRODUCTION)")

    tasks = [

        asyncio.create_task(monitor_loop()),
        asyncio.create_task(watchdog()),
        asyncio.create_task(health_watcher()),

    ]

    await asyncio.gather(*tasks, return_exceptions=True)

# =========================
# SAFE BOOT (NO OVERWRITE)
# =========================

async def safe_boot():

    async with GLOBAL_LOCK:

        print("[BOOT] iniciando sistema")

        await ensure_single_panel()

        await asyncio.sleep(2)

        print("[BOOT] sistema liberado")

# =========================
# 20 STARTUP FINAL (RAILWAY SAFE / SINGLE INSTANCE)
# =========================

import asyncio

# =========================
# BOOT GUARDS (EVITA DUPLICAÇÃO EM RESTART)
# =========================

_BOOT_LOCK = asyncio.Lock()
_BOOT_STARTED = False
_ENGINE_TASK = None
_TELEGRAM_TASK = None


# =========================
# STARTUP PRINCIPAL
# =========================

async def main():

    global _BOOT_STARTED
    global _ENGINE_TASK
    global _TELEGRAM_TASK

    print("[SYSTEM] Inicializando sistema completo...")

    async with _BOOT_LOCK:

        # 🔒 evita double boot no Railway
        if _BOOT_STARTED:
            print("[SYSTEM] Boot já executado (ignorado)")
            return

        _BOOT_STARTED = True

        try:

            # =========================
            # WEB SERVER
            # =========================
            keep_alive()

            # =========================
            # TELEGRAM (IDEMPOTENTE)
            # =========================
            if _TELEGRAM_TASK is None:
                _TELEGRAM_TASK = asyncio.create_task(start_telegram())

            # =========================
            # ENGINE PRINCIPAL (CONTROLADO)
            # =========================
            if _ENGINE_TASK is None:
                _ENGINE_TASK = asyncio.create_task(start_engine())

            # =========================
            # DISCORD BOT (ENTRYPOINT ÚNICO)
            # =========================
            await bot_discord.start(DISCORD_TOKEN)

        except Exception as e:
            print(f"[SYSTEM ERROR] {e}")


# =========================
# ENTRYPOINT SEGURO
# =========================

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("[SYSTEM] Encerrado manualmente")

    except Exception as e:
        print(f"[SYSTEM CRASH] {e}")

# =========================
# 21 PANEL LOOP (PRODUÇÃO SEGURA – BLINDADO)
# =========================

import asyncio

# =========================
# CONTROLE GLOBAL SEGURO
# =========================
PANEL_LOOP_RUNNING = False
PANEL_LOOP_LOCK = asyncio.Lock()
PANEL_LOOP_TASK = None


# =========================
# PANEL LOOP PRINCIPAL
# =========================
async def panel_loop():

    global PANEL_LOOP_RUNNING

    async with PANEL_LOOP_LOCK:

        # proteção real contra duplicação (async safe)
        if PANEL_LOOP_RUNNING:
            return

        PANEL_LOOP_RUNNING = True

    print("[PANEL LOOP] iniciado")

    try:

        while True:

            try:
                await update_panel()

            except Exception as e:
                print(f"[PANEL LOOP ERROR] {e}")

            await asyncio.sleep(5)

    finally:
        PANEL_LOOP_RUNNING = False
        print("[PANEL LOOP] finalizado")


# =========================
# STARTER CONTROLADO (ANTI DUPLICAÇÃO REAL)
# =========================
async def start_background_tasks():

    global PANEL_LOOP_TASK

    async with PANEL_LOOP_LOCK:

        # impede múltiplas tasks reais
        if PANEL_LOOP_TASK and not PANEL_LOOP_TASK.done():
            return

        PANEL_LOOP_TASK = asyncio.create_task(panel_loop())


# =========================
# DISCORD CONNECT SAFE HOOK (BLINDADO)
# =========================
@bot_discord.event
async def on_connect():

    print("[DISCORD] conectado com segurança")

    # garante apenas 1 execução real
    await start_background_tasks()

# =========================
# 22 BOOT MASTER SAFE (ABSOLUTE MODE)
# =========================

import asyncio
import hashlib

# =========================
# GLOBAL BOOT GUARDS (ANTI DUPLICAÇÃO REAL)
# =========================

BOOT_LOCK = asyncio.Lock()
BOOT_DONE = False

PANEL_BOOT_DONE = False
PANEL_BOOT_LOCK = asyncio.Lock()

BOOT_FINGERPRINT = None
BOOT_FINGERPRINT_LOCK = asyncio.Lock()


# =========================
# FINGERPRINT DO ESTADO (ANTI MULTI INSTANCE)
# =========================

def get_boot_fingerprint():

    raw = f"{DISCORD_PANEL_CHANNEL_ID}:{PANEL_CHAT_ID}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# =========================
# RECOVERY UNIFICADO (TELEGRAM + DISCORD)
# =========================

async def recover_panels():

    global panel_message_id, discord_panel_msg_id

    try:
        channel = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)

        if channel:
            async for msg in channel.history(limit=30):
                if msg.author == bot_discord.user:
                    discord_panel_msg_id = msg.id
                    break

    except Exception as e:
        print(f"[RECOVERY DISCORD ERROR] {e}")

    try:
        saved_id = carregar_id_telegram()

        if saved_id:
            panel_message_id = saved_id

    except Exception as e:
        print(f"[RECOVERY TELEGRAM ERROR] {e}")
        panel_message_id = None


# =========================
# SINGLE PANEL GUARD (IDEMPOTENTE)
# =========================

async def ensure_single_panel():

    global PANEL_BOOT_DONE

    async with PANEL_BOOT_LOCK:

        if PANEL_BOOT_DONE:
            return

        await recover_panels()

        PANEL_BOOT_DONE = True

        print("[BOOT] painel único garantido")


# =========================
# BOOT SEQUENCE FINAL (MASTER SAFE)
# =========================

async def safe_boot():

    global BOOT_DONE, BOOT_FINGERPRINT

    async with BOOT_LOCK:

        if BOOT_DONE:
            return

        current_fp = get_boot_fingerprint()

        async with BOOT_FINGERPRINT_LOCK:

            if BOOT_FINGERPRINT == current_fp:
                return

            BOOT_FINGERPRINT = current_fp

        print("[BOOT] iniciando sequência master...")

        await ensure_single_panel()

        await asyncio.sleep(2)

        BOOT_DONE = True

        print("[BOOT] sistema liberado com segurança total")


# =========================
# DISCORD READY SAFE HOOK
# =========================

@bot_discord.event
async def on_ready():

    print("[DISCORD] ready")

    try:
        await safe_boot()
        await bot_discord.tree.sync()

        await bot_discord.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="🪭 Em tournê - Ouvindo Arirang🪭"
            )
        )

    except Exception as e:
        print(f"[ON_READY ERROR] {e}")


# =========================
# CONNECT SAFE HOOK (IDEMPOTENTE)
# =========================

@bot_discord.event
async def on_connect():

    print("[DISCORD] connect event (safe)")


# =========================
# HEALTH CHECK (SAFE + RAILWAY FRIENDLY)
# =========================

def system_health():

    try:
        return {
            "panel_ok": bool(
                globals().get("panel_message_id") or
                globals().get("discord_panel_msg_id")
            ),
            "boot_done": globals().get("BOOT_DONE", False),
            "panel_loop": globals().get("PANEL_LOOP_RUNNING", False)
        }

    except Exception as e:
        print(f"[HEALTH ERROR] {e}")

        return {
            "panel_ok": False,
            "boot_done": False,
            "panel_loop": False
        }

# =========================
# 23 BOOT SEQUENCE MAP (ORDER CONTROL + ANTI LOOP + RAILWAY SAFE)
# =========================

import asyncio
import time

BOOT_SEQUENCE_READY = False


# =========================
# ESTADO GLOBAL DE EXECUÇÃO
# =========================

ENGINE_STARTED = False
WATCHDOG_STARTED = False
HEALTH_STARTED = False


# =========================
# VERIFICAÇÃO DE CONSISTÊNCIA DO SISTEMA
# =========================

def system_integrity_check():

    try:
        return {
            "boot_done": globals().get("BOOT_DONE", False),
            "panel_ok": bool(
                globals().get("panel_message_id") or
                globals().get("discord_panel_msg_id")
            ),
            "engine": globals().get("ENGINE_STARTED", False),
            "watchdog": globals().get("WATCHDOG_STARTED", False),
            "health": globals().get("HEALTH_STARTED", False)
        }

    except Exception as e:
        print(f"[INTEGRITY ERROR] {e}")

        return {
            "boot_done": False,
            "panel_ok": False,
            "engine": False,
            "watchdog": False,
            "health": False
        }


# =========================
# GATE DE SEGURANÇA (BLOQUEIA EXECUÇÃO PRECOCE)
# =========================

async def wait_system_ready():

    global BOOT_SEQUENCE_READY

    timeout = 60
    start = time.time()

    while True:

        status = system_integrity_check()

        # sistema pronto
        if status["boot_done"] and status["panel_ok"]:
            BOOT_SEQUENCE_READY = True
            print("[BOOT MAP] sistema pronto para engine")
            return True

        # timeout de segurança (evita travar infinito no Railway)
        if time.time() - start > timeout:
            print("[BOOT MAP] timeout de boot, liberando com fallback")
            BOOT_SEQUENCE_READY = True
            return False

        await asyncio.sleep(2)


# =========================
# ENGINE GUARD (ANTI DUPLICAÇÃO)
# =========================

async def start_engine_guard():

    global ENGINE_STARTED

    if ENGINE_STARTED:
        return

    ENGINE_STARTED = True

    print("[BOOT MAP] engine liberado")


# =========================
# WATCHDOG GUARD (ANTI LOOP DUPLO)
# =========================

async def start_watchdog_guard():

    global WATCHDOG_STARTED

    if WATCHDOG_STARTED:
        return

    WATCHDOG_STARTED = True

    print("[BOOT MAP] watchdog liberado")


# =========================
# HEALTH GUARD (ANTI REPAIR LOOP)
# =========================

async def start_health_guard():

    global HEALTH_STARTED

    if HEALTH_STARTED:
        return

    HEALTH_STARTED = True

    print("[BOOT MAP] health monitor liberado")


# =========================
# BOOT MAP ORQUESTRADOR
# =========================

async def boot_sequence_map():

    print("[BOOT MAP] iniciando controle de sequência...")

    # 1. espera sistema estabilizar (boot + panel)
    await wait_system_ready()

    # 2. libera camadas em ordem segura
    await start_engine_guard()
    await start_watchdog_guard()
    await start_health_guard()

    print("[BOOT MAP] todas as camadas liberadas com segurança")

# =========================
# ANTI REPAIR LOOP COOLDOWN (EVITA WATCHDOG SPAM)
# =========================

LAST_REPAIR_TIME = 0
REPAIR_COOLDOWN = 60  # segundos


def can_run_repair():

    global LAST_REPAIR_TIME

    now = time.time()

    if now - LAST_REPAIR_TIME < REPAIR_COOLDOWN:
        return False

    LAST_REPAIR_TIME = now
    return True