import os
import discord
from discord.ext import commands
from discord import app_commands
import random
import re
import datetime
import asyncio

TOKEN = os.environ["DISCORD_TOKEN"]

# =========================
# WHITELIST CONFIG
# =========================
WHITELIST_QUESTIONS = []
WHITELIST_LOG_CHANNEL = None
WHITELIST_PANEL_CHANNEL = None
wl_responses = {}

# =========================
# INTENTS
# =========================
intents = discord.Intents.default()
intents.members = True

# =========================
# CARGOS PERMITIDOS
# =========================
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

user_ids = {}

def tem_cargo_permitido(interaction: discord.Interaction):
    return any(role.id in CARGOS_PERMITIDOS for role in interaction.user.roles)

# =========================
# HORÁRIO (UTC-3 11h-23h)
# =========================
def horario_permitido():
    hora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).hour
    return 11 <= hora < 23

async def verificar_horario():
    await bot.wait_until_ready()
    while True:
        if not horario_permitido():
            print("Fora do horário 11h–23h. Desligando bot...")
            await bot.close()
            break
        await asyncio.sleep(60)

# =========================
# BOT
# =========================
class MyBot(commands.Bot):
    async def setup_hook(self):
        self.loop.create_task(verificar_horario())
        await self.tree.sync()

bot = MyBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

# =========================
# /PEDIRID
# =========================
@bot.tree.command(name="pedirid", description="Gera um ID para roleplay")
async def pedirid(interaction: discord.Interaction):

    if not horario_permitido():
        return await interaction.response.send_message(
            "⛔ Fora do horário (11h–23h).",
            ephemeral=True
        )

    uid = interaction.user.id

    if uid in user_ids:
        old_id = user_ids[uid]

        embed = discord.Embed(
            title="❌ Erro na geração",
            description=(
                f"Você já possui um ID.\n\n"
                f"Seu ID antigo é **{old_id}**."
            ),
            color=discord.Color.red()
        )

        return await interaction.response.send_message(embed=embed, ephemeral=True)

    numero_id = random.randint(1000, 9999)
    user_ids[uid] = numero_id

    try:
        nome = interaction.user.display_name
        nome = re.sub(r"^\d{4}\s*\|\s*", "", nome).strip()

        await interaction.user.edit(nick=f"{numero_id} | {nome}")

        embed = discord.Embed(
            title="✅ ID gerado com sucesso!",
            description=(
                f"🆔 Seu novo ID é: **{numero_id}**\n"
                f"Guarde ele com cuidado."
            ),
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Sem permissão para alterar nickname.",
            ephemeral=True
        )

# =========================
# /ANUNCIO
# =========================
@bot.tree.command(name="anuncio", description="Faz um anúncio")
@app_commands.describe(mensagem="Mensagem do anúncio")
async def anuncio(interaction: discord.Interaction, mensagem: str):

    if not horario_permitido():
        return await interaction.response.send_message(
            "⛔ Fora do horário.",
            ephemeral=True
        )

    if not tem_cargo_permitido(interaction):
        return await interaction.response.send_message(
            "❌ Sem permissão.",
            ephemeral=True
        )

    embed = discord.Embed(
        description=mensagem,
        color=discord.Color.red()
    )

    await interaction.response.send_message(embed=embed)

# =========================
# WHITELIST MODAL
# =========================
from discord.ui import View, Button, Modal, TextInput

class WhitelistModal(Modal, title="Whitelist RP"):
    def __init__(self):
        super().__init__()

        self.inputs = []

        for q in WHITELIST_QUESTIONS[:5]:
            field = TextInput(
                label=q[:45],
                style=discord.TextStyle.paragraph,
                required=True
            )
            self.inputs.append(field)
            self.add_item(field)

    async def on_submit(self, interaction: discord.Interaction):

        respostas = [i.value for i in self.inputs]
        wl_responses[interaction.user.id] = respostas

        embed = discord.Embed(
            title="📥 Nova Whitelist",
            description=f"Usuário: {interaction.user.mention}",
            color=discord.Color.orange()
        )

        canal = bot.get_channel(WHITELIST_LOG_CHANNEL)
        if canal:
            await canal.send(embed=embed)

        await interaction.response.send_message(
            "✅ Enviado com sucesso!",
            ephemeral=True
        )

# =========================
# BOTÃO WL
# =========================
class WLButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fazer Whitelist", style=discord.ButtonStyle.green)
    async def wl_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(WhitelistModal())

# =========================
# SET WHITELIST
# =========================
@bot.tree.command(name="setwhitelist", description="Configurar whitelist")
async def setwhitelist(interaction: discord.Interaction, perguntas: str, canal_logs: str, canal_painel: str):

    if not tem_cargo_permitido(interaction):
        return await interaction.response.send_message("Sem permissão.", ephemeral=True)

    global WHITELIST_QUESTIONS, WHITELIST_LOG_CHANNEL, WHITELIST_PANEL_CHANNEL

    WHITELIST_QUESTIONS = perguntas.split("|")
    WHITELIST_LOG_CHANNEL = int(canal_logs)
    WHITELIST_PANEL_CHANNEL = int(canal_painel)

    canal = bot.get_channel(WHITELIST_PANEL_CHANNEL)

    embed = discord.Embed(
        title="📋 WHITELIST RP",
        description="Clique para participar.",
        color=discord.Color.red()
    )

    await canal.send(embed=embed, view=WLButton())

    await interaction.response.send_message("Whitelist configurada.", ephemeral=True)

# =========================
# WL APROVAR
# =========================
@bot.tree.command(name="wl_aprovar")
async def wl_aprovar(interaction: discord.Interaction, usuario: discord.Member):

    if not tem_cargo_permitido(interaction):
        return await interaction.response.send_message("Sem permissão.", ephemeral=True)

    embed = discord.Embed(
        title="✅ Aprovado",
        description=f"{usuario.mention} foi aprovado.",
        color=discord.Color.green()
    )

    canal = bot.get_channel(WHITELIST_LOG_CHANNEL)
    if canal:
        await canal.send(embed=embed)

    await interaction.response.send_message("OK", ephemeral=True)

# =========================
# WL RECUSAR
# =========================
@bot.tree.command(name="wl_recusar")
async def wl_recusar(interaction: discord.Interaction, usuario: discord.Member, motivo: str):

    if not tem_cargo_permitido(interaction):
        return await interaction.response.send_message("Sem permissão.", ephemeral=True)

    embed = discord.Embed(
        title="❌ Recusado",
        description=f"{usuario.mention}\nMotivo: {motivo}",
        color=discord.Color.red()
    )

    canal = bot.get_channel(WHITELIST_LOG_CHANNEL)
    if canal:
        await canal.send(embed=embed)

    await interaction.response.send_message("OK", ephemeral=True)

# =========================
# RUN
# =========================
bot.run(TOKEN)
