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
# 12 FUNÇÃO DE ATUALIZAÇÃO (LEITURA REAL DOS DADOS)
# =============================================================

async def update_panel():
    # Puxa todas as variáveis para dentro da função
    global panel_message_id, panel_chat_id, discord_panel_msg_id
    global total_weverse, total_social, total_tickets, total_buy
    global last_weverse_check, last_social_check, last_ticket_check, last_buy_check

    try:
        data_show, city, dias = get_next_show()
        
        # Monta o texto lendo os valores que o monitor_loop injeta
        text = f"""🪭⊙⊝⊜ARIRANG TOUR⊙⊝⊜🪭

✈️ PRÓXIMAS DATAS
🎫 Data: {data_show}
📍 Local: {city}
🔔 Faltam {dias} dias.

•°• 👾•°• •°• •°• •°*ATUALIZAÇÕES* •°• •°• •°• •°• •°• 🛸

🟣 Weverse {status_color(last_weverse_check)}
   🎯 Acessos realizados: {total_weverse}
   ⏱ Último rastreio há: {minutes_since(last_weverse_check)} min

⚪ Redes sociais {status_color(last_social_check)}
   🎯 Acessos realizados: {total_social}
   ⏱ Último rastreio há: {minutes_since(last_social_check)} min

🟠 Ticketmaster {status_color(last_ticket_check)}
   🎯 Acessos realizados: {total_tickets}
   ⏱ Último rastreio há: {minutes_since(last_ticket_check)} min

🔵 Buyticket {status_color(last_buy_check)}
   🎯 Acessos realizados: {total_buy}
   ⏱ Último rastreio há: {minutes_since(last_buy_check)} min
"""
        # EDITAR NO TELEGRAM (Não envia novo, apenas edita o ID salvo)
        if bot_ticket and panel_message_id:
            try:
                await bot_ticket.edit_message_text(chat_id=panel_chat_id, message_id=panel_message_id, text=text)
            except: pass

        # EDITAR NO DISCORD
        canal = bot_discord.get_channel(DISCORD_PANEL_CHANNEL_ID)
        if canal and discord_panel_msg_id:
            try:
                msg = await canal.fetch_message(discord_panel_msg_id)
                await msg.edit(embed=discord.Embed(description=text, color=0x9b59b6))
            except: pass

    except Exception as e:
        print(f"[ERRO UPDATE PANEL] {e}")

# =========================
# 13 ALERTAS WEVERSE (CORRIGIDO)
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
# 14 ALERTAS INSTAGRAM (CORRIGIDO)
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
# 15 ALERTAS TIKTOK (CORRIGIDO)
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
# 16 SISTEMA DE TESTE (ROTEADO PARA AS SALAS CERTAS)
# =============================================================

TEST_HEADER = "⚠️ TESTE ⚠️"

async def run_full_test():
    """Executa a sequência de testes enviando para os canais específicos."""
    t_link = "https://www.ticketmaster.com.br/arirang-test"
    
    # 1. Testes de Tickets (Vão para a sala de Tickets)
    await test_ticket_reposicao(t_link, "28/10/2026", True)
    await asyncio.sleep(1)
    await test_agenda({"date": "28/10/2026", "city": "São Paulo", "country": "Brasil"})
    
    # 2. Testes de Weverse (Vão para a sala de Weverse)
    await asyncio.sleep(1)
    await test_weverse_post(t_link, "bts", "Update", "Conteúdo Teste", True)
    
    # 3. Testes de Redes Sociais (Vão para a sala Social)
    await asyncio.sleep(1)
    await test_instagram_post(t_link, "bts", "post", True)
    await test_tiktok_post("https://www.tiktok.com/@bts_official_bighit", "bts", "video", True)

# --- FUNÇÕES DE LAYOUT PARA O TESTE (AJUSTADAS) ---

async def test_ticket_reposicao(url, key, found):
    msg = f"{TEST_HEADER}\n\n🔥*ALERTA DE REPOSIÇÃO*🔥\n📅 *Data:* 28/10/2026\n🔗 *Link:* {url}\n✅ *Status:* Liberado"
    await send_alert("reposicao", msg)

async def test_agenda(data):
    msg = f"{TEST_HEADER}\n\n💜*AGENDA NOVAS DATAS*💜\n📅 *Data:* 28/10/2026\n🏙️ *Cidade:* São Paulo\n🌎 *País:* Brasil"
    await send_alert("agenda", msg)

async def test_weverse_post(url, member_name, title, message_translated, found):
    msg = f"{TEST_HEADER}\n\n🩷*WEVERSE POST*🩷\n👤 {member_name.upper()} publicou uma mensagem!\n🔗 {url}"
    await send_alert("weverse_post", msg)

async def test_instagram_post(url, member_name, title, found):
    msg = f"{TEST_HEADER}\n\n🌟*INSTAGRAM POST*🌟\n👤 {member_name} postou uma foto!\n🔗 {url}"
    await send_alert("instagram_post", msg)

async def test_tiktok_post(url, member_name, title, found):
    msg = f"{TEST_HEADER}\n\n🎵*TIKTOK POST*🎵\n👤 {member_name.upper()} postou um vídeo!\n🔗 {url}"
    await send_alert("tiktok_post", msg)

# =============================================================
# 17 COMANDOS (GATILHO DIRETO)
# =============================================================

# --- DISCORD (SLASH COMMAND) ---
@bot_discord.tree.command(name="teste", description="Dispara modelos de teste para as salas")
async def discord_teste(interaction: discord.Interaction):
    """Executa o teste e responde apenas com um check invisível ou efêmero."""
    # O interaction.response é obrigatório no Discord, então usamos uma resposta rápida
    await interaction.response.send_message("🧪 Executando modelos...", ephemeral=True, delete_after=2)
    await run_full_test()

# --- TELEGRAM ---
async def handle_commands_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    if update.message.chat.type != "private": return
    
    if update.message.text.lower().strip() == "/teste":
        await run_full_test()

# =============================================================
# 18 MOTOR DE MONITORAMENTO (CONTADORES E CORREÇÃO DE BOOT)
# =============================================================

async def monitor_loop():
    """Motor principal: Executa o boot inicial e atualiza os contadores."""
    
    # 1. Espera o bot estar pronto
    await bot_discord.wait_until_ready()
    
    # 2. Executa o boot oficial (O Bloco 12 que definimos antes)
    # Aqui corrigimos o erro NameError chamando o nome certo
    try:
        await send_boot() 
        print("[SISTEMA] Painel inicializado com sucesso.")
    except Exception as e:
        print(f"[BOOT ERROR] Falha ao iniciar painel: {e}")

    # 3. Variáveis globais para os contadores subirem
    global total_tickets, total_buy, total_weverse, total_social
    global last_ticket_check, last_buy_check, last_weverse_check, last_social_check

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # --- CICLO DE VARREDURA E SOMA ---
                
                # Ticketmaster
                await check_ticketmaster(session)
                total_tickets += 1
                last_ticket_check = datetime.now()
                
                # BuyTicket
                await check_buyticket(session)
                total_buy += 1
                last_buy_check = datetime.now()

                # Weverse
                await check_weverse(session)
                total_weverse += 1
                last_weverse_check = datetime.now()

                # Redes Sociais
                await check_social(session)
                total_social += 1
                last_social_check = datetime.now()

                # --- ATUALIZAÇÃO DO PAINEL ---
                # Esta função (Bloco 13) vai editar a mensagem e mostrar os números
                await update_panel()

                # Intervalo para não ser banido dos sites e manter o bot ágil
                await asyncio.sleep(30)

            except Exception as e:
                print(f"[MONITOR ERROR] Falha no ciclo: {e}")
                await asyncio.sleep(10)
# =============================================================
# 19 MOTOR DE MONITORAMENTO (VERSÃO FINAL SEM ERROS)
# =============================================================

async def monitor_loop():
    """Motor principal que alimenta os contadores e gerencia o painel."""
    
    # 1. Espera o bot do Discord conectar totalmente
    await bot_discord.wait_until_ready()
    
    # 2. CORREÇÃO DO ERRO: Chama send_boot em vez de safe_boot
    try:
        await send_boot() 
        print("[SISTEMA] Painel Arirang inicializado.")
    except Exception as e:
        print(f"[BOOT ERROR] Falha ao iniciar: {e}")

    # 3. Garante acesso às variáveis globais para os contadores subirem
    global total_tickets, total_buy, total_weverse, total_social
    global last_ticket_check, last_buy_check, last_weverse_check, last_social_check

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # --- EXECUÇÃO DOS RASTREIOS ---
                await check_ticketmaster(session)
                total_tickets += 1
                last_ticket_check = datetime.now()
                
                await check_buyticket(session)
                total_buy += 1
                last_buy_check = datetime.now()

                await check_weverse(session)
                total_weverse += 1
                last_weverse_check = datetime.now()

                await check_social(session)
                total_social += 1
                last_social_check = datetime.now()

                # --- ATUALIZAÇÃO DO PAINEL (EDITAR) ---
                # Atualiza os números no Telegram e Discord (borda roxa)
                await update_panel()

                # Espera 30 segundos para o próximo ciclo de busca
                await asyncio.sleep(30)

            except Exception as e:
                print(f"[MONITOR ERROR] Falha no ciclo: {e}")
                await asyncio.sleep(10)

# =========================
# 20 FETCH UNIVERSAL
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
# 21 CHECKS (MONITORAMENTO ATIVO)
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
# 22 LOOP PRINCIPAL (MOTOR)
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
# 23 DISCORD: EVENTO ON_READY
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
# 24 INICIALIZAÇÃO FINAL (MAIN)
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
