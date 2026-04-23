# =========================
# 0 HEALTH CHECK (MUST BE FIRST LEVEL)
# ========================= 
def system_health():
    try:
        return {
            "panel_ok": bool(globals().get("panel_message_id") or globals().get("discord_panel_msg_id")),
            "boot_done": globals().get("PANEL_BOOT_DONE", False),
            "panel_loop": globals().get("PANEL_LOOP_RUNNING", False)
        }
    except Exception as e:
        print(f"[HEALTH ERROR] {e}")
        return {"panel_ok": False, "boot_done": False, "panel_loop": False}

# =========================
# AUTO REPAIR SAFE
# =========================
async def auto_repair_panel():
    try:
        await update_panel()
    except Exception as e:
        print(f"[AUTO REPAIR ERROR] {e}")

# =========================
# 1 BOT WOOTTEO & IMPORTS
# =========================
import asyncio, time, hashlib, os, re, json
from datetime import datetime
from threading import Thread, Lock
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from bs4 import BeautifulSoup
from flask import Flask
from telegram import Bot

# =========================
# 2 CONFIGURAÇÃO E PERSISTÊNCIA
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PANEL_CHAT_ID = -1003920883053
DISCORD_PANEL_CHANNEL_ID = 1494667029150695625

# Arquivos de persistência
COUNTERS_FILE = "counters.json"
PANEL_DATA_FILE = "panel_data.json"
PANEL_BOOT_DONE = False


def load_storage(file, default):
    if os.path.exists(file):
        with open(file, "r") as f: return json.load(f)
    return default

def save_storage(file, data):
    with open(file, "w") as f: json.dump(data, f)

# Carregar dados salvos
stored_counters = load_storage(COUNTERS_FILE, {"tickets": 0, "weverse": 0, "social": 0, "buy": 0})
stored_panel = load_storage(PANEL_DATA_FILE, {"tg_msg_id": None, "dc_msg_id": None})

# Variáveis globais sincronizadas
total_tickets = stored_counters["tickets"]
total_weverse = stored_counters["weverse"]
total_social = stored_counters["social"]
panel_message_id = stored_panel["tg_msg_id"] # ID do Telegram
discord_panel_msg_id = stored_panel["dc_msg_id"] # ID do Discord

# Bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot_discord = commands.Bot(command_prefix="!", intents=intents)

@bot_discord.event
async def setup_hook():
    try:
        await bot_discord.tree.sync()
        print("[SYNC] Slash commands sincronizados")
    except Exception as e: print(f"[SYNC ERROR] {e}")

# =========================
# 2.1 TELEGRAM START
# =========================
bot_ticket = Bot(token=TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

async def start_telegram():
    if bot_ticket:
        print("[TELEGRAM] pronto (Modo Legacy)")

# =========================
# 3 CONTROLE DE CONTADORES (FIX SINCRONIA)
# =========================
COUNTER_LOCK = asyncio.Lock()

async def save_counters():
    """Salva os contadores no disco para evitar perda de dados."""
    try:
        # [FIX] Adicionado o fechamento do dicionário } e do parênteses
        data = {
            "tickets": total_tickets, 
            "weverse": total_weverse, 
            "social": total_social
        }
        save_storage(COUNTERS_FILE, data)
    except Exception as e:
        print(f"[SAVE ERROR] {e}")

async def increment_ticket():
    global total_tickets
    async with COUNTER_LOCK:
        total_tickets += 1
        await save_counters()
        return total_tickets

async def increment_weverse():
    global total_weverse
    async with COUNTER_LOCK:
        total_weverse += 1
        await save_counters()
        return total_weverse

async def increment_social():
    global total_social
    async with COUNTER_LOCK:
        total_social += 1
        await save_counters()
        return total_social

# =========================
# 4 WEB SERVER (KEEP ALIVE)
# =========================
app_web = Flask(__name__)
start_time = time.time()

@app_web.route("/")
def home(): return {"status": "online", "uptime": int(time.time() - start_time)}

_web_started = False
def run_web():
    app_web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False, use_reloader=False)

def keep_alive():
    global _web_started
    if not _web_started:
        _web_started = True
        Thread(target=run_web, daemon=True).start()

# =========================
# 5 ANTI-SPAM E HASH (PERSISTENTE)
# =========================
CONTENT_HASH = load_storage("content_hash_cache.json", {})
CONTENT_LOCK = asyncio.Lock()

def normalize_html(html):
    if not html: return ""
    return " ".join(BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True).split())

async def is_new(url, html):
    global CONTENT_HASH
    new_hash = hashlib.md5(normalize_html(html).encode("utf-8")).hexdigest()
    async with CONTENT_LOCK:
        if CONTENT_HASH.get(url) != new_hash:
            CONTENT_HASH[url] = new_hash
            save_storage("content_hash_cache.json", CONTENT_HASH)
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

def get_uptime():
    try:
        s = int(time.time() - start_time)
        return f"{s//3600}h {(s%3600)//60}m {s%60}s"
    except: return "0h 0m 0s"

def resolve_status(last_check_time):
    try:
        diff = time.time() - last_check_time
        if diff > 1800: return "🔴"
        return "🟡" if diff > 600 else "🟢"
    except: return "🔴"

def clean(v): return v if v and str(v).strip() else "ESGOTADO"

def days_left(date_str):
    try:
        target = datetime.strptime(date_str, "%d/%m/%Y").date()
        return max((target - datetime.now().date()).days, 0)
    except: return 0

def minutes_since(ts):
    try: return int((time.time() - ts) / 60)
    except: return 0

def get_countdown_data():
    now_dt = datetime.now()
    prox_data, prox_local, d_prox, d_br = "Continua…", "---", 0, 0
    if not isinstance(globals().get("AGENDA"), list): return prox_data, prox_local, d_prox, d_br
    for item in AGENDA:
        try:
            show_dt = datetime.strptime(f"{item[0]} {item[3]}", "%d/%m/%Y %H:%M")
            if show_dt > now_dt and prox_data == "Continua…":
                prox_data, prox_local = item[0], f"{item[1]}, {item[2]}"
                d_prox = (show_dt.date() - now_dt.date()).days
            if "Brasil" in str(item[2]) and d_br == 0:
                br_date = datetime.strptime(item[0], "%d/%m/%Y").date()
                if br_date >= now_dt.date(): d_br = (br_date - now_dt.date()).days
        except: continue
    return prox_data, prox_local, d_prox, d_br

# =========================
# 9 SESSION HTTP
# =========================
http_session = None
_session_lock = asyncio.Lock()

async def get_session():
    global http_session
    async with _session_lock:
        if http_session is None or http_session.closed:
            http_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": "Mozilla/5.0"})
    return http_session

async def fetch(url, retries=2):
    for attempt in range(retries + 1):
        try:
            session = await get_session()
            async with session.get(url) as resp:
                if resp.status == 200: return await resp.text()
        except: await asyncio.sleep(1)
    return None

# =========================
# 10 EMOJIS & FORMATTER
# =========================
MEMBER_EMOJI = {"rm":"🐨","jin":"🐹","suga":"🐱","jhope":"🐿️","jimin":"🐥","v":"🐻","jungkook":"🐰","bts":"💜","wootteo":"🛸"}

def get_member_emoji(name):
    return MEMBER_EMOJI.get(re.sub(r"[^a-z0-9]", "", str(name).lower()), "💜")

def format_member(name):
    emoji = get_member_emoji(name)
    return {"emoji": emoji, "name": str(name).upper(), "display": f"{emoji} {name.upper()}"}

# =========================
# 11 CORE ROUTER (FIX CONTADORES)
# =========================
async def send_alert(alert_type, message):
    try:
        # Incremento automático baseado no tipo de alerta
        if "ticket" in alert_type: await increment_ticket()
        elif "weverse" in alert_type: await increment_weverse()
        elif any(x in alert_type for x in ["instagram", "tiktok", "youtube"]): await increment_social()

        if bot_ticket: await bot_ticket.send_message(chat_id=PANEL_CHAT_ID, text=message)
        
        discord_map = {
            "ticket": DISCORD_TICKETS_CHANNEL_ID, "weverse_post": DISCORD_WEVERSE_CHANNEL_ID,
            "instagram_post": DISCORD_SOCIAL_CHANNEL_ID, "tiktok_post": DISCORD_SOCIAL_CHANNEL_ID
        }
        cid = discord_map.get(alert_type) or DISCORD_SOCIAL_CHANNEL_ID
        ch = bot_discord.get_channel(cid) or await bot_discord.fetch_channel(cid)
        if ch: await ch.send(embed=discord.Embed(description=message, color=0x8A2BE2))
    except Exception as e: print(f"[ALERT ERROR] {e}")

# =========================
# 12 PAINEL (FIX OBRIGATÓRIO ANTI-DUPLICAÇÃO)
# =========================
panel_lock = asyncio.Lock()

async def update_panel():
    global panel_message_id, discord_panel_msg_id
    async with panel_lock:
        try:
            data_show, city, d_prox, d_br = get_countdown_data()
            texto = gerar_texto_painel(data_show, city, d_prox, d_br)
            
            # --- TELEGRAM (EDIT OU POST) ---
            if bot_ticket:
                try:
                    if panel_message_id:
                        await bot_ticket.edit_message_text(chat_id=PANEL_CHAT_ID, message_id=panel_message_id, text=texto)
                    else:
                        msg = await bot_ticket.send_message(chat_id=PANEL_CHAT_ID, text=texto)
                        panel_message_id = msg.message_id
                        await bot_ticket.pin_chat_message(chat_id=PANEL_CHAT_ID, message_id=panel_message_id)
                        save_storage(PANEL_DATA_FILE, {"tg_msg_id": panel_message_id, "dc_msg_id": discord_panel_msg_id})
                except: panel_message_id = None

            # --- DISCORD (EDIT OU POST) ---
            ch = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID) or await bot_discord.fetch_channel(DISCORD_PANEL_CHANNEL_ID)
            if ch:
                embed = discord.Embed(description=texto, color=0x8A2BE2)
                if discord_panel_msg_id:
                    try:
                        m = await ch.fetch_message(discord_panel_msg_id)
                        await m.edit(embed=embed)
                    except: discord_panel_msg_id = None
                
                if not discord_panel_msg_id:
                    msg = await ch.send(embed=embed)
                    discord_panel_msg_id = msg.id
                    await msg.pin()
                    save_storage(PANEL_DATA_FILE, {"tg_msg_id": panel_message_id, "dc_msg_id": discord_panel_msg_id})
        except Exception as e: print(f"[PANEL ERROR] {e}")

# =========================
# 12.1 RECOVERY (OBRIGATÓRIO)
# =========================
async def ensure_single_panel():
    global PANEL_BOOT_DONE, panel_message_id, discord_panel_msg_id
    if PANEL_BOOT_DONE: return
    
    data = load_storage(PANEL_DATA_FILE, {"tg_msg_id": None, "dc_msg_id": None})
    panel_message_id = data.get("tg_msg_id")
    discord_panel_msg_id = data.get("dc_msg_id")
    
    PANEL_BOOT_DONE = True
    print(f"[RECOVERY] IDs carregados: TG={panel_message_id} DC={discord_panel_msg_id}")

# =========================
# 13 SISTEMA DE PERSISTÊNCIA & WEVERSE ALERTS
# =========================

import hashlib
import asyncio
import json
import os
import time  # [FIX] Import necessário para o time.time()

# =========================
# INICIALIZAÇÃO DE GLOBAIS (ANTI-ERROR)
# =========================
PANEL_BOOT_DONE = globals().get("PANEL_BOOT_DONE", False)
COUNTERS_FILE = "counters_state.json"
WEVERSE_CACHE = {}
WEVERSE_LOCK = asyncio.Lock()

# =========================
# SISTEMA DE DISCO (RAILWAY SAFE)
# =========================

async def save_counters():
    """Salva os totais de acessos e timestamps no disco da Railway."""
    try:
        data = {
            "total_weverse": globals().get("total_weverse", 0),
            "total_social": globals().get("total_social", 0),
            "total_tickets": globals().get("total_tickets", 0),
            "last_weverse_check": globals().get("last_weverse_check", 0),
            "last_social_check": globals().get("last_social_check", 0),
            "last_ticket_check": globals().get("last_ticket_check", 0)
        }
        with open(COUNTERS_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[SAVE ERROR] Falha ao salvar contadores: {e}")

async def load_counters():
    """Carrega os dados salvos para as globais no início do bot."""
    if os.path.exists(COUNTERS_FILE):
        try:
            with open(COUNTERS_FILE, 'r') as f:
                data = json.load(f)
            
            globals()["total_weverse"] = data.get("total_weverse", 0)
            globals()["total_social"] = data.get("total_social", 0)
            globals()["total_tickets"] = data.get("total_tickets", 0)
            globals()["last_weverse_check"] = data.get("last_weverse_check", 0)
            globals()["last_social_check"] = data.get("last_social_check", 0)
            globals()["last_ticket_check"] = data.get("last_ticket_check", 0)
            
            print("[SYSTEM] Contadores restaurados do disco.")
        except Exception as e:
            print(f"[LOAD ERROR] Falha ao carregar contadores: {e}")
    else:
        print("[SYSTEM] Nenhum arquivo de contadores prévio encontrado.")

# =========================
# LOGICA DE DUPLICAÇÃO
# =========================

def is_new_weverse_event(event_type, url, content=""):
    """Evita duplicação usando hash do conteúdo."""
    raw = f"{event_type}:{url}:{content}"
    new_hash = hashlib.md5(raw.encode("utf-8")).hexdigest()

    if WEVERSE_CACHE.get(event_type) == new_hash:
        return False

    WEVERSE_CACHE[event_type] = new_hash
    return True

# =========================
# FUNÇÕES DE ALERTA (WEVERSE)
# =========================

async def weverse_post(url, member_name, title, message_translated, found):
    async with WEVERSE_LOCK:
        if not is_new_weverse_event("post", url, title + message_translated):
            return

        globals()["total_weverse"] = globals().get("total_weverse", 0) + 1
        globals()["last_weverse_check"] = time.time()
        await save_counters() 

        emoji = get_member_emoji(member_name)
        msg = f"""🩷 WEVERSE POST 🩷
{emoji} {member_name.upper()} fez uma publicação 
📌 {title}
📝 {message_translated}
🔗 {url}"""

        await send_alert("weverse_post", msg)
        await update_panel()

async def weverse_live(url, member_name, found):
    async with WEVERSE_LOCK:
        if not is_new_weverse_event("live", url):
            return

        globals()["total_weverse"] = globals().get("total_weverse", 0) + 1
        globals()["last_weverse_check"] = time.time()
        await save_counters()

        emoji = get_member_emoji(member_name)
        msg = f"""📹 WEVERSE LIVE 📹
{emoji} {member_name.upper()} está ao vivo
🔗 {url}"""

        await send_alert("weverse_live", msg)
        await update_panel()

async def weverse_news(url, member_name, message_translated, found):
    async with WEVERSE_LOCK:
        if not is_new_weverse_event("news", url, message_translated):
            return

        globals()["total_weverse"] = globals().get("total_weverse", 0) + 1
        globals()["last_weverse_check"] = time.time()
        await save_counters()

        emoji = get_member_emoji(member_name)
        msg = f"""🚨 WEVERSE NEWS 🚨
{emoji} {member_name.upper()} fez uma publicação 
📝 {message_translated}
🔗 {url}"""

        await send_alert("weverse_news", msg)
        await update_panel()

async def weverse_media(url, member_name, title, message_translated, found):
    async with WEVERSE_LOCK:
        if not is_new_weverse_event("media", url, title + message_translated):
            return

        globals()["total_weverse"] = globals().get("total_weverse", 0) + 1
        globals()["last_weverse_check"] = time.time()
        await save_counters()

        emoji = get_member_emoji(member_name)
        msg = f"""📀 WEVERSE MEDIA 📀
{emoji} {member_name.upper()} fez uma publicação 
⭐ {title}
📝 {message_translated}
🔗 {url}"""

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
        await save_counters()

        # FIX: format_member retorna dict, acessando chaves corretamente
        m_data = format_member(member_name)
        emoji = m_data["emoji"]
        name = m_data["name"]

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
        await save_counters()

        m_data = format_member(member_name)
        emoji = m_data["emoji"]
        name = m_data["name"]

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
        await save_counters()

        m_data = format_member(member_name)
        emoji = m_data["emoji"]
        name = m_data["name"]

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
        await save_counters()

        m_data = format_member(member_name)
        emoji = m_data["emoji"]
        name = m_data["name"]

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

        # FIX: Incremento e persistência
        global total_social, last_social_check
        total_social += 1
        last_social_check = time.time()
        await save_counters()

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

        global total_social, last_social_check
        total_social += 1
        last_social_check = time.time()
        await save_counters()

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

        global total_social, last_social_check
        total_social += 1
        last_social_check = time.time()
        await save_counters()

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

        global total_social, last_social_check
        total_social += 1
        last_social_check = time.time()
        await save_counters()

        live_url = "https://www.youtube.com/@BTS/live"

        msg = f"""

📹 YOUTUBE LIVE 📹
🚨 BTS está ao vivo agora
🔗 {live_url}

"""

        await send_alert("youtube_live", msg)
        await update_panel()

# =========================
# 15.1 TICKETMASTER (PRODUÇÃO SEGURA)
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

    # FIX: Incremento e persistência
    total_tickets += 1
    last_ticket_check = time.time()
    await save_counters()

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

    # FIX: Incremento e persistência
    total_tickets += 1
    last_ticket_check = time.time()
    await save_counters()

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

    # TEST MODE: apenas log (Não incrementa contadores reais)
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

    # Em produção, usa a lógica de EDIT vs SEND protegida no Bloco 12
    await update_panel()


# =========================
# RUN TEST DISCORD (BATERIA COMPLETA)
# =========================
async def run_full_test_discord():

    print("[TESTE DC] iniciando bateria completa...")

    try:

        # =========================
        # TICKET
        # =========================
        await test_ticket_reposicao()
        await test_ticket_agenda()
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
# TICKET TESTS
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
# 17 COMMAND ENGINE FRAMEWORK FINAL (CORREÇÃO DE CANAL)
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
# SENDER UNIFICADO (GARANTE O DESTINO)
# =========================
async def send(ctx, text):
    if ctx.is_discord and ctx.interaction:
        try:
            if ctx.interaction.response.is_done():
                await ctx.interaction.followup.send(text)
            else:
                await ctx.interaction.response.send_message(text)
        except Exception as e:
            print(f"[DISCORD SEND ERROR] {e}")

    elif ctx.is_telegram and ctx.chat_id:
        try:
            await bot_ticket.send_message(chat_id=ctx.chat_id, text=text)
        except Exception as e:
            print(f"[TELEGRAM SEND ERROR] {e}")

# =========================
# DEFINIÇÃO DOS COMANDOS (PROIBIDO ALTERAR PING, BTS, COMANDOS)
# =========================

@command("ping")
async def ping(ctx):
    await send(ctx, f"🏓 Pong! {get_uptime()}")

@command("comandos")
async def comandos(ctx):
    await send(ctx, "/ping\n/comandos\n/teste\n/bts")

@command("bts")
async def bts(ctx):
    membros = ["🐨 KIM NAMJOON", "🐹 KIM SEOKJIN", "🐱 MIN YOONGI", "🐿️ JUNG HOSEOK", "🐥 PARK JIMIN", "🐻 KIM TAEHYUNG", "🐰 JEON JUNGKOOK", "💜 BTS"]
    if ctx.is_discord and ctx.interaction:
        await ctx.interaction.response.send_message(membros[0])
        for m in membros[1:]:
            await asyncio.sleep(1.2)
            await ctx.interaction.channel.send(m)
        await asyncio.sleep(1.2)
        await ctx.interaction.channel.send("🪭Ouça Arirang no Spotify🪭\nhttps://open.spotify.com/intl-pt/album/3ukkRHDHbN8tNRPKsGZR1h")
        return
    await send(ctx, "\n".join(membros) + "\n\n🪭Ouça Arirang no Spotify🪭")

# =========================
# /TESTE (VERSÃO DISCORD-ONLY)
# =========================
@command("teste")
async def teste(ctx):
    await send(ctx, "⚠️ Verificando integridade e disparando alertas no Discord...")
    
    if ctx.is_discord:
        try:
            # 1. DISPARA ALERTAS NOS CANAIS DO DISCORD
            # Chamamos a função de reparo/alerta garantindo que ela não use o Telegram
            if "repair_loop" in globals() or "trigger_alert" in globals():
                # Aqui você chama a função que envia as embeds para as salas do Discord
                # Se 'run_full_test_discord' for essencial, vamos chamá-la mas silenciando erros de Telegram
                await run_full_test_discord() 
            
            uptime = get_uptime()
            await send(ctx, f"✅ Alertas enviados para as salas do Discord.\n✅ Uptime: {uptime}\n✅ Painel: Sincronizado")
            
            # 2. ATUALIZA O PAINEL VISUAL
            await update_panel()
            
        except Exception as e:
            await send(ctx, f"❌ Erro ao disparar alertas: {e}")
    else:
        # Lógica para Telegram (permanece igual)
        try:
            await run_full_test_discord()
            await send(ctx, "✅ Teste Telegram concluído.")
        except:
            await send(ctx, "❌ Falha no teste Telegram.")


# =========================
# PONTES E REGISTROS (BLOQUEADOS)
# =========================
async def executar_discord(cmd, interaction):
    ctx = CommandContext(origin="discord", interaction=interaction)
    await execute_command(cmd, ctx)

async def executar_telegram(update, context):
    if not update.message or not update.message.text: return
    text = update.message.text.strip().lower()
    if not text.startswith("/"): return
    cmd = text.replace("/", "").split("@")[0]
    ctx = CommandContext(origin="telegram", chat_id=update.message.chat_id)
    await execute_command(cmd, ctx)

@bot_discord.tree.command(name="ping", description="Verifica latência")
async def slash_ping(interaction: discord.Interaction):
    await executar_discord("ping", interaction)

@bot_discord.tree.command(name="bts", description="Lista os membros do BTS")
async def slash_bts(interaction: discord.Interaction):
    await executar_discord("bts", interaction)

@bot_discord.tree.command(name="teste", description="Executa o teste de monitoramento")
async def slash_teste(interaction: discord.Interaction):
    await executar_discord("teste", interaction)

@bot_discord.tree.command(name="comandos", description="Mostra lista de comandos")
async def slash_comandos(interaction: discord.Interaction):
    await executar_discord("comandos", interaction)

# =========================
# 18.0 APOIO: CORES DINÂMICAS (PULSO VERDE)
# =========================
def status_color(last_check_time, tipo):
    # Se estiver a verificar agora, mostra VERDE (Efeito de piscar/atividade)
    if globals().get(f"is_checking_{tipo}", False):
        return "🟢"
    
    if not last_check_time or last_check_time == 0:
        return "🔴"
        
    elapsed = time.time() - last_check_time
    if elapsed < 600: return "🟣" # Online e Ativo
    elif elapsed < 1800: return "🟡" # Em espera
    else: return "🔴"

def get_countdown_data():
    now_dt = datetime.now()
    next_global_date, next_global_local = "Continua…", "---"
    days_to_next_global, days_to_brazil = 0, 0
    agenda_data = globals().get("AGENDA", [])
    
    for item in agenda_data:
        try:
            show_dt = datetime.strptime(f"{item[0]} {item[3]}", "%d/%m/%Y %H:%M")
            if show_dt > now_dt:
                next_global_date, next_global_local = item[0], f"{item[1]}, {item[2]}"
                days_to_next_global = (show_dt.date() - now_dt.date()).days
                break
        except: continue
    for item in agenda_data:
        try:
            if "Brasil" in item[2]:
                br_date = datetime.strptime(item[0], "%d/%m/%Y").date()
                if br_date >= now_dt.date():
                    days_to_brazil = (br_date - now_dt.date()).days
                    break
        except: continue
    return next_global_date, next_global_local, days_to_next_global, days_to_brazil

# =========================
# 18.1 GERAÇÃO DE TEXTO (STATUS ATUALIZADO)
# =========================
def gerar_texto_painel(data_show, city, d_prox, d_br):
    lwc = globals().get("last_weverse_check", 0)
    lsc = globals().get("last_social_check", 0)
    ltc = globals().get("last_ticket_check", 0)
    tw = globals().get("total_weverse", 0)
    ts = globals().get("total_social", 0)
    tt = globals().get("total_tickets", 0)
    uptime = get_uptime()

    return f"""🪭 ⊙⊝⊜ ARIRANG TOUR ⊙⊝⊜ 🪭

✈️ PRÓXIMAS DATAS

🎫 Data: {data_show}
📍 Local: {city}
🔔 Faltam {d_prox} dias.
🩷 Faltam {d_br} dias para o BTS no Brasil!

•°•🌙.•°ATUALIZAÇÕES •°.💫 * . * •°•°🛸

🟣 Weverse {status_color(lwc, "weverse")}
🎯 Acessos realizados: {tw}

🟠 Redes sociais {status_color(lsc, "social")}
🎯 Acessos realizados: {ts}

💷 Ticketmaster {status_color(ltc, "ticket")}
🎯 Acessos realizados: {tt}

•°•👾 Wootteo em rota há: {uptime} ✨"""

# =========================
# 18.2 SINCRONIZAÇÃO E EVENTO ON_READY
# =========================
panel_lock = asyncio.Lock()
last_panel_update = 0

async def update_panel():
    global panel_message_id, discord_panel_msg_id, last_panel_update
    async with panel_lock:
        try:
            now = time.time()
            if (now - last_panel_update) < 3: return # Reduzi para 3s para o pulso ser mais rápido
            last_panel_update = now
            d_show, city, d_prox, d_br = get_countdown_data()
            texto = gerar_texto_painel(d_show, city, d_prox, d_br)

            if bot_ticket and PANEL_CHAT_ID:
                try:
                    if panel_message_id:
                        try: await bot_ticket.edit_message_text(chat_id=PANEL_CHAT_ID, message_id=panel_message_id, text=texto)
                        except: panel_message_id = None
                    if not panel_message_id:
                        m = await bot_ticket.send_message(chat_id=PANEL_CHAT_ID, text=texto)
                        panel_message_id = m.message_id
                        try: await bot_ticket.pin_chat_message(PANEL_CHAT_ID, panel_message_id)
                        except: pass
                except: pass

            if DISCORD_PANEL_CHANNEL_ID:
                try:
                    chan = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)
                    if not chan: chan = await bot_discord.fetch_channel(DISCORD_PANEL_CHANNEL_ID)
                    if chan:
                        emb = discord.Embed(description=texto, color=0x8A2BE2)
                        if discord_panel_msg_id:
                            try:
                                m = await chan.fetch_message(discord_panel_msg_id)
                                await m.edit(embed=emb)
                            except: discord_panel_msg_id = None
                        if not discord_panel_msg_id:
                            m = await chan.send(embed=emb)
                            discord_panel_msg_id = m.id
                            try: await m.pin()
                            except: pass
                    save_storage(PANEL_DATA_FILE, {"tg_msg_id": panel_message_id, "dc_msg_id": discord_panel_msg_id})
                except: pass
        except Exception as e: print(f"[PANEL ERR] {e}")

@bot_discord.event
async def on_ready():
    # 1. FORÇAR FRASE DE STATUS (Sempre)
    act = discord.Activity(type=discord.ActivityType.listening, name="🪭 Em tournê - Ouvindo Arirang🪭")
    await bot_discord.change_presence(status=discord.Status.online, activity=act)

    # 2. FORÇAR SYNC DE COMANDOS (Para o Bloco 17 aparecer)
    try:
        await bot_discord.tree.sync()
        print(f"[SYNC] Comandos atualizados para {bot_discord.user}")
    except Exception as e: print(f"[SYNC ERROR] {e}")

    # 3. TRAVA DE BOOT ÚNICO
    if globals().get("PANEL_BOOT_DONE", False): return
    print(f"DISCORD CONECTADO: {bot_discord.user}")

    try:
        await ensure_single_panel()
        await update_panel()
        globals()["PANEL_BOOT_DONE"] = True
    except Exception as e: print(f"[INIT ERROR] {e}")

# =========================
# 18.3 MONITORAMENTO (CHECKERS COM PULSO VERDE)
# =========================
async def check_ticketmaster(session):
    try:
        globals()["is_checking_ticket"] = True
        await update_panel()
        for url in TICKET_LINKS:
            await throttle("ticket_" + url, 1)
            html = await fetch_html(session, url)
            if not html: continue
            globals()["total_tickets"] = globals().get("total_tickets", 0) + 1
            globals()["last_ticket_check"] = time.time()
            await save_counters()
        globals()["is_checking_ticket"] = False
        await update_panel()
    except: globals()["is_checking_ticket"] = False

async def check_weverse(session):
    try:
        globals()["is_checking_weverse"] = True
        await update_panel()
        for url in WEVERSE_LINKS:
            await throttle("weverse_" + url, 1)
            html = await fetch_html(session, url)
            if not html: continue
            globals()["total_weverse"] = globals().get("total_weverse", 0) + 1
            globals()["last_weverse_check"] = time.time()
            await save_counters()
        globals()["is_checking_weverse"] = False
        await update_panel()
    except: globals()["is_checking_weverse"] = False

async def check_social(session):
    try:
        globals()["is_checking_social"] = True
        await update_panel()
        all_links = list(INSTAGRAM_LINKS.values()) + YOUTUBE_LINKS
        for url in all_links:
            await throttle("social_" + url, 3)
            html = await fetch_html(session, url)
            if html:
                globals()["total_social"] = globals().get("total_social", 0) + 1
                globals()["last_social_check"] = time.time()
                await save_counters()
        globals()["is_checking_social"] = False
        await update_panel()
    except: globals()["is_checking_social"] = False

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
        "links": links[:60],
        "images": images[:60]
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

        # [FIX] Respeita o cooldown mas garante que o estado final seja salvo
        if now - _last_panel_sync < 2:
            return

        _last_panel_sync = now

        # [FIX] Garante que contadores e IDs de mensagem estejam em disco antes do update visual
        await save_counters()
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
        # Sincronia imediata para eventos críticos
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
        # Nível 1 não força update de painel para economizar API

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
        # [FIX] Cada check agora salva contadores internamente (Bloco 18)
        await throttle("ticket", 1)
        await check_ticketmaster(session)

        await throttle("weverse", 1)
        await check_weverse(session)

        await throttle("social", 1)
        await check_social(session)

        # Update final do ciclo para garantir paridade
        await locked_update_panel()

    except Exception as e:
        print(f"[MONITOR ERROR] {e}")

# =========================
# MONITOR LOOP (SINGLE INSTANCE)
# =========================

async def monitor_loop():

    global _ENGINE_STARTED

    await bot_discord.wait_until_ready()

    # Prevenção de race condition no boot
    if _ENGINE_STARTED:
        return

    _ENGINE_STARTED = True

    print("[MONITOR] RUNNING (SINGLE INSTANCE)")

    # [FIX] Reaproveitamento de sessão para evitar overhead de handshake
    async with aiohttp.ClientSession() as session:

        while True:
            await safe_monitor_cycle(session)
            # Sleep balanceado para não ser banido pelos servidores (Weverse/IG)
            await asyncio.sleep(20)

# =========================
# WATCHDOG
# =========================

async def watchdog():

    await bot_discord.wait_until_ready()

    print("[WATCHDOG] ativo")

    while True:

        await asyncio.sleep(60)

        # [FIX] Recuperação automática se o ID sumir da memória
        if not globals().get("panel_message_id") or not globals().get("discord_panel_msg_id"):
            print("[WATCHDOG] painel perdido ou IDs desincronizados -> reparando via disco")
            await ensure_single_panel()
            await update_panel()

# =========================
# HEALTH WATCHER
# =========================

async def health_watcher():

    await bot_discord.wait_until_ready()

    while True:

        try:
            # system_health() deve retornar um dicionário com o estado dos serviços
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

    # A trava global impede que tasks duplicadas rodem após reconexões
    if globals().get("_ENGINE_TASKS_STARTED", False):
        return

    globals()["_ENGINE_TASKS_STARTED"] = True

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

        # [FIX] Carregamento obrigatório de estado persistente antes de ligar motores
        await ensure_single_panel()
        await load_counters()

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
            # Carrega contadores e IDs persistentes antes de qualquer outra coisa
            await load_counters()
            await ensure_single_panel()

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
                # O start_engine já contém monitor_loop, watchdog e health_watcher
                _ENGINE_TASK = asyncio.create_task(start_engine())

            # =========================
            # DISCORD BOT (ENTRYPOINT ÚNICO)
            # =========================
            # O start() bloqueia a execução, então deve ser o último
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
                # FIX: Garante que os contadores salvos no disco reflitam no painel
                await update_panel()

            except Exception as e:
                print(f"[PANEL LOOP ERROR] {e}")

            # Intervalo de 20s para evitar rate-limit agressivo
            await asyncio.sleep(20)

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

    # Prioridade 1: Recuperar do Arquivo (Mais seguro contra resets)
    ids_disco = carregar_storage(PANEL_DATA_FILE)
    if ids_disco:
        panel_message_id = ids_disco.get("tg_msg_id", panel_message_id)
        discord_panel_msg_id = ids_disco.get("dc_msg_id", discord_panel_msg_id)

    # Prioridade 2: Busca ativa no histórico do Discord se o disco falhar
    if not discord_panel_msg_id:
        try:
            channel = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)
            if not channel: channel = await bot_discord.fetch_channel(DISCORD_PANEL_CHANNEL_ID)
            
            if channel:
                async for msg in channel.history(limit=30):
                    if msg.author == bot_discord.user and "ARIRANG TOUR" in (msg.content or ""):
                        discord_panel_msg_id = msg.id
                        break
        except Exception as e:
            print(f"[RECOVERY DISCORD ERROR] {e}")


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
        await asyncio.sleep(1)

        BOOT_DONE = True

        print("[BOOT] sistema liberado com segurança total")

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
        # Puxa os estados reais definidos nos blocos de BOOT e ENGINE
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

        # sistema pronto (Boot concluído e pelo menos um painel localizado)
        if status["boot_done"] and status["panel_ok"]:
            BOOT_SEQUENCE_READY = True
            print("[BOOT MAP] sistema pronto para engine")
            return True

        # timeout de segurança (evita travar infinito no Railway se as APIs demorarem)
        if time.time() - start > timeout:
            print("[BOOT MAP] timeout de boot, liberando com fallback para evitar travamento")
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

    # FIX: Aciona a inicialização real da engine se ainda não subiu
    if not globals().get("_ENGINE_TASKS_STARTED", False):
        asyncio.create_task(start_engine())

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

    # 1. espera sistema estabilizar (carregamento de disco + recovery de painel)
    await wait_system_ready()

    # 2. libera camadas em ordem segura para evitar race conditions
    await start_engine_guard()
    await start_watchdog_guard()
    await start_health_guard()

    print("[BOOT MAP] todas as camadas liberadas com segurança")

# =========================
# ANTI REPAIR LOOP COOLDOWN (EVITA WATCHDOG SPAM)
# =========================

LAST_REPAIR_TIME = 0
REPAIR_COOLDOWN = 60  # segundos (Janela de segurança contra flood)


def can_run_repair():

    global LAST_REPAIR_TIME

    now = time.time()

    if now - LAST_REPAIR_TIME < REPAIR_COOLDOWN:
        return False

    LAST_REPAIR_TIME = now
    return True
