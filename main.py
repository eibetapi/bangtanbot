# =========================
# 0 BOT WOOTTEO
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
# 1 CONFIGURAÇÃO DE CREDENCIAIS & TELEGRAM
# ==========================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Corrigido: Removido caractere invisível/espaço após o ID
CHAT_ID = -1003920883053 

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Dicionário para rastrear a última mensagem do painel e evitar spam
panel_message = None 
panel_initialized = False

bot_ticket = None
if TELEGRAM_TOKEN:
    try:
        bot_ticket = Bot(token=TELEGRAM_TOKEN)
        print("[SISTEMA] Telegram configurado com sucesso.")
    except Exception as e:
        print(f"[ERRO CONFIG TELEGRAM] {e}")


# ==========================================
# 2 CONTADORES GLOBAIS
# ==========================================
total_tickets = 0
total_buy = 0
total_weverse = 0
total_social = 0

last_ticket_check = time.time()
last_buy_check = time.time()
last_weverse_check = time.time()
last_social_check = time.time()

start_time = time.time()

CONTENT_HASH = {}
SEEN_TICKET = set()
SEEN_BUY = set()
SEEN_WEVERSE = set()
SEEN_SOCIAL = set()

# =========================
# 3 DISCORD SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot_discord = commands.Bot(command_prefix="!", intents=intents)

# IDs dos Canais (Confirmado o final ...625 para o Painel)
DISCORD_PANEL_CHANNEL_ID = 1494667029150695625
DISCORD_TICKETS_CHANNEL_ID = 1494670074374651985
DISCORD_WEVERSE_CHANNEL_ID = 1494680233025208461
DISCORD_SOCIAL_CHANNEL_ID = 1494682078950981864

@bot_discord.event
async def on_ready():
    print(f"[DISCORD] Conectado como {bot_discord.user}")
    
    # Define a frase exatamente como você solicitou
    await bot_discord.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, 
            name="Em tournê - ouvindo: Arirang 🪭"
        ),
        status=discord.Status.online
    )

    try:
        synced = await bot_discord.tree.sync()
        print(f"[DISCORD] Slash commands sincronizados: {len(synced)}")
    except Exception as e:
        print(f"[DISCORD SYNC ERROR] {e}")

    # Inicia o servidor Keep Alive e o Loop de Monitoramento
    keep_alive()
    
    # Garante que o monitor só inicie se não houver um rodando
    if not hasattr(bot_discord, 'monitor_started'):
        bot_discord.loop.create_task(monitor_loop())
        bot_discord.monitor_started = True


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
    
    # Cria um resumo (hash) do conteúdo ignorando espaços extras
    content_clean = " ".join(html.split())
    new_hash = hashlib.md5(content_clean.encode('utf-8')).hexdigest()
    
    # TRAVA DE SEGURANÇA 1: Se o bot acabou de ligar (hash vazio)
    # Ele apenas armazena o valor atual como 'conhecido' e retorna False
    if url not in CONTENT_HASH:
        CONTENT_HASH[url] = new_hash
        print(f"[MEMÓRIA] URL aprendida: {url}")
        return False
        
    # TRAVA DE SEGURANÇA 2: Comparação Real
    if CONTENT_HASH[url] != new_hash:
        CONTENT_HASH[url] = new_hash
        print(f"[ALERTA] Mudança real detectada em: {url}")
        return True
        
    # Se for igual, ignora silenciosamente
    return False


# =========================
# 6 LINKS
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
    "jhope": "https://www.tiktok.com/@iamurhope",
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
# 8 CONTROLE
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
    if 'AGENDA' not in globals(): return "Continua…", "---", 0
    
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
# 9 SESSION (FIX: CLIENT SESSION ÚNICA)
# =========================
import aiohttp

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
    "rm": "🐨", "jin": "🐹", "suga": "🐱", "jhope": "🐿️",
    "jimin": "🐥", "v": "🐻", "jungkook": "🐰", "bts": "💜", "wootteo": "🛸"
}

def get_member_emoji(member_name):
    return MEMBER_EMOJI.get(str(member_name).lower(), "💜")

def format_member(member_name):
    emoji = get_member_emoji(member_name)
    name = str(member_name).upper()
    return emoji, name 

# =========================
# 11 ROTEAMENTO DE ALERTAS (FIX: TELEGRAM SAFE)
# =========================
async def send_to_all(alert_type, message):
    if bot_ticket is not None:
        try:
            await bot_ticket.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"[TELEGRAM ERROR] {e}")

    try:
        loop = asyncio.get_running_loop()
        
        if alert_type in ["ticket", "reposicao", "nova_data", "revenda", "agenda"]:
            loop.create_task(send_discord(DISCORD_TICKETS_CHANNEL_ID, message))
        
        elif alert_type in ["weverse_post", "weverse_live", "weverse_news", "weverse_media"]:
            loop.create_task(send_discord(DISCORD_WEVERSE_CHANNEL_ID, message))
        
        elif alert_type in ["instagram_post", "instagram_reels", "instagram_stories", "instagram_live", "tiktok_post", "tiktok_live"]:
            loop.create_task(send_discord(DISCORD_SOCIAL_CHANNEL_ID, message))
        
        else:
            if 'DISCORD_NEWS_CHANNEL_ID' in globals():
                loop.create_task(send_discord(DISCORD_NEWS_CHANNEL_ID, message))
    except Exception as e:
        print(f"[DISCORD ROUTING ERROR] {e}")

# =============================================================
# 12 FUNÇÃO DE BOOT (INICIALIZAÇÃO - SEM PAINEL GENÉRICO)
# =============================================================

async def send_boot():
    """Lança apenas o layout obrigatório no Telegram e Discord."""
    global panel_message_id, panel_chat_id, panel_initialized, discord_panel_msg_id
    
    boot_msg = "🛸•°•Wootteo entrando em rota°•°🛸"
    # Conteúdo inicial respeitando o seu layout
    conteudo_inicial = "🪭⊙⊝⊜ARIRANG TOUR⊙⊝⊜🪭\n\n⌛ Sincronizando com os servidores..."

    # --- TELEGRAM ---
    if bot_ticket and CHAT_ID:
        try:
            await bot_ticket.send_message(chat_id=CHAT_ID, text=boot_msg)
            # Posta o painel real
            p_msg = await bot_ticket.send_message(chat_id=CHAT_ID, text=conteudo_inicial)
            panel_message_id = p_msg.message_id
            panel_chat_id = CHAT_ID
            # Fixa no canal
            await bot_ticket.pin_chat_message(chat_id=CHAT_ID, message_id=panel_message_id)
        except Exception as e:
            print(f"[TELEGRAM BOOT ERROR] {e}")

    # --- DISCORD ---
    try:
        canal = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)
        if canal:
            await canal.send(boot_msg)
            # Envia o Layout Obrigatório direto no Embed Roxo (sem o título genérico)
            embed = discord.Embed(description=conteudo_inicial, color=0x9b59b6)
            d_msg = await canal.send(embed=embed)
            discord_panel_msg_id = d_msg.id
    except Exception as e:
        print(f"[DISCORD BOOT ERROR] {e}")

    panel_initialized = True


# =============================================================
# 13 ATUALIZAÇÃO DO PAINEL (MANTENDO APENAS O LAYOUT ARIRANG)
# =============================================================

async def update_panel():
    global panel_message_id, panel_chat_id, last_panel_text, discord_panel_msg_id
    global total_weverse, total_social, total_tickets, total_buy

    try:
        data, city, dias = get_next_show()
        w_min = minutes_since(last_weverse_check)
        s_min = minutes_since(last_social_check)
        t_min = minutes_since(last_ticket_check)
        b_min = minutes_since(last_buy_check)

        # SEU LAYOUT OBRIGATÓRIO EXCLUSIVO
        text = f"""🪭⊙⊝⊜ARIRANG TOUR⊙⊝⊜🪭

✈️ PRÓXIMAS DATAS
🎫 Data: {data}
📍 Local: {city}
🔔 Faltam {dias} dias.

•°• 👾•°• •°• •°• •°*ATUALIZAÇÕES* •°• •°• •°• •°• •°• 🛸

🟣 Weverse {status_color(last_weverse_check)}
   🎯 Acessos realizados: {total_weverse}
   ⏱ Último rastreio há: {w_min} min

⚪ Redes sociais {status_color(last_social_check)}
   🎯 Acessos realizados: {total_social}
   ⏱ Último rastreio há: {s_min} min

🟠 Ticketmaster {status_color(last_ticket_check)}
   🎯 Acessos realizados: {total_tickets}
   ⏱ Último rastreio há: {t_min} min

🔵 Buyticket {status_color(last_buy_check)}
   🎯 Acessos realizados: {total_buy}
   ⏱ Último rastreio há: {b_min} min
"""

        if text == last_panel_text:
            return
        last_panel_text = text

        # Edição no Telegram
        if bot_ticket and panel_message_id:
            try:
                await bot_ticket.edit_message_text(chat_id=panel_chat_id, message_id=panel_message_id, text=text)
            except: pass

        # Edição no Discord (Apenas o Embed com seu texto)
        canal = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)
        if canal and discord_panel_msg_id:
            try:
                msg = await canal.fetch_message(discord_panel_msg_id)
                await msg.edit(embed=discord.Embed(description=text, color=0x9b59b6))
            except:
                # Caso a mensagem tenha sido apagada, recria no formato correto
                new_msg = await canal.send(embed=discord.Embed(description=text, color=0x9b59b6))
                discord_panel_msg_id = new_msg.id

    except Exception as e:
        print(f"[PAINEL ERROR] {e}")


# =========================
# 14 ALERTAS OFICIAIS
# =========================

async def ticket_reposicao(url, key, found):
    if any(x in str(key) for x in ["28/10", "30/10", "31/10"]):
        msg = f"""🔥*ALERTA DE REPOSIÇÃO*🔥
📅 *Data:* {clean(key)}
🔗 *Link:* {url}
📍 *Setor:* ESGOTADO
🎫 *Categoria:* ESGOTADO
🛡️ *Tipo:* ESGOTADO
✅ *Status:* {resolve_status(found)}
"""
        await send_to_all("reposicao", msg)

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
        await send_to_all("nova_data", msg)

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
        await send_to_all("revenda", msg)

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
        await send_to_all("agenda", msg)

# =========================
# 15 ALERTAS WEVERSE (CORRIGIDO)
# =========================

# Memórias para evitar spam de posts e lives repetidas
LAST_WEVERSE_POST_URL = None
LAST_WEVERSE_LIVE_URL = None

async def weverse_post(url, member_name, title, message_translated, found):
    global LAST_WEVERSE_POST_URL
    
    # Trava Anti-Spam: Ignora se o link for o mesmo do último alerta
    if url == LAST_WEVERSE_POST_URL:
        return
    LAST_WEVERSE_POST_URL = url
    
    emoji = get_member_emoji(member_name)
    msg = f"""🩷*WEVERSE POST*🩷
{emoji} {member_name.upper()} publicou uma mensagem:
📌 {title}
{message_translated}
🔗 {url}
"""
    await send_alert("weverse_post", msg)

async def test_weverse_live(url, member_name, found):
    global LAST_WEVERSE_LIVE_URL
    
    # Trava para Lives: Evita avisar várias vezes sobre a mesma live aberta
    if url == LAST_WEVERSE_LIVE_URL:
        return
    LAST_WEVERSE_LIVE_URL = url
    
    emoji = get_member_emoji(member_name)
    msg = f"""📹*WEVERSE LIVE*📹
{emoji} {member_name.upper()} está ao vivo!
🔗 {url}
"""
    await send_alert("weverse_live", msg)

async def test_weverse_news(url, member_name, message_translated, found):
    global LAST_WEVERSE_POST_URL
    
    if url == LAST_WEVERSE_POST_URL:
        return
    LAST_WEVERSE_POST_URL = url
    
    emoji = get_member_emoji(member_name)
    msg = f"""🚨*WEVERSE NEWS*🚨
{emoji} {member_name.upper()} publicou uma notícia:
📌 {message_translated}
🔗 {url}
"""
    await send_alert("weverse_news", msg)

async def test_weverse_media(url, member_name, title, message_translated, found):
    global LAST_WEVERSE_POST_URL
    
    if url == LAST_WEVERSE_POST_URL:
        return
    LAST_WEVERSE_POST_URL = url
    
    emoji = get_member_emoji(member_name)
    msg = f"""📀 WEVERSE MÍDIA📀
{emoji} {member_name.upper()} publicou uma nova mídia!
⭐️ {title}
{message_translated}
🔗 {url}
"""
    await send_alert("weverse_media", msg)

# =========================
# 16 ALERTAS INSTAGRAM (CORRIGIDO)
# =========================

# Memória para evitar repetição do último post/story
LAST_INSTA_POST_LINK = None
LAST_INSTA_STORY_LINK = None

async def instagram_post(url, member_name, title, found):
    global LAST_INSTA_POST_LINK
    
    # Trava Anti-Spam
    if url == LAST_INSTA_POST_LINK:
        return
    LAST_INSTA_POST_LINK = url
    
    emoji, name = format_member(member_name)
    msg = f"""🌟*INSTAGRAM POST*🌟
{emoji} {name} postou uma foto!
🔗 {url}
"""
    await send_alert("instagram_post", msg)

async def instagram_reel(url, member_name, title, found):
    global LAST_INSTA_POST_LINK # Reels e Posts compartilham a mesma trava
    
    if url == LAST_INSTA_POST_LINK:
        return
    LAST_INSTA_POST_LINK = url
    
    emoji, name = format_member(member_name)
    msg = f"""🎬*INSTAGRAM REELS*🎬
{emoji} {name} postou um reels!
🔗 {url}
"""
    await send_alert("instagram_reels", msg)

async def instagram_story(url, member_name, title, found):
    global LAST_INSTA_STORY_LINK
    
    if url == LAST_INSTA_STORY_LINK:
        return
    LAST_INSTA_STORY_LINK = url
    
    emoji, name = format_member(member_name)
    msg = f"""🫧*INSTAGRAM STORIES*🫧
{emoji} {name} atualizou os stories!
🔗 {url}
"""
    await send_alert("instagram_stories", msg)

async def instagram_live(url, member_name, title, found):
    emoji, name = format_member(member_name)
    msg = f"""🎥*INSTAGRAM LIVE*🎥
{emoji} {name} está ao vivo!
🔗 {url}
"""
    await send_alert("instagram_live", msg)


# =========================
# 17 ALERTAS TIKTOK (CORRIGIDO)
# =========================

# Memória para evitar que o mesmo post repita (Spam)
LAST_TIKTOK_LINK = None

async def tiktok_post(url, member_name, title, found):
    global LAST_TIKTOK_LINK
    
    # CORREÇÃO DO LINK: Garante que o underline não seja removido
    # O link oficial deve ser sempre respeitado
    link_correto = "https://www.tiktok.com/@bts_official_bighit"
    
    # Se a URL recebida não tiver o link completo, nós montamos
    if "video/" in url:
        video_id = url.split("video/")[1].split("?")[0]
        final_url = f"{link_correto}/video/{video_id}"
    else:
        final_url = link_correto

    # TRAVA ANTI-SPAM: Só envia se o link for diferente do último
    if final_url == LAST_TIKTOK_LINK:
        return
    
    LAST_TIKTOK_LINK = final_url
    emoji = get_member_emoji(member_name)
    
    msg = f"""🎵*TIKTOK POST*🎵
{emoji} {member_name.upper()} postou um vídeo!
🔗 *Link:* {final_url}
"""
    # Envia para o roteador oficial do Bloco 21
    await send_alert("tiktok_post", msg)

async def tiktok_live(url, member_name, title, found):
    emoji = get_member_emoji(member_name)
    msg = f"""🎥*TIKTOK LIVE*🎥
{emoji} {member_name.upper()} está ao vivo no TikTok!
🔗 *Link:* https://www.tiktok.com/@bts_official_bighit/live
"""
    await send_alert("tiktok_live", msg)

# =============================================================
# 18 SISTEMA DE TESTE SOB DEMANDA (/TESTE)
# =============================================================

TEST_HEADER = "⚠️ TESTE ⚠️"

async def run_full_test():
    """
    DISPARADOR ÚNICO: 
    Esta função só é chamada quando o usuário digita /teste.
    """
    # Links e dados fictícios para a simulação completa
    t_link = "https://www.ticketmaster.com.br/arirang-test"
    b_link = "https://buyticketbrasil.com/evento-teste"
    
    # 1. Testes de Tickets e Agenda
    await test_ticket_reposicao(t_link, "28/10/2026", True)
    await asyncio.sleep(1)
    await test_ticket_nova_data(t_link, "30/10/2026", True)
    await asyncio.sleep(1)
    await test_buy_revenda(b_link, "28/10/2026", True)
    await asyncio.sleep(1)
    await test_agenda({"date": "28/10/2026", "city": "São Paulo", "country": "Brasil"})
    
    # 2. Testes de Weverse
    await asyncio.sleep(1)
    await test_weverse_post(t_link, "bts", "Update", "Conteúdo Teste", True)
    await test_weverse_live(t_link, "jungkook", True)
    await test_weverse_news(t_link, "rm", "msg", True)
    await test_weverse_media(t_link, "v", "title", "msg", True)
    
    # 3. Testes de Redes Sociais
    await asyncio.sleep(1)
    await test_instagram_post(t_link, "bts", "post", True)
    await test_instagram_reel(t_link, "bts", "reel", True)
    await test_instagram_story(t_link, "bts", "story", True)
    await test_instagram_live(t_link, "bts", "live", True)
    await test_tiktok_post(t_link, "bts", "video", True)
    await test_tiktok_live(t_link, "bts", "live", True)

# --- FUNÇÕES DE LAYOUT PARA O TESTE ---

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
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

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
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

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
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

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
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

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
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

async def test_weverse_live(url, member_name, found):
    emoji = get_member_emoji(member_name)
    msg = f"""{TEST_HEADER}

📹*WEVERSE LIVE*📹
{emoji} {member_name.upper()} está ao vivo!
🔗 {url}
👀 *Viewers:* 1.2M assistindo
⏱️ *Duração:* 00:18:42
"""
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

async def test_weverse_news(url, member_name, message_translated, found):
    emoji = get_member_emoji(member_name)
    msg = f"""{TEST_HEADER}

🚨*WEVERSE NEWS*🚨
{emoji} {member_name.upper()} publicou uma notícia:
📌 *Atualização:* novo conteúdo exclusivo liberado
💬 "Special announcement coming soon"
🔗 {url}
"""
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

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
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

async def test_instagram_post(url, member_name, title, found):
    emoji, name = format_member(member_name)
    msg = f"""{TEST_HEADER}

🌟*INSTAGRAM POST*🌟
{emoji} {name} postou uma foto!
📌 *Legenda:* “Back on stage 💜”
❤️ *Likes:* 8.9M
🔗 {url}
"""
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

async def test_instagram_reel(url, member_name, title, found):
    emoji, name = format_member(member_name)
    msg = f"""{TEST_HEADER}

🎬*INSTAGRAM REELS*🎬
{emoji} {name} postou um reels!
🎵 *Música:* trending audio #1 global
👀 *Views:* 12.4M
🔗 {url}
"""
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

async def test_instagram_story(url, member_name, title, found):
    emoji, name = format_member(member_name)
    msg = f"""{TEST_HEADER}

🫧*INSTAGRAM STORIES*🫧
{emoji} {name} atualizou os stories!
📸 *Tipo:* bastidores da turnê
⏳ *Duração:* 24h
🔗 {url}
"""
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

async def test_instagram_live(url, member_name, title, found):
    emoji, name = format_member(member_name)
    msg = f"""{TEST_HEADER}

🎥*INSTAGRAM LIVE*🎥
{emoji} {name} está ao vivo!
👀 *Viewers:* 780k
💬 *Chat:* ativo
🔗 {url}
"""
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

async def test_tiktok_post(url, member_name, title, found):
    emoji = get_member_emoji(member_name)
    msg = f"""{TEST_HEADER}

🎵*TIKTOK POST*🎵
{emoji} {member_name.upper()} postou um vídeo!
🔥 *Views:* 6.7M em 2h
❤️ *Likes:* 1.1M
🔗 {url}
"""
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

async def test_tiktok_live(url, member_name, title, found):
    emoji = get_member_emoji(member_name)
    msg = f"""{TEST_HEADER}

🎥*TIKTOK LIVE*🎥
{emoji} {member_name.upper()} está ao vivo no TikTok!
👀 *Viewers:* 540k
💬 *Chat:* explosivo
🔗 {url}
"""
    if bot_ticket: await bot_ticket.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")


# =============================================================
# 19 COMANDOS DE INTERAÇÃO (TELEGRAM + DISCORD)
# =============================================================

# --- HANDLER TELEGRAM (PV EXCLUSIVO) ---
async def handle_commands_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processa comandos enviados diretamente ao bot no Telegram.
    """
    if not update.message or not update.message.text:
        return
        
    # Restringe comandos ao seu privado para segurança
    if update.message.chat.type != "private":
        return
    
    command = update.message.text.lower().strip()

    if command == "/teste":
        await update.message.reply_text("🧪 [TELEGRAM] Iniciando sequência de testes detalhados...")
        await run_full_test()
        await update.message.reply_text("✅ Sequência de testes finalizada.")

    elif command == "/ping":
        await update.message.reply_text("🏓 Pong! O sistema Arirang está operacional.")

    elif command == "/status":
        uptime = get_uptime()
        await update.message.reply_text(f"📊 *STATUS DO SISTEMA*\n\n⏱ Uptime: {uptime}\n🛰️ Monitoramento: Ativo", parse_mode="Markdown")

# --- COMANDO DISCORD (SLASH COMMAND) ---
@bot_discord.tree.command(name="teste", description="Executa a sequência completa de alertas de teste")
async def discord_teste(interaction: discord.Interaction):
    """
    Comando slash (/) para o Discord.
    """
    await interaction.response.send_message("🧪 [DISCORD] Iniciando sequência de testes detalhados...")
    
    try:
        await run_full_test()
        await interaction.followup.send("✅ Testes disparados com sucesso para os canais oficiais.")
    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao executar testes: {e}")

@bot_discord.tree.command(name="ping", description="Verifica se o bot está online")
async def discord_ping(interaction: discord.Interaction):
    latency = round(bot_discord.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latência: {latency}ms")

# =============================================================
# 20 SAFE BOOT E MOTOR DE MONITORAMENTO
# =============================================================

async def safe_boot():
    """
    Garante que o anúncio de inicialização (Boot) ocorra apenas uma vez 
    e que o painel seja criado corretamente.
    """
    global panel_initialized
    
    if panel_initialized:
        return

    try:
        # Envia a mensagem de BOOT (Bloco 02/12)
        await send_boot()
        print("[SISTEMA] Mensagem de Boot enviada ao Telegram.")
        
        # Marca como inicializado para não repetir se o bot reconectar
        panel_initialized = True
        
    except Exception as e:
        print(f"[SAFE_BOOT ERROR] Falha ao inicializar sistema: {e}")

async def monitor_loop():
    """
    Motor principal: varre os sites em ciclos infinitos com intervalos de segurança.
    """
    # Espera o bot do Discord estar 100% pronto antes de começar
    await bot_discord.wait_until_ready()
    
    # Executa o boot inicial
    await safe_boot()
    
    print("[MONITOR] Ciclo de varredura iniciado com sucesso.")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # 1. Checa Ticketmaster
                await check_ticketmaster(session)
                await asyncio.sleep(5) # Pausa técnica

                # 2. Checa BuyTicket
                await check_buyticket(session)
                await asyncio.sleep(5)

                # 3. Checa Weverse
                await check_weverse(session)
                await asyncio.sleep(5)

                # 4. Checa Redes Sociais (Insta/TikTok)
                await check_social(session)

                # 5. Intervalo Geral antes da próxima rodada completa
                # Ajustado para 30 segundos para manter o bot ágil mas seguro
                await asyncio.sleep(30)

            except Exception as e:
                print(f"[MONITOR ERROR] Ocorreu uma falha no ciclo: {e}")
                # Em caso de erro grave, espera 10 segundos antes de tentar de novo
                await asyncio.sleep(10)

# =========================
# 21 ALERT ENGINE (REVISADO PARA O SEU ID)
# =========================

ALERT_LOCK = asyncio.Lock()

async def send_discord(channel_id, message):
    """Envia mensagens para canais específicos, garantindo o uso do ID correto."""
    try:
        # O Discord exige que o ID seja int. O seu ID: 1494667029150695625
        channel = bot_discord.get_channel(int(channel_id))
        if channel:
            await channel.send(message)
        else:
            # Tenta buscar o canal se ele não estiver no cache
            channel = await bot_discord.fetch_channel(int(channel_id))
            if channel:
                await channel.send(message)
            else:
                print(f"[DISCORD ERROR] Não localizei o canal {channel_id}.")
    except Exception as e:
        print(f"[DISCORD SEND ERROR] {e}")

async def update_panel_discord(text):
    """
    Envia a atualização do painel especificamente para o seu ID 1494667029150695625.
    """
    try:
        # Se você quiser que ele edite a mensagem em vez de mandar novas, 
        # precisaríamos salvar o ID da mensagem anterior. 
        # Por enquanto, ele enviará o status atualizado lá.
        await send_discord(1494667029150695625, text)
    except Exception as e:
        print(f"[DISCORD PANEL ERROR] {e}")

async def send_alert(alert_type, message):
    async with ALERT_LOCK:
        # --- TELEGRAM ---
        if bot_ticket and CHAT_ID:
            try:
                await bot_ticket.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
            except:
                pass # Silencia o Chat Not Found para não sujar o log

        # --- DISCORD (ROTEAMENTO) ---
        loop = asyncio.get_running_loop()
        
        # Roteamento baseado no tipo
        if alert_type in ["ticket", "reposicao", "nova_data", "revenda"]:
            loop.create_task(send_discord(DISCORD_TICKETS_CHANNEL_ID, message))
        
        elif alert_type in ["weverse_post", "weverse_live"]:
            loop.create_task(send_discord(DISCORD_WEVERSE_CHANNEL_ID, message))
            
        elif "instagram" in alert_type or "tiktok" in alert_type:
            loop.create_task(send_discord(DISCORD_SOCIAL_CHANNEL_ID, message))
            
        # SEMPRE envia uma cópia resumida para o seu canal de PAINEL (ID 625)
        loop.create_task(update_panel_discord(f"🔔 **Novo Alerta:** {alert_type}"))

# =========================
# 22 FETCH UNIVERSAL
# =========================

async def fetch(session, url):
    """Download seguro com timeout e headers para evitar bloqueios."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        async with session.get(url, headers=headers, timeout=20) as response:
            if response.status != 200:
                return None
            return await response.text()
    except Exception:
        return None

# =========================
# 23 CHECKS (MONITORAMENTO ATIVO)
# =========================

async def check_ticketmaster(session):
    global last_ticket_check, total_tickets
    if 'TICKET_LINKS' not in globals(): return
    
    for url in TICKET_LINKS:
        html = await fetch(session, url)
        if html and is_new(url, html):
            found = "esgotado" not in html.lower()
            total_tickets += 1
            # Chama o alerta detalhado do Bloco 14
            await ticket_reposicao(url, url, found)
            last_ticket_check = time.time()
            await update_panel()

async def check_buyticket(session):
    global last_buy_check, total_buy
    if 'BUY_LINKS' not in globals(): return
    
    for url in BUY_LINKS:
        html = await fetch(session, url)
        if html and is_new(url, html):
            found = "esgotado" not in html.lower()
            total_buy += 1
            # Chama o alerta detalhado do Bloco 14
            await buy_revenda(url, url, found)
            last_buy_check = time.time()
            await update_panel()

async def check_weverse(session):
    global last_weverse_check, total_weverse
    if 'WEVERSE_LINKS' not in globals(): return
    
    for url in WEVERSE_LINKS:
        html = await fetch(session, url)
        if html and is_new(url, html):
            total_weverse += 1
            # Chama o alerta detalhado do Bloco 15
            await weverse_post(url, "bts", "Update Detectado", "O conteúdo da página mudou.", True)
            last_weverse_check = time.time()
            await update_panel()

async def check_social(session):
    global last_social_check, total_social
    insta = list(INSTAGRAM_LINKS.items()) if 'INSTAGRAM_LINKS' in globals() else []
    ttok = list(TIKTOK_LINKS.items()) if 'TIKTOK_LINKS' in globals() else []
    all_links = insta + ttok
    
    for member, url in all_links:
        html = await fetch(session, url)
        if html and is_new(url, html):
            total_social += 1
            if "instagram" in url:
                await instagram_post(url, member, "Update", True)
            elif "tiktok" in url:
                await tiktok_post(url, member, "Update", True)
            last_social_check = time.time()
            await update_panel()
# =========================
# 24 LOOP PRINCIPAL (MOTOR)
# =========================

async def monitor_loop():
    """
    Executa a varredura contínua. 
    Nota: monitor_loop já foi definido no Bloco 20, 
    esta versão reafirma a ordem de execução.
    """
    await bot_discord.wait_until_ready()
    await safe_boot() # Dispara Boot e Painel uma única vez
    
    print("[MONITOR] Loop de varredura iniciado.")

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await check_ticketmaster(session)
                await asyncio.sleep(2)
                await check_buyticket(session)
                await asyncio.sleep(2)
                await check_weverse(session)
                await asyncio.sleep(2)
                await check_social(session)

                # Pausa de 30 segundos entre ciclos para evitar bans
                await asyncio.sleep(30)
            except Exception as e:
                print(f"[MONITOR ERROR] {e}")
                await asyncio.sleep(10)

# =========================
# 26 DISCORD: EVENTO ON_READY
# =========================

@bot_discord.event
async def on_ready():
    print(f"✅ Logado no Discord como {bot_discord.user}")
    
    # AJUSTE AQUI: Mudando a frase de exibição
    await bot_discord.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, 
            name="Em tournê - ouvindo: Arirang 🪭"  
        ),
        status=discord.Status.online
    )

    try:
        synced = await bot_discord.tree.sync()
        print(f"✅ {len(synced)} comandos slash sincronizados.")
    except Exception as e:
        print(f"❌ Erro na sincronização: {e}")

# =========================
# 27 INICIALIZAÇÃO FINAL (MAIN)
# =========================

async def main():
    """
    Ponto de entrada principal do sistema Arirang.
    """
    # 1. Inicia o monitor em segundo plano como uma Task
    asyncio.create_task(monitor_loop())
    
    # 2. Configura Handlers do Telegram (python-telegram-bot v20+)
    # O handler 'handle_commands_telegram' gerencia o /teste, /ping e /status
    if 'application' in globals():
        from telegram.ext import CommandHandler
        
        application.add_handler(CommandHandler("teste", handle_commands_telegram))
        application.add_handler(CommandHandler("ping", handle_commands_telegram))
        application.add_handler(CommandHandler("status", handle_commands_telegram))
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        print("[SISTEMA] Telegram operativo.")

    # 3. Inicia o Discord (Este comando é bloqueante, mantendo o script vivo)
    try:
        # Puxa o token das variáveis de ambiente ou do seu Bloco de Configurações
        token = os.getenv('DISCORD_TOKEN') or DISCORD_TOKEN
        await bot_discord.start(token)
    except Exception as e:
        print(f"[FATAL] Erro ao iniciar bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Finalização limpa ao pressionar Ctrl+C
        print("\n🛸 Desligando motores e recolhendo Wootteo...")
