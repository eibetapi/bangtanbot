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
# 22 DISCORD ULTRA SAFE (CORRIGIDO DEFINITIVO)
# =========================

# ⚠️ IMPORTANTE: NÃO DUPLICAR on_ready
# (fica APENAS UM evento no arquivo inteiro)

if not hasattr(bot_discord, "COMMANDS_LOADED"):
    bot_discord.COMMANDS_LOADED = False


async def register_discord_commands():

    if bot_discord.COMMANDS_LOADED:
        return

    if bot_discord.tree.get_command("teste"):
        bot_discord.COMMANDS_LOADED = True
        return

    @bot_discord.tree.command(
        name="teste",
        description="Dispara alertas reais do sistema"
    )
    async def teste(interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        try:
            await run_full_test_discord()

            embed = discord.Embed(
                title="🧪 TESTE ARIRANG SYSTEM",
                description="Execução completa de alertas simulados",
                color=0x8A2BE2
            )

            canais = [
                DISCORD_TICKETS_CHANNEL_ID,
                DISCORD_WEVERSE_CHANNEL_ID,
                DISCORD_SOCIAL_CHANNEL_ID
            ]

            for cid in canais:
                channel = interaction.guild.get_channel(cid)
                if channel:
                    await channel.send(embed=embed)

            await interaction.followup.send("✅ Teste executado com sucesso.", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro no teste: {e}", ephemeral=True)

    bot_discord.COMMANDS_LOADED = True
    print("[DISCORD] Comandos registrados com sucesso.")


# =========================
# ON READY (ÚNICO E LIMPO)
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
        await register_discord_commands()
        synced = await bot_discord.tree.sync()
        print(f"[DISCORD] Slash commands sincronizados: {len(synced)}")

    except Exception as e:
        print(f"[DISCORD ERROR SYNC] {e}")
