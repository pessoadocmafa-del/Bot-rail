import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import re
import datetime

TOKEN = os.environ["DISCORD_TOKEN"]

# =========================
# CONFIG
# =========================
LOG_CHANNEL_ID = 1506671577931055255
CALL_STAFF_ROLE = 1507089576462778499

WL_ROLE_ID = 1506446576267038821
WL_REMOVE_ROLE_ID = 1506446577261084733

CARGOS_PERMITIDOS = [
    1506446522714161275,
    1506446521607131198,
    1506446520692637717,
    1506446519677489272,
    1506446518482243656,
    1506446517614018730,
    1506446511960101007,
    1506446510798274661
]

WHITELIST_QUESTIONS = [
    "Qual nome do seu personagem?",
    "Qual sua idade e a do personagem?",
    "O que é RDM e VDM?",
    "Você já fez RP antes?",
    "Algum recado?"
]

user_ids = {}
ticket_counter = 0

# =========================
# HORÁRIO
# =========================

def horario_ok():
    agora = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    return 11 <= agora.hour < 23

# =========================
# STAFF CHECK
# =========================
def staff(interaction: discord.Interaction):
    return any(r.id in CARGOS_PERMITIDOS for r in interaction.user.roles)

# =========================
# BOT
# =========================
intents = discord.Intents.default()
intents.members = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

# =========================
# ANÚNCIO
# =========================
@bot.tree.command(name="anuncio")
@app_commands.describe(
    titulo="Título do anúncio",
    mensagem="Mensagem do anúncio"
)
async def anuncio(
    interaction: discord.Interaction,
    titulo: str,
    mensagem: str
):

    if not horario_ok():
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ ERRO",
                description="⛔ Fora do horário (11h–23h UTC-3).",
                color=discord.Color.red()
            ),
            ephemeral=True
        )

    if not staff(interaction):
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ ERRO",
                description="Sem permissão.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )

    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title=titulo,
        description=mensagem,
        color=discord.Color.red()
    )

    await interaction.channel.send(embed=embed)

    await interaction.followup.send(
        embed=discord.Embed(
            title="✅ ANÚNCIO ENVIADO",
            description="O anúncio foi enviado com sucesso.",
            color=discord.Color.green()
        ),
        ephemeral=True
    )

# =========================
# RUN
# =========================
bot.run(TOKEN)
