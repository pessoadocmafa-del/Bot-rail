import os
import discord
from discord.ext import commands
from discord import app_commands
import datetime

# =========================
# TOKEN
# =========================
TOKEN = os.environ["DISCORD_TOKEN"]

# =========================
# CONFIG
# =========================
LOG_CHANNEL_ID = 1506671577931055255
CALL_STAFF_ROLE = 1507089576462778499

# ⚠️ CORRIGIDO: agora é ID normal
CARGOS_PERMITIDOS = [
    141503254964
]

WL_ROLE_ID = 1506446576267038821
WL_REMOVE_ROLE_ID = 1506446577261084733

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
# HORÁRIO PERMITIDO
# =========================
def horario_ok():
    agora = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    return 11 <= agora.hour < 23

# =========================
# STAFF CHECK (corrigido)
# =========================
def staff(interaction: discord.Interaction):
    return any(user.id in CARGOS_PERMITIDOS for role in interaction.user.roles)

# =========================
# BOT SETUP
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
# /ANUNCIO
# =========================
@bot.tree.command(name="anuncio")
@app_commands.describe(
    titulo="Título do anúncio",
    mensagem="Mensagem do anúncio"
)
async def anuncio(interaction: discord.Interaction, titulo: str, mensagem: str):

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

    embed = discord.Embed(
        title=titulo,
        description=mensagem,
        color=discord.Color.red()
    )

    await interaction.channel.send(embed=embed)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="✅ SUCESSO",
            description="Anúncio enviado com sucesso.",
            color=discord.Color.green()
        ),
        ephemeral=True
    )

# =========================
# /POSICAO
# =========================
@bot.tree.command(name="posicao")
@app_commands.describe(
    nick="Nick do Roblox",
    posicao="Posição do jogador",
    numero="Número do jogador"
)
async def posicao(interaction: discord.Interaction, nick: str, posicao: str, numero: int):

    if not nick.strip():
        return await interaction.response.send_message("Nick inválido.", ephemeral=True)

    if not posicao.strip():
        return await interaction.response.send_message("Posição inválida.", ephemeral=True)

    if numero <= 0:
        return await interaction.response.send_message("Número inválido.", ephemeral=True)

    embed = discord.Embed(
        title="📌 REGISTRO DE POSIÇÃO",
        color=discord.Color.blue()
    )

    embed.add_field(name="👤 Discord", value=interaction.user.mention, inline=False)
    embed.add_field(name="🎮 Nick Roblox", value=nick, inline=True)
    embed.add_field(name="📍 Posição", value=posicao, inline=True)
    embed.add_field(name="🔢 Número", value=str(numero), inline=True)

    await interaction.response.send_message(embed=embed)

# =========================
# START BOT
# =========================
bot.run(TOKEN)
