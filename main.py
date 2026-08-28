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
import asyncio, time, hashlib, os, re, json, random
from datetime import datetime
from zoneinfo import ZoneInfo
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
PANEL_CHAT_ID = -1003972186058
DISCORD_PANEL_CHANNEL_ID = 1494667029150695625
# IDs específicos para roteamento de alertas
DISCORD_TICKETS_CHANNEL_ID = 1494670074374651985
DISCORD_ALERTA_CHANNELS = [DISCORD_TICKETS_CHANNEL_ID]
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
}
stored_counters = load_storage(COUNTERS_FILE, default_counters)
stored_panel = load_storage(PANEL_DATA_FILE, {"tg_msg_id": None, "dc_msg_id": None})
# Variáveis globais sincronizadas (Usando .get para evitar KeyError)
total_tickets = stored_counters.get("total_tickets", 0)
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
        data = {
            "total_tickets": globals().get("total_tickets", 0),
            "last_ticket_check": globals().get("last_ticket_check", 0),
            "tg_msg_id": globals().get("panel_message_id"),
            "dc_msg_id": globals().get("discord_panel_msg_id")
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
# Auxiliar para estabilização de eventos do Bloco 13
EVENT_CACHE_REP = {}
def is_new_event(tipo, key):
    if key in EVENT_CACHE_REP: return False
    EVENT_CACHE_REP[key] = time.time()
    return True
# =========================
# 6 LINKS (ÚNICO - NÃO DUPLICAR)
# =========================
TICKET_LINKS = [
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-28-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-30-10",
    "https://www.ticketmaster.com.br/event/venda-geral-bts-world-tour-arirang-31-10"
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
    ("28/08/2026", "Chicago", "Estados Unidos", "20:00"),
    ("01/09/2026", "Los Angeles", "Estados Unidos", "20:00"),
    ("02/09/2026", "Los Angeles", "Estados Unidos", "20:00"),
    ("05/09/2026", "Los Angeles", "Estados Unidos", "20:00"),
    ("06/09/2026", "Los Angeles", "Estados Unidos", "20:00"),
    ("02/10/2026", "Bogotá", "Colômbia", "20:00"),
    ("03/10/2026", "Bogotá", "Colômbia", "20:00"),
    ("07/10/2026", "Lima", "Peru", "20:00"),
    ("09/10/2026", "Lima", "Peru", "20:00"),
    ("10/10/2026", "Lima", "Peru", "20:00"),
    ("14/10/2026", "Santiago", "Chile", "20:00"),
    ("16/10/2026", "Santiago", "Chile", "20:00"),
    ("17/10/2026", "Santiago", "Chile", "20:00"),
    ("23/10/2026", "Buenos Aires", "Argentina", "20:00"),
    ("24/10/2026", "Buenos Aires", "Argentina", "20:00"),
    ("28/10/2026", "São Paulo", "Brasil", "20:00"),
    ("30/10/2026", "São Paulo", "Brasil", "20:00"),
    ("31/10/2026", "São Paulo", "Brasil", "20:00"),
    ("19/11/2026", "Kaohsiung", "Taiwan", "20:00"),
    ("21/11/2026", "Kaohsiung", "Taiwan", "20:00"),
    ("22/11/2026", "Kaohsiung", "Taiwan", "20:00"),
    ("03/12/2026", "Bangkok", "Tailândia", "20:00"),
    ("05/12/2026", "Bangkok", "Tailândia", "20:00"),
    ("06/12/2026", "Bangkok", "Tailândia", "20:00"),
    ("12/12/2026", "Kuala Lumpur", "Malásia", "20:00"),
    ("13/12/2026", "Kuala Lumpur", "Malásia", "20:00"),
    ("17/12/2026", "Singapura", "Singapura", "20:00"),
    ("19/12/2026", "Singapura", "Singapura", "20:00"),
    ("20/12/2026", "Singapura", "Singapura", "20:00"),
    ("22/12/2026", "Singapura", "Singapura", "20:00"),
    ("26/12/2026", "Jacarta", "Indonésia", "20:00"),
    ("27/12/2026", "Jacarta", "Indonésia", "20:00"),
    ("29/12/2026", "Jacarta", "Indonésia", "20:00"),
    ("10/02/2027", "Melbourne", "Austrália", "20:00"),
    ("12/02/2027", "Melbourne", "Austrália", "20:00"),
    ("13/02/2027", "Melbourne", "Austrália", "20:00"),
    ("20/02/2027", "Sydney", "Austrália", "20:00"),
    ("21/02/2027", "Sydney", "Austrália", "20:00"),
    ("04/03/2027", "Hong Kong", "Hong Kong", "20:00"),
    ("06/03/2027", "Hong Kong", "Hong Kong", "20:00"),
    ("07/03/2027", "Hong Kong", "Hong Kong", "20:00"),
    ("13/03/2027", "Bocaue", "Filipinas", "20:00"),
    ("14/03/2027", "Bocaue", "Filipinas", "20:00"),
    ("16/03/2027", "Bocaue", "Filipinas", "20:00")
]

# 8 RESOLVE STATUS & GESTÃO DE ESTADO
# =========================
import time
is_checking_ticket = False
def status_color(last_check_time, tipo):
    if globals().get(f"is_checking_{tipo}", False):
        return "🟢"
    if not last_check_time or last_check_time == 0:
        return "🔴"
    elapsed = time.time() - last_check_time
    if elapsed < 600:    
        return "🟣"
    elif elapsed < 1800: 
        return "🟡"
    else:                
        return "🔴"
def get_uptime():
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
# 10 ALERT DISPATCHER (ESTABILIZADO)
# =========================
import asyncio
async def send_alert(alert_type, message, increment=False):
    try:
      if DISCORD_ALERTA_CHANNELS:
for channel_id in DISCORD_ALERTA_CHANNELS:
canal = bot_discord.get_channel(channel_id)
if canal:
try: await canal.send(message)
except Exception as e: print(f"❌ [DISCORD ERR] {channel_id}: {e}")
if increment:
if "ticket" in alert_type or "reposicao" in alert_type:
globals()["total_tickets"] += 1
await save_counters()
except Exception as e:
print(f"⚠️ [DISPATCH ERR] {e}")
async def increment_only(alert_type):
if "ticket" in alert_type:
globals()["total_tickets"] += 1
await save_counters()

# =========================
# 11 PERSISTÊNCIA & STORAGE (CORRIGIDO)
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
# 12 SISTEMA DE PERSISTÊNCIA (COMPLETO)
# =========================
import hashlib
import asyncio
import json
import os
import time 

# INICIALIZAÇÃO DE GLOBAIS (ANTI-ERROR) # 
PANEL_BOOT_DONE = globals().get("PANEL_BOOT_DONE", False)
COUNTERS_FILE = "counters.json" 

# SISTEMA DE DISCO (RAILWAY SAFE) #
async def save_counters():
    """Salva totais e IDs das mensagens para evitar 'amnésia' e duplicatas."""
    try:
        data = {
            "total_tickets": globals().get("total_tickets", 0),
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

            globals()["total_tickets"] = data.get("total_tickets", 0)
            globals()["last_ticket_check"] = data.get("last_ticket_check", 0)
            # [FIX] Recupera IDs para que o Motor edite em vez de criar novo
            globals()["panel_message_id"] = data.get("tg_msg_id")
            globals()["discord_panel_msg_id"] = data.get("dc_msg_id")

            print("✅ [SYSTEM] Estado e IDs restaurados com sucesso.")
        except Exception as e:
            print(f"❌ [LOAD ERROR] Falha ao carregar estado: {e}")


# =========================================================
# 13 ALERTAS TICKETMASTER
# =========================================================

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
# 14 TESTE DE SISTEMA (CORRIGIDO)
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
# 15 COMMAND ENGINE FRAMEWORK - FINAL (COM FORÇA BRUTA)
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
# 16 UTILS: MOTOR DE REQUISIÇÃO ASSÍNCRONA (ANTI-BLOCK)
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
# 17 SISTEMA INTEGRADO: ESTADO, PERSISTÊNCIA E FAXINA (COMPLETO)
# =========================================================
import asyncio
import time
import discord
from datetime import datetime

# --- VARIÁVEIS GLOBAIS DE ESTADO (PAINEL 🟢) ---
# Mantém os indicadores de checagem para as bolinhas funcionarem
is_checking_ticket = False

# --- PERSISTÊNCIA (NOMES UNIFICADOS COM BLOCO 13) ---
async def save_counters():
    """Salva estado garantindo que os IDs batam com o Recovery do Bloco 13"""
    data_counters = {
        "total_tickets": globals().get("total_tickets", 0),
        "total_tickets_found": globals().get("total_tickets_found", 0),
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

def status_color(last_check_time, tipo):
    # 1. ATIVIDADE EM TEMPO REAL
    # Se o motor do Bloco 19 estiver acessando o site agora, fica Verde
    if globals().get(f"is_checking_{tipo}", False): 
        return "🟢" 

    # 2. VERIFICAÇÃO DE HISTÓRICO
    if not last_check_time or last_check_time == 0: 
        return "🔴" 

    elapsed = time.time() - last_check_time

    # 3. ESTADOS DE OPERAÇÃO
    # Se o último acesso foi há menos de 10 min, mantém Roxo (Ativo)
    if elapsed < 600: 
        return "🟣" 
    # Se passar de 10 min, entra em atenção (Amarelo)
    elif elapsed < 1800: 
        return "🟡" 
    # Somente após 30 min sem registros ele fica Vermelho (Offline)
    else: 
        return "🔴"

# Fusos horários oficiais das cidades da agenda.
# A hora informada em AGENDA é a hora LOCAL do show.
AGENDA_TIMEZONES = {
    "Chicago": "America/Chicago",
    "Los Angeles": "America/Los_Angeles",
    "Bogotá": "America/Bogota",
    "Lima": "America/Lima",
    "Santiago": "America/Santiago",
    "Buenos Aires": "America/Argentina/Buenos_Aires",
    "São Paulo": "America/Sao_Paulo",
    "Kaohsiung": "Asia/Taipei",
    "Bangkok": "Asia/Bangkok",
    "Kuala Lumpur": "Asia/Kuala_Lumpur",
    "Singapura": "Asia/Singapore",
    "Jacarta": "Asia/Jakarta",
    "Melbourne": "Australia/Melbourne",
    "Sydney": "Australia/Sydney",
    "Hong Kong": "Asia/Hong_Kong",
    "Bocaue": "Asia/Manila",
}

def get_countdown_data():
    # IMPORTANTE:
    # datetime.now() sozinho usa o fuso do servidor (Railway/UTC).
    # Como cada show está marcado pela hora LOCAL da cidade, isso podia
    # fazer o painel considerar um show como já encerrado antes da hora real.
    now_utc = datetime.now(ZoneInfo("UTC"))

    next_show, next_local = "Continua…", "---"
    d_prox, d_br = 0, 0
    agenda_data = globals().get("AGENDA", [])

    for item in agenda_data:
        try:
            city = item[1]
            timezone_name = AGENDA_TIMEZONES.get(city, "UTC")
            local_tz = ZoneInfo(timezone_name)

            # A data/hora da agenda representa a hora LOCAL do show.
            show_naive = datetime.strptime(
                f"{item[0]} {item[3]}",
                "%d/%m/%Y %H:%M"
            )
            show_dt = show_naive.replace(tzinfo=local_tz)

            # Compara corretamente, independentemente do fuso do servidor.
            if show_dt.astimezone(ZoneInfo("UTC")) > now_utc:
                now_local = now_utc.astimezone(local_tz)
                next_show = item[0]
                next_local = f"{item[1]}, {item[2]}"
                d_prox = max(0, (show_dt.date() - now_local.date()).days)
                break

        except Exception as err:
            print(
                f"⚠️ [AGENDA ERR] Data inválida ignorada "
                f"({item[0]} - {item[1]}): {err}"
            )
            continue

    # Contagem para o primeiro show no Brasil, usando a data de São Paulo.
    try:
        br_tz = ZoneInfo("America/Sao_Paulo")
        br_today = now_utc.astimezone(br_tz).date()

        for item in agenda_data:
            if "Brasil" in item[2]:
                br_date = datetime.strptime(item[0], "%d/%m/%Y").date()
                if br_date >= br_today:
                    d_br = (br_date - br_today).days
                    break
    except Exception as err:
        print(f"⚠️ [AGENDA BR ERR] {err}")

    return next_show, next_local, d_prox, d_br

def gerar_texto_painel(data_show, city, d_prox, d_br):
    # SEU DESIGN VISUAL FOI 100% PRESERVADO AQUI
    ltc = globals().get("last_ticket_check", 0)
    tt = globals().get("total_tickets", 0)
    ttf = globals().get("total_tickets_found", 0)
    uptime = get_uptime() if 'get_uptime' in globals() else "Calculando..."

    return f"""🪭⊙⊝⊜ ARIRANG TOUR ⊙⊝⊜🪭

✈️ PRÓXIMAS DATAS
🎫 Data: {data_show}
📍 Local: {city}
🔔 Faltam {d_prox} dias.
🩷 Faltam {d_br} dias para o BTS no Brasil!

•°•🌙.•°ATUALIZAÇÕES •°.💫

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
    """Configura o status visual e força a atualização do painel no boot."""
    act = discord.Activity(
        type=discord.ActivityType.listening, 
        name="🪭Em tournê - Ouvindo: Arirang"
    )
    await bot_discord.change_presence(status=discord.Status.online, activity=act)

    print(f"✅ BOT ONLINE: {bot_discord.user}")

    # Carrega dados e força a edição do painel imediatamente ao ligar
    await load_counters()
    await update_panel()

    globals()["PANEL_BOOT_DONE"] = True

# =========================================================
# 18 MOTOR UNIFICADO (FIX: SINCRONIA DE CORES DAS BOLINHAS)
# =========================================================
import asyncio
import time
import aiohttp

# --- REFERÊNCIA DE MEMÓRIA ---
if 'contadores_globais' not in globals():
    globals()['contadores_globais'] = {'total_tickets': 0}

_INITIAL_WARMUP_DONE = False
_WARMUP_STEPS = 0

async def safe_monitor_cycle(session):
    global _INITIAL_WARMUP_DONE, _WARMUP_STEPS
    now = time.time()
    stats = globals()['contadores_globais']

    try:
        # 1. TICKETMASTER (1 MINUTO)
        stats['total_tickets'] += 1
        globals()['total_tickets'] = stats['total_tickets']

        # AJUSTE DE CORES: Salva nos dois formatos para o Bloco 18 encontrar
        globals()['last_check_ticket'] = now
        globals()['last_ticket_check'] = now 

        globals()["is_checking_ticket"] = True
        if 'check_ticketmaster' in globals():
            try:
                await asyncio.wait_for(check_ticketmaster(session), timeout=15.0)
                if 'update_panel' in globals(): await update_panel()
            except Exception: pass 
        globals()["is_checking_ticket"] = False

        # LOGS DE CONTROLE
        if not _INITIAL_WARMUP_DONE:
            _WARMUP_STEPS += 1
            if _WARMUP_STEPS >= 2: _INITIAL_WARMUP_DONE = True
            print(f"⚙️ [WARMUP] Passo {_WARMUP_STEPS}/2 concluído.")

        # ATUALIZAÇÃO FINAL (Retorno ao estado de descanso)
        if 'update_panel' in globals():
            await update_panel()

    except Exception as e:
        print(f"⚠️ [MONITOR ERROR] {e}")

async def monitor_loop():
    await bot_discord.wait_until_ready()
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
# 19 STARTUP FINAL (RAILWAY SAFE)
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
        if _BOOT_STARTED:
            print("⚠️ [SYSTEM] Boot já executado (ignorado)")
            return
        _BOOT_STARTED = True

        try:
            await load_counters()

            if 'keep_alive' in globals():
                keep_alive()

            # Ativa a atualização contínua em segundo plano
            if 'start_background_tasks' in globals():
                await start_background_tasks()

            if _TELEGRAM_TASK is None and 'start_telegram' in globals():
                print("📨 [BOOT] Iniciando Telegram...")
                _TELEGRAM_TASK = asyncio.create_task(start_telegram())

            if _ENGINE_TASK is None and 'start_engine' in globals():
                print("⚙️ [BOOT] Iniciando Motor de Monitoramento...")
                _ENGINE_TASK = asyncio.create_task(start_engine())

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
# 20 PANEL LOOP (ANTI-SPAM)
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
# 21 BOOT MASTER SAFE (ABSOLUTE MODE)
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

=========================================================
22 BOOT SEQUENCE MAP (ORDER CONTROL & RAILWAY SAFE)
=========================================================
ENGINE_STARTED = False
async def run_full_test_discord(): await asyncio.sleep(0.5)
def system_integrity_check():
return {
"boot_done": globals().get("BOOT_DONE", False),
"panel_ok": bool(globals().get("panel_message_id") or globals().get("discord_panel_msg_id"))
}
async def wait_system_ready():
timeout = 15
start = time.time()
while True:
status = system_integrity_check()
if status["boot_done"] or (time.time() - start > timeout): return True
await asyncio.sleep(1)
async def boot_sequence_map():
global ENGINE_STARTED
if ENGINE_STARTED: return
ENGINE_STARTED = True
print("🛰️ [BOOT MAP] Sincronizando camadas...")
asyncio.create_task(safe_boot())
await wait_system_ready()
await start_background_tasks()
await start_engine()
asyncio.create_task(start_telegram())
globals()["PANEL_BOOT_DONE"] = True
print("🌟 [BOOT MAP] Wootteo operando em 100%!")
if name == "main":
try: asyncio.run(main())
except KeyboardInterrupt: print("🛑 [SYSTEM] Encerrado")
except Exception as e: print(f"💀 [SYSTEM CRASH] {e}")
IME = now
    return True

