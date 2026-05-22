import os
import discord
from discord.ext import commands
from discord import app_commands
import random
import re
import datetime
import asyncio
from discord.ui import View, Button, Modal, TextInput

TOKEN = os.environ["DISCORD_TOKEN"]

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

# =========================
# VARIÁVEIS GERAIS
# =========================
user_ids = {}

WHITELIST_QUESTIONS = [
    "Qual nome do seu personagem?",
    "Qual sua idade e a do personagem?",
    "O que é RDM e VDM?",
    "Você já fez RP antes?",
    "Algum recado?"
]

WHITELIST_LOG_CHANNEL = None
WHITELIST_PANEL_CHANNEL = None
wl_responses = {}

# =========================
# PERMISSÃO
# =========================
def tem_cargo_permitido(interaction: discord.Interaction):
    return any(role.id in CARGOS_PERMITIDOS for role in interaction.user.roles)

# =========================
# HORÁRIO (11h–23h UTC-3)
# =========================
def horario_permitido():
    hora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).hour
    return 11 <= hora < 23

async def verificar_horario():
    await bot.wait_until_ready()
    while True:
        if not horario_permitido():
            print("Fora do horário (11h–23h). Desligando bot...")
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
@bot.tree.command(name="pedirid", description="Gerar ID RP")
async def pedirid(interaction: discord.Interaction):

    if not horario_permitido():
        return await interaction.response.send_message("⛔ Fora do horário.", ephemeral=True)

    uid = interaction.user.id

    if uid in user_ids:
        return await interaction.response.send_message(
            f"❌ Você já tem um ID: **{user_ids[uid]}**",
            ephemeral=True
        )

    numero_id = random.randint(1000, 9999)
    user_ids[uid] = numero_id

    try:
        nome = interaction.user.display_name
        nome = re.sub(r"^\d{4}\s*\|\s*", "", nome).strip()

        await interaction.user.edit(nick=f"{numero_id} | {nome}")

        embed = discord.Embed(
            title="✅ ID gerado com sucesso!",
            description=f"🆔 Seu novo ID é: **{numero_id}**",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    except discord.Forbidden:
        await interaction.response.send_message("❌ Sem permissão de nick.", ephemeral=True)

# =========================
# /ANUNCIO
# =========================
@bot.tree.command(name="anuncio", description="Fazer anúncio")
@app_commands.describe(mensagem="Mensagem do anúncio")
async def anuncio(interaction: discord.Interaction, mensagem: str):

    if not tem_cargo_permitido(interaction):
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

    embed = discord.Embed(
        description=mensagem,
        color=discord.Color.red()
    )

    await interaction.response.send_message(embed=embed)

# =========================
# WHITELIST MODAL
# =========================
class WhitelistModal(Modal, title="Whitelist RP"):

    def __init__(self):
        super().__init__()

        self.inputs = []

        for q in WHITELIST_QUESTIONS:
            field = TextInput(
                label=q[:45],
                style=discord.TextStyle.paragraph,
                required=True
            )
            self.inputs.append(field)
            self.add_item(field)

    async def on_submit(self, interaction: discord.Interaction):

        wl_responses[interaction.user.id] = [i.value for i in self.inputs]

        embed = discord.Embed(
            title="📥 Whitelist enviada",
            description=f"{interaction.user.mention}",
            color=discord.Color.orange()
        )

        canal = bot.get_channel(WHITELIST_LOG_CHANNEL)
        if canal:
            await canal.send(embed=embed)

        await interaction.response.send_message("✅ Enviado!", ephemeral=True)

# =========================
# BOTÃO WL
# =========================
class WLButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fazer Whitelist", style=discord.ButtonStyle.green)
    async def wl(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(WhitelistModal())

# =========================
# SET WHITELIST
# =========================
@bot.tree.command(name="setwhitelist", description="Criar painel whitelist")
async def setwhitelist(interaction: discord.Interaction):

    global WHITELIST_LOG_CHANNEL, WHITELIST_PANEL_CHANNEL

    if not tem_cargo_permitido(interaction):
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

    # usa canal atual como painel
    WHITELIST_PANEL_CHANNEL = interaction.channel.id
    WHITELIST_LOG_CHANNEL = interaction.channel.id

    embed = discord.Embed(
        title="📋 WHITELIST RP",
        description="Clique para fazer sua whitelist",
        color=discord.Color.red()
    )

    await interaction.channel.send(embed=embed, view=WLButton())

    await interaction.response.send_message("✅ WL criada", ephemeral=True)

# =========================
# APROVAR WL
# =========================
@bot.tree.command(name="aprovarwl")
async def aprovarwl(interaction: discord.Interaction, usuario: discord.Member):

    if not tem_cargo_permitido(interaction):
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

    embed = discord.Embed(
        title="✅ APROVADO",
        description="Você foi aprovado na whitelist!",
        color=discord.Color.green()
    )

    try:
        await usuario.send(embed=embed)
    except:
        pass

    canal = bot.get_channel(WHITELIST_LOG_CHANNEL)
    if canal:
        await canal.send(f"✅ {usuario} aprovado")

    await interaction.response.send_message("OK", ephemeral=True)

# =========================
# RECUSAR WL
# =========================
@bot.tree.command(name="recusarwl")
async def recusarwl(interaction: discord.Interaction, usuario: discord.Member, motivo: str):

    if not tem_cargo_permitido(interaction):
        return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

    embed = discord.Embed(
        title="❌ RECUSADO",
        description=f"Motivo: {motivo}",
        color=discord.Color.red()
    )

    try:
        await usuario.send(embed=embed)
    except:
        pass

    canal = bot.get_channel(WHITELIST_LOG_CHANNEL)
    if canal:
        await canal.send(f"❌ {usuario} recusado: {motivo}")

    await interaction.response.send_message("OK", ephemeral=True)

# =========================
# RUN
# =========================
bot.run(TOKEN)
