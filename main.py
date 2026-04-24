# =========================
# 0 HEALTH CHECK  
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

# AUTO REPAIR SAFE #
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
import os
import json
import discord
from discord.ext import commands
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PANEL_CHAT_ID = -1003972186058
DISCORD_PANEL_CHANNEL_ID = 1494667029150695625

# IDs específicos para roteamento de alertas
DISCORD_TICKETS_CHANNEL_ID = 1494670074374651985
DISCORD_WEVERSE_CHANNEL_ID = 1494680233025208461
DISCORD_SOCIAL_CHANNEL_ID = 1494682078950981864

# Arquivos de persistência
COUNTERS_FILE = "counters.json"
PANEL_DATA_FILE = "panel_data.json"
PANEL_BOOT_DONE = False

def load_storage(file, default):
    """Carrega o JSON de forma segura"""
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[MEMÓRIA] Erro ao ler {file}: {e}")
            return default
    return default

def save_storage(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# --- CARREGAMENTO BLINDADO ---
# Usamos chaves que batem com o que o Bloco 18 salva
default_counters = {
    "total_tickets": 0, 
    "total_weverse": 0, 
    "total_social": 0, 
    "total_buy": 0
}
stored_counters = load_storage(COUNTERS_FILE, default_counters)
stored_panel = load_storage(PANEL_DATA_FILE, {"tg_msg_id": None, "dc_msg_id": None})

# Variáveis globais sincronizadas (Usando .get para evitar KeyError)
total_tickets = stored_counters.get("total_tickets", 0)
total_weverse = stored_counters.get("total_weverse", 0)
total_social = stored_counters.get("total_social", 0)

panel_message_id = stored_panel.get("tg_msg_id")
discord_panel_msg_id = stored_panel.get("dc_msg_id")

# --- CONFIGURAÇÃO DO BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot_discord = commands.Bot(command_prefix="!", intents=intents)

@bot_discord.event
async def setup_hook():
    try:
        await bot_discord.tree.sync()
        print("[SYNC] Slash commands sincronizados")
    except Exception as e: 
        print(f"[SYNC ERROR] {e}")

# 2.1 TELEGRAM START #
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
# 8 RESOLVE STATUS & GESTÃO DE ESTADO
# =========================
import time

# Variáveis de controle de estado para as bolinhas do painel
is_checking_weverse = False
is_checking_social = False
is_checking_ticket = False

def status_color(last_check_time, tipo):
    """
    Retorna o emoji de status baseado no tempo decorrido e estado atual.
    Substitui a antiga 'resolve_status' para compatibilidade com o Bloco 16 e 18.
    """
    # 1. Prioridade: Se o motor estiver rodando a função agora, mostra VERDE
    if globals().get(f"is_checking_{tipo}", False):
        return "🟢"
    
    # 2. Se nunca checou ou tempo zerado, mostra VERMELHO
    if not last_check_time or last_check_time == 0:
        return "🔴"
    
    # 3. Cálculo de latência
    elapsed = time.time() - last_check_time
    
    if elapsed < 600:    # Menos de 10 min: ATIVO (ROXO)
        return "🟣"
    elif elapsed < 1800: # Menos de 30 min: LENTO (AMARELO)
        return "🟡"
    else:                # Mais de 30 min: OFFLINE (VERMELHO)
        return "🔴"

def get_uptime():
    """Calcula o tempo de atividade do bot"""
    if 'start_time' not in globals():
        return "N/A"
    
    total_seconds = int(time.time() - globals()["start_time"])
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f"{hours}h {minutes}m {seconds}s"
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
# 10 EMOJIS & FORMATTER (ATUALIZADO)
# =========================
import re

MEMBER_EMOJI = {
    "rm": "🐨", "jin": "🐹", "suga": "🐱", 
    "jhope": "🐿️", "jimin": "🐥", "v": "🐻", 
    "jungkook": "🐰", "bts": "💜", "wootteo": "🛸"
}

def get_member_emoji(name):
    """Retorna o emoji do membro com fallback para 💜"""
    if not name: 
        return "💜"
    # Limpa caracteres especiais e espaços para bater com as chaves do dicionário
    clean_name = re.sub(r"[^a-z0-9]", "", str(name).lower())
    return MEMBER_EMOJI.get(clean_name, "💜")

def format_member(name):
    """Retorna dicionário formatado para uso nos alertas do Instagram/Weverse"""
    if not name:
        return {"emoji": "💜", "name": "BTS", "display": "💜 BTS"}
    
    emoji = get_member_emoji(name)
    u_name = str(name).upper()
    return {
        "emoji": emoji, 
        "name": u_name, 
        "display": f"{emoji} {u_name}"
    }
    
# =========================
# 11 ALERT DISPATCHER (ESTABILIZADO)
# =========================
import asyncio

async def send_alert(alert_type, message, increment=False):
    """
    Despachante central de alertas (Discord + Telegram).
    increment=False: Evita somar o contador duas vezes (Erro do Bloco 14/15).
    """
    try:
        # 1. Envio para o Discord
        if DISCORD_ALERTA_CHANNELS:
            for channel_id in DISCORD_ALERTA_CHANNELS:
                canal = bot_discord.get_channel(channel_id)
                if canal:
                    try:
                        await canal.send(message)
                    except Exception as e:
                        print(f"❌ [DISCORD ERR] Erro no canal {channel_id}: {e}")

        # 2. Envio para o Telegram (Usa a função estável do Bloco 10)
        if 'send_alert_telegram' in globals():
            await send_alert_telegram(message)
        
        # 3. Incremento Controlado (Só roda se explicitamente pedido)
        if increment:
            if "weverse" in alert_type:
                globals()["total_weverse"] += 1
            elif "ticket" in alert_type or "reposicao" in alert_type:
                globals()["total_tickets"] += 1
            elif "instagram" in alert_type or "tiktok" in alert_type or "social" in alert_type:
                globals()["total_social"] += 1
            
            # Salva após o incremento para manter o painel fiel
            if 'save_counters' in globals():
                await save_counters()

    except Exception as e:
        print(f"⚠️ [DISPATCH ERR] Falha crítica no envio: {e}")

async def increment_only(alert_type):
    """Apenas incrementa o contador sem enviar mensagem (Útil para logs silenciosos)"""
    if "weverse" in alert_type:
        globals()["total_weverse"] += 1
    elif "ticket" in alert_type:
        globals()["total_tickets"] += 1
    elif "social" in alert_type:
        globals()["total_social"] += 1
    
    if 'save_counters' in globals():
        await save_counters()

# =========================
# 12 PERSISTÊNCIA & STORAGE (CORRIGIDO)
# =========================
import json
import os

# Unificação de nomes conforme Bloco 18 e 22
# Resolve o erro de "amnésia" no reboot
COUNTER_DATA_FILE = "counters.json"
PANEL_DATA_FILE = "panel_ids.json"  # Alterado de panel_data para panel_ids

def save_storage(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ [STORAGE SAVE ERR] {e}")

def load_storage(filename, default=None):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ [STORAGE LOAD ERR] {filename}: {e}")
        return default

# Chaves internas unificadas para evitar duplicidade de painel
async def save_panel_ids():
    """Salva os IDs usando as chaves definitivas: tg_msg_id e dc_msg_id"""
    data = {
        "tg_msg_id": globals().get("panel_message_id"),
        "dc_msg_id": globals().get("discord_panel_msg_id")
    }
    save_storage(PANEL_DATA_FILE, data)

# =========================
# 13 SISTEMA DE PERSISTÊNCIA & WEVERSE ALERTS (COMPLETO)
# =========================
import hashlib
import asyncio
import json
import os
import time 

# INICIALIZAÇÃO DE GLOBAIS (ANTI-ERROR) # 
PANEL_BOOT_DONE = globals().get("PANEL_BOOT_DONE", False)
COUNTERS_FILE = "counters.json" 
WEVERSE_CACHE = {}
WEVERSE_LOCK = asyncio.Lock()

# SISTEMA DE DISCO (RAILWAY SAFE) #
async def save_counters():
    """Salva totais e IDs das mensagens para evitar 'amnésia' e duplicatas."""
    try:
        data = {
            "total_weverse": globals().get("total_weverse", 0),
            "total_social": globals().get("total_social", 0),
            "total_tickets": globals().get("total_tickets", 0),
            "last_weverse_check": globals().get("last_weverse_check", 0),
            "last_social_check": globals().get("last_social_check", 0),
            "last_ticket_check": globals().get("last_ticket_check", 0),
            # [FIX] Garante que o ID do painel seja persistido
            "tg_msg_id": globals().get("panel_message_id"),
            "dc_msg_id": globals().get("discord_panel_msg_id")
        }
        with open(COUNTERS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"❌ [SAVE ERROR] Falha ao salvar estado: {e}")

async def load_counters():
    """Carrega dados e IDs para garantir painel único no boot."""
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
            # [FIX] Recupera IDs para que o Motor edite em vez de criar novo
            globals()["panel_message_id"] = data.get("tg_msg_id")
            globals()["discord_panel_msg_id"] = data.get("dc_msg_id")
            
            print("✅ [SYSTEM] Estado e IDs restaurados com sucesso.")
        except Exception as e:
            print(f"❌ [LOAD ERROR] Falha ao carregar estado: {e}")

# LÓGICA DE DUPLICAÇÃO # 
def is_new_weverse_event(event_type, url, content=""):
    """Evita duplicação usando hash do conteúdo."""
    raw = f"{event_type}:{url}:{content}"
    new_hash = hashlib.md5(raw.encode("utf-8")).hexdigest()

    if WEVERSE_CACHE.get(event_type) == new_hash:
        return False

    WEVERSE_CACHE[event_type] = new_hash
    return True

# FUNÇÕES DE ALERTA (WEVERSE) # 

async def weverse_post(url, member_name, title, message_translated, found):
    async with WEVERSE_LOCK:
        if not is_new_weverse_event("post", url, title + message_translated):
            return

        globals()["total_weverse"] = globals().get("total_weverse", 0) + 1
        globals()["last_weverse_check"] = time.time()
        await save_counters() 

        emoji = get_member_emoji(member_name)
        msg = f"🩷 WEVERSE POST 🩷\n{emoji} {member_name.upper()} fez uma publicação\n📌 {title}\n📝 {message_translated}\n🔗 {url}"

        # [FIX] increment=False para não duplicar contagem no Bloco 11
        await send_alert("weverse_post", msg, increment=False)
        await update_panel()

async def weverse_live(url, member_name, found):
    async with WEVERSE_LOCK:
        if not is_new_weverse_event("live", url):
            return

        globals()["total_weverse"] = globals().get("total_weverse", 0) + 1
        globals()["last_weverse_check"] = time.time()
        await save_counters()

        emoji = get_member_emoji(member_name)
        msg = f"📹 WEVERSE LIVE 📹\n{emoji} {member_name.upper()} está ao vivo\n🔗 {url}"

        await send_alert("weverse_live", msg, increment=False)
        await update_panel()

async def weverse_news(url, member_name, message_translated, found):
    async with WEVERSE_LOCK:
        if not is_new_weverse_event("news", url, message_translated):
            return

        globals()["total_weverse"] = globals().get("total_weverse", 0) + 1
        globals()["last_weverse_check"] = time.time()
        await save_counters()

        emoji = get_member_emoji(member_name)
        msg = f"🚨 WEVERSE NEWS 🚨\n{emoji} {member_name.upper()} fez uma publicação\n📝 {message_translated}\n🔗 {url}"

        await send_alert("weverse_news", msg, increment=False)
        await update_panel()

async def weverse_media(url, member_name, title, message_translated, found):
    async with WEVERSE_LOCK:
        if not is_new_weverse_event("media", url, title + message_translated):
            return

        globals()["total_weverse"] = globals().get("total_weverse", 0) + 1
        globals()["last_weverse_check"] = time.time()
        await save_counters()

        emoji = get_member_emoji(member_name)
        msg = f"📀 WEVERSE MEDIA 📀\n{emoji} {member_name.upper()} fez uma publicação\n⭐ {title}\n📝 {message_translated}\n🔗 {url}"

        await send_alert("weverse_media", msg, increment=False)
        await update_panel()

# =========================
# 14 INSTAGRAM ALERTS (PRODUÇÃO SEGURA)
# ========================= 
import hashlib
import asyncio
import time

INSTAGRAM_CACHE = {"post": None, "reel": None, "story": None, "live": None}
INSTAGRAM_LOCK = asyncio.Lock()

def is_new_instagram(event_type, url, extra=""):
    raw = f"{event_type}:{url}:{extra}"
    new_hash = hashlib.md5(raw.encode("utf-8")).hexdigest()
    if INSTAGRAM_CACHE.get(event_type) == new_hash:
        return False
    INSTAGRAM_CACHE[event_type] = new_hash
    return True

async def instagram_post(url, member_name, title, found):
    async with INSTAGRAM_LOCK:
        if not is_new_instagram("post", url, title): return
        
        global total_social, last_social_check
        total_social += 1
        last_social_check = time.time()
        await save_counters()

        m_data = format_member(member_name)
        msg = f"🌟 **INSTAGRAM POST** 🌟\n{m_data['emoji']} **{m_data['name']}** fez uma publicação\n🔗 {url}"

        # FIX: increment=False para evitar contagem dupla no B11
        await send_alert("instagram_post", msg, increment=False)
        await update_panel()

async def instagram_reel(url, member_name, title, found):
    async with INSTAGRAM_LOCK:
        if not is_new_instagram("reel", url, title): return
        
        global total_social, last_social_check
        total_social += 1
        last_social_check = time.time()
        await save_counters()

        m_data = format_member(member_name)
        msg = f"🎬 **INSTAGRAM REELS** 🎬\n{m_data['emoji']} **{m_data['name']}** publicou um reels\n🔗 {url}"
        
        await send_alert("instagram_reels", msg, increment=False)
        await update_panel()

async def instagram_story(url, member_name, title, found):
    async with INSTAGRAM_LOCK:
        if not is_new_instagram("story", url, title): return
        
        global total_social, last_social_check
        total_social += 1
        last_social_check = time.time()
        await save_counters()

        m_data = format_member(member_name)
        msg = f"🫧 **INSTAGRAM STORY** 🫧\n{m_data['emoji']} **{m_data['name']}** publicou stories\n🔗 {url}"
        
        await send_alert("instagram_stories", msg, increment=False)
        await update_panel()

async def instagram_live(url, member_name, title, found):
    async with INSTAGRAM_LOCK:
        if not is_new_instagram("live", url): return
        
        global total_social, last_social_check
        total_social += 1
        last_social_check = time.time()
        await save_counters()

        m_data = format_member(member_name)
        msg = f"🎥 **INSTAGRAM LIVE** 🎥\n{m_data['emoji']} **{m_data['name']}** está ao vivo\n🔗 {url}"
        
        await send_alert("instagram_live", msg, increment=False)
        await update_panel()
        
# =========================================================
# 15 ALERTAS TIKTOK, YOUTUBE E TICKETMASTER
# =========================================================

async def tiktok_post(url, member_name, title, found):
    async with SOCIAL_LOCK:
        key = f"post:{member_name}:{url}"
        if not is_new_social(LAST_TIKTOK, key): return

        global total_social, last_social_check
        total_social += 1
        last_social_check = time.time()
        await save_counters()

        emoji = get_member_emoji(member_name)
        msg = f"🎵 **TIKTOK POST** 🎵\n{emoji} **{member_name.upper()}** publicou um vídeo\n🔗 {url}"
        
        await send_alert("tiktok_post", msg, increment=False)
        await update_panel()

async def youtube_post(url, final_url=None):
    async with SOCIAL_LOCK:
        key = f"post:{url}"
        if not is_new_social(LAST_YOUTUBE, key): return

        global total_social, last_social_check
        total_social += 1
        last_social_check = time.time()
        await save_counters()

        link = final_url or "https://www.youtube.com/@BTS"
        msg = f"🎞️ **YOUTUBE POST** 🎞️\n💜 **BTS** publicou vídeo novo\n🔗 {link}"
        
        await send_alert("youtube_post", msg, increment=False)
        await update_panel()

async def ticket_reposicao(url, data, setor, categoria):
    global total_tickets, last_ticket_check
    key = f"{url}:{data}:{setor}:{categoria}"
    if not is_new_event("reposicao", key): return

    total_tickets += 1
    last_ticket_check = time.time()
    await save_counters()

    msg = f"🔥 **ALERTA DE REPOSIÇÃO** 🔥\n📅 **Data:** {data}\n🎫 **Setor:** {setor}\n🏷️ **Cat:** {categoria}\n🔗 {url}"
    
    await send_alert("reposicao", msg, increment=False)
    await update_panel()
    
# =========================
# 16 TESTE DE SISTEMA (CORRIGIDO)
# =========================
@bot_discord.tree.command(name="teste", description="Valida o funcionamento do bot")
async def teste(interaction: discord.Interaction):
    """Diagnóstico consolidado enviado diretamente ao canal do usuário."""
    # Garante que o Discord não dê timeout enquanto o bot processa
    await interaction.response.defer(thinking=True)
    
    # Extração de dados (Fallback para 0 se não existir)
    uptime = get_uptime() if 'get_uptime' in globals() else "N/A"
    
    # Estrutura de dados para o relatório
    stats = {
        "Weverse": (globals().get("last_weverse_check", 0), "weverse", "total_weverse"),
        "Social": (globals().get("last_social_check", 0), "social", "total_social"),
        "Tickets": (globals().get("last_ticket_check", 0), "ticket", "total_tickets")
    }

    report = "## 🛠️ Relatório Wootteo\n"
    report += f"✅ **Status:** Online | ⏳ **Uptime:** {uptime}\n\n"

    for label, (t_last, t_key, count_key) in stats.items():
        # [FIX] Agora chama status_color, que foi corrigido no Bloco 8
        if 'status_color' in globals():
            color = status_color(t_last, t_key)
        else:
            color = "⚪"
            
        count = globals().get(count_key, 0)
        report += f"{color} **{label}:** `{count}` acessos\n"

    report += "\n---\n*Monitoramento ativo e operando em ciclos de segurança.*"

    try:
        await interaction.followup.send(content=report)
    except Exception as e:
        print(f"❌ [TEST ERR] {e}")

# =============================
# 17 COMMAND ENGINE FRAMEWORK - FINAL (COM FORÇA BRUTA)
# ============================
COMMANDS = {}

def command(name):
    def wrapper(func):
        COMMANDS[name] = func
        return func
    return wrapper

class CommandContext:
    def __init__(self, origin, interaction=None, chat_id=None):
        self.origin = origin
        self.interaction = interaction
        self.chat_id = chat_id
    @property
    def is_discord(self): return self.origin == "discord"
    @property
    def is_telegram(self): return self.origin == "telegram"

async def send(ctx, text):
    if ctx.is_discord and ctx.interaction:
        try:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(text)
            else:
                await ctx.interaction.followup.send(text)
        except: pass
    elif ctx.is_telegram and ctx.chat_id:
        try: await bot_ticket.send_message(chat_id=ctx.chat_id, text=text)
        except: pass

# COMANDOS BLOQUEADOS (LAYOUT ORIGINAL) # 
@command("ping")
async def ping(ctx):
    await send(ctx, f"🏓 Pong! | {get_uptime()}")

@command("comandos")
async def comandos(ctx):
    await send(ctx, "/ping\n/comandos\n/teste\n/bts")

@command("bts")
async def bts(ctx):
    membros = [
        "🐨 KIM NAMJOON", "🐹 KIM SEOKJIN", "🐱 MIN YOONGI",
        "🐿️ JUNG HOSEOK", "🐥 PARK JIMIN", "🐻 KIM TAEHYUNG",
        "🐰 JEON JUNGKOOK", "💜 BTS"
    ]
    if ctx.is_discord:
        await ctx.interaction.response.send_message(membros[0])
        for m in membros[1:]:
            await asyncio.sleep(1.2)
            await ctx.interaction.channel.send(m)
        await asyncio.sleep(1.2)
        await ctx.interaction.channel.send("🪭Ouça Arirang no Spotify🪭\nhttps://open.spotify.com/intl-pt/album/3ukkRHDHbN8tNRPKsGZR1h")
    else:
        texto = "\n".join(membros) + "\n\n🪭Ouça Arirang no Spotify🪭\nhttps://open.spotify.com/intl-pt/album/3ukkRHDHbN8tNRPKsGZR1h"
        await send(ctx, texto)

# /TESTE - AGORA FORÇANDO ALERTA NAS SALAS #
@command("teste")
async def teste(ctx):
    if ctx.is_discord:
        await send(ctx, "⚠️ [DISCORD] Forçando disparo de alertas nas salas de teste...")
        
        # Silencia o Telegram para não vazar
        orig_tg = bot_ticket.send_message
        bot_ticket.send_message = lambda *a, **k: asyncio.sleep(0) 
        
        try:
            # 1. Tenta a rotina do Bloco 16
            await run_full_test_discord()
            
            # 2. FORÇA BRUTA: Se a rotina acima não mandou nada (porque não houve mudança real),
            # nós mandamos um alerta manual agora para confirmar a rota.
            alerta_canais = globals().get("DISCORD_ALERTA_CHANNELS", [])
            for cid in alerta_canais:
                canal = bot_discord.get_channel(cid)
                if canal:
                    await canal.send("🚨 **SINAL DE TESTE:** Este canal está recebendo alertas corretamente.")

            await send(ctx, f"✅ Alertas enviados para {len(alerta_canais)} salas.\n✅ Telegram mantido em silêncio.")
        finally:
            bot_ticket.send_message = orig_tg
    else:
        await send(ctx, "⚠️ [TELEGRAM] Rodando teste padrão...")
        await run_full_test_discord()
        await send(ctx, "✅ Teste concluído.")

# PONTES DE EXECUÇÃO #
async def executar_discord(cmd, interaction):
    ctx = CommandContext(origin="discord", interaction=interaction)
    handler = COMMANDS.get(cmd)
    if handler: await handler(ctx)

async def executar_telegram(update, context):
    if not update.message or not update.message.text: return
    text = update.message.text.strip().lower()
    if text.startswith("/"):
        cmd = text.replace("/", "").split("@")[0]
        ctx = CommandContext(origin="telegram", chat_id=update.message.chat_id)
        handler = COMMANDS.get(cmd)
        if handler: await handler(ctx)

@bot_discord.tree.command(name="ping")
async def slash_ping(i: discord.Interaction): await executar_discord("ping", i)
@bot_discord.tree.command(name="bts")
async def slash_bts(i: discord.Interaction): await executar_discord("bts", i)
@bot_discord.tree.command(name="comandos")
async def slash_comandos(i: discord.Interaction): await executar_discord("comandos", i)

# =========================================================
# 17.1 UTILS: MOTOR DE REQUISIÇÃO ASSÍNCRONA (ANTI-BLOCK)
# =========================================================
import asyncio
import random

async def fetch_html(session, url):
    """Realiza a busca segura do HTML com disfarce dinâmico"""
    
    # Headers simulando um navegador moderno e real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/",
        "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        # Delay aleatório (1.5 a 4.5s) para evitar detecção de padrão robótico
        # Isso ajuda MUITO contra o erro 429 do Instagram
        await asyncio.sleep(random.uniform(1.5, 4.5))

        async with session.get(url, headers=headers, timeout=20) as response:
            if response.status == 200:
                return await response.text()
            
            # Se cair no 429 (Too Many Requests), avisa no console
            if response.status == 429:
                print(f"[LIMIT] Instagram/Site limitou o IP (429): {url}")
            elif response.status == 403:
                print(f"[BLOCK] Ticketmaster barrou o acesso (403): {url}")
            else:
                print(f"[FETCH] Status {response.status} para: {url}")
            
            return None

    except asyncio.TimeoutError:
        print(f"[TIMEOUT] Link muito lento: {url}")
        return None
    except Exception as e:
        print(f"[FETCH ERR] Falha crítica em {url}: {e}")
        return None
        
# =========================================================
# 18 SISTEMA INTEGRADO: ESTADO, PERSISTÊNCIA E FAXINA (COMPLETO)
# =========================================================
import asyncio
import time
import discord
from datetime import datetime

# --- VARIÁVEIS GLOBAIS DE ESTADO (PAINEL 🟢) ---
# Mantém os indicadores de checagem para as bolinhas funcionarem
is_checking_weverse = False
is_checking_social = False
is_checking_ticket = False

# --- PERSISTÊNCIA (NOMES UNIFICADOS COM BLOCO 13) ---
async def save_counters():
    """Salva estado garantindo que os IDs batam com o Recovery do Bloco 13"""
    data_counters = {
        "total_weverse": globals().get("total_weverse", 0),
        "total_social": globals().get("total_social", 0),
        "total_tickets": globals().get("total_tickets", 0),
        "total_tickets_found": globals().get("total_tickets_found", 0),
        "last_weverse_check": globals().get("last_weverse_check", 0),
        "last_social_check": globals().get("last_social_check", 0),
        "last_ticket_check": globals().get("last_ticket_check", 0),
        # [PONTE FIXA] Salva com os nomes que o seu Bloco 13 busca no reboot
        "tg_msg_id": globals().get("panel_message_id"),
        "dc_msg_id": globals().get("discord_panel_msg_id")
    }
    save_storage(COUNTER_DATA_FILE, data_counters)

async def load_counters():
    """Carrega os dados e resgata os IDs das mensagens do disco"""
    try:
        c_data = load_storage(COUNTER_DATA_FILE, {})
        if c_data:
            for k, v in c_data.items(): 
                globals()[k] = v
            # [FIX] Garante que as variáveis de ID recebam os valores do arquivo
            globals()["panel_message_id"] = c_data.get("tg_msg_id")
            globals()["discord_panel_msg_id"] = c_data.get("dc_msg_id")
    except Exception as e:
        print(f"[MEMÓRIA ERR] {e}")

# --- LÓGICA DO PAINEL (MANTIDO SEU PADRÃO VISUAL) ---
def status_color(last_check_time, tipo):
    # Regra: Se estiver checando agora, fica verde. Senão, calcula por tempo.
    if globals().get(f"is_checking_{tipo}", False): return "🟢"
    if not last_check_time or last_check_time == 0: return "🔴"
    elapsed = time.time() - last_check_time
    if elapsed < 600: return "🟣" # Online e Ativo
    elif elapsed < 1800: return "🟡" # Lento
    else: return "🔴" # Offline

def get_countdown_data():
    now_dt = datetime.now()
    next_show, next_local = "Continua…", "---"
    d_prox, d_br = 0, 0
    agenda_data = globals().get("AGENDA", [])
    
    for item in agenda_data:
        try:
            show_dt = datetime.strptime(f"{item[0]} {item[3]}", "%d/%m/%Y %H:%M")
            if show_dt > now_dt:
                next_show, next_local = item[0], f"{item[1]}, {item[2]}"
                d_prox = (show_dt.date() - now_dt.date()).days
                break
        except: continue
    
    for item in agenda_data:
        try:
            if "Brasil" in item[2]:
                br_date = datetime.strptime(item[0], "%d/%m/%Y").date()
                if br_date >= now_dt.date():
                    d_br = (br_date - now_dt.date()).days
                    break
        except: continue
    return next_show, next_local, d_prox, d_br

def gerar_texto_painel(data_show, city, d_prox, d_br):
    # SEU DESIGN VISUAL FOI 100% PRESERVADO AQUI
    lwc = globals().get("last_weverse_check", 0)
    lsc = globals().get("last_social_check", 0)
    ltc = globals().get("last_ticket_check", 0)
    tw, ts, tt, ttf = globals().get("total_weverse", 0), globals().get("total_social", 0), globals().get("total_tickets", 0), globals().get("total_tickets_found", 0)
    uptime = get_uptime() if 'get_uptime' in globals() else "Calculando..."

    return f"""🪭⊙⊝⊜ ARIRANG TOUR ⊙⊝⊜🪭

✈️ PRÓXIMAS DATAS
🎫 Data: {data_show}
📍 Local: {city}
🔔 Faltam {d_prox} dias.
🩷 Faltam {d_br} dias para o BTS no Brasil!

•°•🌙.•°ATUALIZAÇÕES •°.💫

🟣 Weverse {status_color(lwc, "weverse")}
🎯 Acessos realizados: {tw}

🟠 Redes sociais {status_color(lsc, "social")}
🎯 Acessos realizados: {ts}

💷 Ticketmaster {status_color(ltc, "ticket")}
🎯 Acessos realizados: {tt}
🎟️ Ingressos rastreados: {ttf}

👾 Wootteo em rota há: {uptime} ✨

🛰️ Status: 
🟢 Verificando
🟣 Ativo
🟡 Lento
🔴 Offline
"""

# --- MOTOR DE ATUALIZAÇÃO (ENGINE) ---
panel_lock = asyncio.Lock()
last_panel_update = 0

async def update_panel():
    global last_panel_update
    async with panel_lock:
        try:
            now = time.time()
            if (now - last_panel_update) < 5: return 
            last_panel_update = now
            
            d_show, city, d_prox, d_br = get_countdown_data()
            texto = gerar_texto_painel(d_show, city, d_prox, d_br)

            # --- DISCORD ---
            if DISCORD_PANEL_CHANNEL_ID:
                chan = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)
                if chan:
                    dc_id = globals().get("discord_panel_msg_id")
                    emb = discord.Embed(description=texto, color=0x8A2BE2)
                    
                    success_dc = False
                    if dc_id:
                        try:
                            msg = await chan.fetch_message(dc_id)
                            await msg.edit(embed=emb)
                            success_dc = True
                        except: globals()["discord_panel_msg_id"] = None

                    if not success_dc:
                        m = await chan.send(embed=emb)
                        globals()["discord_panel_msg_id"] = m.id
                        try: await m.pin()
                        except: pass

            # --- TELEGRAM ---
            if bot_ticket and PANEL_CHAT_ID:
                tg_id = globals().get("panel_message_id")
                success_tg = False
                if tg_id:
                    try:
                        await bot_ticket.edit_message_text(chat_id=PANEL_CHAT_ID, message_id=tg_id, text=texto)
                        success_tg = True
                    except: globals()["panel_message_id"] = None

                if not success_tg:
                    m = await bot_ticket.send_message(chat_id=PANEL_CHAT_ID, text=texto)
                    globals()["panel_message_id"] = m.message_id
            
            await save_counters()
        except Exception as e:
            print(f"[PANEL ENGINE ERR] {e}")

# --- EVENTOS DE STARTUP (RESTAURADO) ---

@bot_discord.event
async def on_ready():
    """Configura o status visual e restaura o painel no boot."""
    
    # [ESTRITAMENTE COMO SOLICITADO] - Define a atividade "Ouvindo"
    act = discord.Activity(
        type=discord.ActivityType.listening, 
        name="🪭Em tournê - Ouvindo: Arirang"
    )
    await bot_discord.change_presence(status=discord.Status.online, activity=act)
    
    # Evita que o boot rode duas vezes se o bot reconectar
    if globals().get("PANEL_BOOT_DONE", False): 
        return
        
    print(f"✅ BOT ONLINE: {bot_discord.user}")
    
    # Restaura memória e sincroniza painel inicial
    await load_counters()
    await update_panel()
    
    globals()["PANEL_BOOT_DONE"] = True
    
# =========================================================
# 19 MOTOR UNIFICADO (FIX: ESCOPO DE VARIÁVEIS GLOBAIS)
# =========================================================
import asyncio
import time
import aiohttp

# Inicialização de segurança no topo do bloco
_LAST_SOCIAL_RUN = 0
_LAST_WEVERSE_RUN = 0 
_INITIAL_WARMUP_DONE = False
_WARMUP_STEPS = 0

async def safe_monitor_cycle(session):
    # Declarando explicitamente as globais que o Bloco 18 (Painel) lê
    global total_tickets, total_weverse, total_social
    global _INITIAL_WARMUP_DONE, _LAST_SOCIAL_RUN, _LAST_WEVERSE_RUN, _WARMUP_STEPS
    global is_checking_ticket, is_checking_weverse, is_checking_social
    
    # Garantindo que as variáveis existam antes de somar
    if 'total_tickets' not in globals(): globals()['total_tickets'] = 0
    if 'total_weverse' not in globals(): globals()['total_weverse'] = 0
    if 'total_social' not in globals(): globals()['total_social'] = 0

    now = time.time()
    
    try:
        # 1. TICKETMASTER (1 MINUTO)
        globals()["is_checking_ticket"] = True
        if 'check_ticketmaster' in globals():
            await check_ticketmaster(session)
            globals()["total_tickets"] += 1
            globals()["last_ticket_check"] = now
        globals()["is_checking_ticket"] = False

        # 2. WEVERSE (2 MINUTOS)
        if now - _LAST_WEVERSE_RUN >= 120:
            globals()["is_checking_weverse"] = True
            if 'check_weverse' in globals():
                await check_weverse(session)
                globals()["total_weverse"] += 1
                globals()["last_weverse_check"] = now
                _LAST_WEVERSE_RUN = now
            globals()["is_checking_weverse"] = False

        # 3. SOCIAIS (2 MINUTOS)
        if now - _LAST_SOCIAL_RUN >= 120:
            globals()["is_checking_social"] = True
            if 'check_social' in globals():
                await check_social(session)
                globals()["total_social"] += 1
                globals()["last_social_check"] = now
                _LAST_SOCIAL_RUN = now
            globals()["is_checking_social"] = False
        
        # LÓGICA DE WARMUP
        if not _INITIAL_WARMUP_DONE:
            if _WARMUP_STEPS < 2:
                _WARMUP_STEPS += 1
                print(f"⚙️ [WARMUP] Passo {_WARMUP_STEPS}/2...")
            else:
                _INITIAL_WARMUP_DONE = True
                print("✅ [ENGINE] Monitoramento Ativo!")

        # ATUALIZAÇÃO DO PAINEL
        if 'update_panel' in globals():
            await update_panel()

    except Exception as e:
        print(f"⚠️ [MONITOR ERROR] {e}")

async def monitor_loop():
    await bot_discord.wait_until_ready()
    print("🚀 [MONITOR] Motor Iniciado (TM: 1min | WV/SOC: 2min)")
    
    async with aiohttp.ClientSession() as session:
        while True:
            await safe_monitor_cycle(session)
            await asyncio.sleep(60)

async def start_engine():
    if globals().get("_ENGINE_TASKS_STARTED", False): return
    globals()["_ENGINE_TASKS_STARTED"] = True
    asyncio.create_task(monitor_loop())
    if 'watchdog' in globals():
        asyncio.create_task(watchdog())

# =========================
# 20 STARTUP FINAL (RAILWAY SAFE)
# =========================
import asyncio

# BOOT GUARDS (EVITA DUPLICAÇÃO EM RESTART) # 
_BOOT_LOCK = asyncio.Lock()
_BOOT_STARTED = False
_ENGINE_TASK = None
_TELEGRAM_TASK = None

async def main():
    global _BOOT_STARTED, _ENGINE_TASK, _TELEGRAM_TASK

    print("🚀 [SYSTEM] Inicializando sistema completo...")

    async with _BOOT_LOCK:
        # 🔒 Proteção contra double boot no Railway/Render
        if _BOOT_STARTED:
            print("⚠️ [SYSTEM] Boot já executado (ignorado)")
            return
        _BOOT_STARTED = True

        try:
            # 1. Carrega memória (Contadores e IDs) antes de tudo
            await load_counters()
            
            # 2. Garante que o painel antigo seja limpo ou recuperado
            # se 'ensure_single_panel' existir no seu Bloco 18/22
            if 'ensure_single_panel' in globals():
                await ensure_single_panel()

            # 3. WEB SERVER (Monitoramento de Saúde)
            if 'keep_alive' in globals():
                keep_alive()

            # 4. TELEGRAM (Inicia como Task Independente)
            if _TELEGRAM_TASK is None and 'start_telegram' in globals():
                print("📨 [BOOT] Iniciando Telegram...")
                _TELEGRAM_TASK = asyncio.create_task(start_telegram())

            # 5. ENGINE PRINCIPAL (Monitoramento)
            if _ENGINE_TASK is None and 'start_engine' in globals():
                print("⚙️ [BOOT] Iniciando Motor de Monitoramento...")
                _ENGINE_TASK = asyncio.create_task(start_engine())

            # 6. DISCORD BOT (Entrypoint bloqueante)
            # Deve ser o último pois o .start() trava o loop
            print("👾 [BOOT] Conectando ao Discord...")
            await bot_discord.start(DISCORD_TOKEN)

        except Exception as e:
            print(f"❌ [SYSTEM ERROR] Falha no startup: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 [SYSTEM] Encerrado manualmente")
    except Exception as e:
        print(f"💀 [SYSTEM CRASH] {e}")

# =========================
# 21 PANEL LOOP (ANTI-SPAM)
# =========================
import asyncio

PANEL_LOOP_RUNNING = False
PANEL_LOOP_LOCK = asyncio.Lock()
PANEL_LOOP_TASK = None

async def panel_loop():
    """
    Atualização passiva para garantir que o Uptime e os 
    contadores estejam sempre frescos, mesmo sem alertas.
    """
    global PANEL_LOOP_RUNNING
    async with PANEL_LOOP_LOCK:
        if PANEL_LOOP_RUNNING: return
        PANEL_LOOP_RUNNING = True

    print("📊 [PANEL LOOP] Iniciado (Ciclo de 60s)")

    try:
        while True:
            try:
                # [FIX] Aumentado para 60s para evitar Erro 429 (Spam)
                # O motor (B19) já atualiza o painel quando há posts.
                # Este loop serve apenas para o relógio de Uptime.
                await update_panel()
            except Exception as e:
                print(f"⚠️ [PANEL LOOP ERR] {e}")

            await asyncio.sleep(60) 
    finally:
        PANEL_LOOP_RUNNING = False

async def start_background_tasks():
    """Starter controlado para as tasks de fundo."""
    global PANEL_LOOP_TASK
    async with PANEL_LOOP_LOCK:
        if PANEL_LOOP_TASK and not PANEL_LOOP_TASK.done():
            return
        PANEL_LOOP_TASK = asyncio.create_task(panel_loop())
        
# =========================
# 22 BOOT MASTER SAFE (ABSOLUTE MODE)
# =========================
import asyncio
import hashlib

BOOT_LOCK = asyncio.Lock()
BOOT_DONE = False
PANEL_BOOT_DONE = False
PANEL_BOOT_LOCK = asyncio.Lock()

# FINGERPRINT DO ESTADO (ANTI MULTI INSTANCE) #
def get_boot_fingerprint():
    # Usa as variáveis globais de configuração para criar uma assinatura única da instância
    raw = f"{globals().get('DISCORD_PANEL_CHANNEL_ID')}:{globals().get('PANEL_CHAT_ID')}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

# RECOVERY UNIFICADO (TELEGRAM + DISCORD) #
async def recover_panels():
    global panel_message_id, discord_panel_msg_id

    # Prioridade 1: Recuperar do Arquivo (Mais seguro contra resets)
    # [FIX] Chamando a função correta de leitura do Bloco 18
    await load_counters() 

    # Prioridade 2: Busca ativa no histórico do Discord se o ID no disco for inválido
    if not discord_panel_msg_id:
        try:
            channel = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)
            if not channel: 
                channel = await bot_discord.fetch_channel(DISCORD_PANEL_CHANNEL_ID)
            
            if channel:
                async for msg in channel.history(limit=50):
                    # [CORREÇÃO CRÍTICA]: O painel é um Embed, então buscamos dentro da descrição do Embed
                    if msg.author == bot_discord.user and msg.embeds:
                        embed_desc = msg.embeds[0].description or ""
                        if "ARIRANG TOUR" in embed_desc:
                            discord_panel_msg_id = msg.id
                            print(f"✅ [RECOVERY] Painel Discord localizado: {msg.id}")
                            break
        except Exception as e:
            print(f"⚠️ [RECOVERY DISCORD ERR] {e}")

# SINGLE PANEL GUARD (IDEMPOTENTE) #
async def ensure_single_panel():
    global PANEL_BOOT_DONE
    async with PANEL_BOOT_LOCK:
        if PANEL_BOOT_DONE: return
        await recover_panels()
        PANEL_BOOT_DONE = True

# BOOT SEQUENCE FINAL (MASTER SAFE) #
async def safe_boot():
    global BOOT_DONE
    async with BOOT_LOCK:
        if BOOT_DONE: return
        print("🛠️ [BOOT] Iniciando sequência master...")
        await ensure_single_panel()
        await asyncio.sleep(1)
        BOOT_DONE = True
        print("🏁 [BOOT] Sistema liberado com segurança total!")

# =========================================================
# 23 BOOT SEQUENCE MAP (ORDER CONTROL & RAILWAY SAFE)
# =========================================================
import asyncio
import time

# ESTADO GLOBAL DE EXECUÇÃO #
ENGINE_STARTED = False
WATCHDOG_STARTED = False

def system_integrity_check():
    """Verifica se o boot foi concluído e os IDs existem."""
    return {
        "boot_done": globals().get("BOOT_DONE", False),
        "panel_ok": bool(globals().get("panel_message_id") or globals().get("discord_panel_msg_id"))
    }

async def wait_system_ready():
    """Gate de segurança que aguarda o Bloco 22 terminar."""
    timeout = 45 # Reduzido para ser mais ágil no Railway
    start = time.time()

    while True:
        status = system_integrity_check()
        # Se o boot terminou (Bloco 22) ou se o timeout bateu, liberamos a engine
        if status["boot_done"]:
            print("🚀 [BOOT MAP] Sistema pronto!")
            return True

        if time.time() - start > timeout:
            print("⚠️ [BOOT MAP] Timeout atingido. Forçando liberação para evitar travamento.")
            return False

        await asyncio.sleep(2)

async def boot_sequence_map():
    """Orquestrador final que amarra todos os blocos."""
    global ENGINE_STARTED, WATCHDOG_STARTED
    
    print("🛰️ [BOOT MAP] Sincronizando camadas...")

    # 1. Espera o Bloco 22 (Recuperação de IDs e Arquivos)
    await wait_system_ready()

    # 2. Inicia o Motor de Monitoramento (Bloco 19)
    if not ENGINE_STARTED:
        if 'start_engine' in globals():
            asyncio.create_task(start_engine())
            ENGINE_STARTED = True
            print("✅ [BOOT MAP] Engine monitor liberado.")

    # 3. Inicia o Loop do Painel (Bloco 21)
    if 'start_background_tasks' in globals():
        await start_background_tasks()
        print("✅ [BOOT MAP] Sync loop liberado.")

    print("🌟 [BOOT MAP] Wootteo operando em 100%!")

# Variáveis de Cooldown para o Watchdog do Bloco 19 não flodar as APIs
LAST_REPAIR_TIME = 0
REPAIR_COOLDOWN = 60 

def can_run_repair():
    global LAST_REPAIR_TIME
    now = time.time()
    if now - LAST_REPAIR_TIME < REPAIR_COOLDOWN:
        return False
    LAST_REPAIR_TIME = now
    return True
