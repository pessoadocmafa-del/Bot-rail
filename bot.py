import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import re
import datetime
from discord.ui import View, Button, Modal, TextInput

TOKEN = os.environ["DISCORD_TOKEN"]

# =========================
# CONFIG
# =========================
LOG_CHANNEL_ID = 1506671577931055255
WL_ROLE_ID = 1506446576267038821

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
wl_data = {}
ticket_counter = 0

# =========================
# HORÁRIO
# =========================
def horario_permitido():
    hora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).hour
    return 11 <= hora < 23

async def verificar_horario():
    await asyncio.sleep(5)
    while True:
        if not horario_permitido():
            print("Fora do horário (11h–23h). Bot desligando...")
            await bot.close()
            break
        await asyncio.sleep(60)

# =========================
# PERMISSÃO
# =========================
def tem_cargo_permitido(interaction: discord.Interaction):
    return any(role.id in CARGOS_PERMITIDOS for role in interaction.user.roles)

# =========================
# BOT
# =========================
intents = discord.Intents.default()
intents.members = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()
        self.loop.create_task(verificar_horario())

bot = MyBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

# =========================
# PEDIR ID
# =========================
@bot.tree.command(name="pedirid", description="Gera ID RP")
async def pedirid(interaction: discord.Interaction):

    if not horario_permitido():
        return await interaction.response.send_message("⛔ Fora do horário.", ephemeral=True)

    uid = interaction.user.id

    if uid in user_ids:
        return await interaction.response.send_message(
            f"❌ Você já tem ID: **{user_ids[uid]}**",
            ephemeral=True
        )

    numero_id = random.randint(1000, 9999)
    user_ids[uid] = numero_id

    nome = interaction.user.display_name
    nome = re.sub(r"^\d{4}\s*\|\s*", "", nome)

    try:
        await interaction.user.edit(nick=f"{numero_id} | {nome}")

        embed = discord.Embed(
            title="✅ ID GERADO",
            description=f"Seu ID: **{numero_id}**",
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed)

    except discord.Forbidden:
        await interaction.response.send_message("❌ Sem permissão para alterar nick.", ephemeral=True)

# =========================
# ANÚNCIO
# =========================
@bot.tree.command(name="anuncio", description="Faz anúncio")
async def anuncio(interaction: discord.Interaction, mensagem: str):

    if not tem_cargo_permitido(interaction):
        return await interaction.response.send_message("Sem permissão.", ephemeral=True)

    embed = discord.Embed(
        description=mensagem,
        color=discord.Color.red()
    )

    await interaction.response.send_message(embed=embed)

# =========================
# WHITELIST
# =========================
class WhitelistModal(Modal, title="Whitelist RP"):

    def __init__(self):
        super().__init__()
        self.inputs = []

        for q in WHITELIST_QUESTIONS:
            field = TextInput(label=q[:45], style=discord.TextStyle.paragraph, required=True)
            self.inputs.append(field)
            self.add_item(field)

    async def on_submit(self, interaction: discord.Interaction):

        respostas = [i.value for i in self.inputs]
        wl_data[interaction.user.id] = interaction.user

        canal = bot.get_channel(LOG_CHANNEL_ID)

        embed = discord.Embed(
            title="📋 NOVA WL",
            description=f"{interaction.user.mention}",
            color=discord.Color.red()
        )

        for q, r in zip(WHITELIST_QUESTIONS, respostas):
            embed.add_field(name=q, value=r[:1024], inline=False)

        await canal.send(embed=embed, view=WLView(interaction.user))

        await interaction.response.send_message("WL enviada!", ephemeral=True)

class WLView(View):

    def __init__(self, user):
        super().__init__()
        self.user = user

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green)
    async def aprovar(self, interaction: discord.Interaction, button: Button):

        if not tem_cargo_permitido(interaction):
            return await interaction.response.send_message("Sem permissão.", ephemeral=True)

        role = interaction.guild.get_role(WL_ROLE_ID)
        await self.user.add_roles(role)

        await self.user.send(embed=discord.Embed(
            title="WL APROVADA",
            color=discord.Color.red()
        ))

        await interaction.response.send_message("Aprovado.", ephemeral=True)

    @discord.ui.button(label="Reprovar", style=discord.ButtonStyle.red)
    async def reprovar(self, interaction: discord.Interaction, button: Button):

        await self.user.send(embed=discord.Embed(
            title="WL REPROVADA",
            color=discord.Color.red()
        ))

        await interaction.response.send_message("Reprovado.", ephemeral=True)

class WLPanel(View):

    @discord.ui.button(label="Fazer WL", style=discord.ButtonStyle.green)
    async def start(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(WhitelistModal())

@bot.tree.command(name="setwhitelist")
async def setwhitelist(interaction: discord.Interaction):

    embed = discord.Embed(
        title="WHITELIST RP",
        color=discord.Color.red()
    )

    await interaction.channel.send(embed=embed, view=WLPanel())
    await interaction.response.send_message("WL criada.", ephemeral=True)

# =========================
# TICKET
# =========================
class TicketView(View):

    @discord.ui.button(label="🤝 Parceria", style=discord.ButtonStyle.blurple)
    async def p(self, interaction: discord.Interaction, button: Button):
        await self.create(interaction, "Parceria")

    @discord.ui.button(label="🤔 Dúvidas", style=discord.ButtonStyle.blurple)
    async def d(self, interaction: discord.Interaction, button: Button):
        await self.create(interaction, "Dúvidas")

    @discord.ui.button(label="⚠️ Denúncia", style=discord.ButtonStyle.red)
    async def dn(self, interaction: discord.Interaction, button: Button):
        await self.create(interaction, "Denúncia")

    @discord.ui.button(label="❔ Outros", style=discord.ButtonStyle.gray)
    async def o(self, interaction: discord.Interaction, button: Button):
        await self.create(interaction, "Outros")

    async def create(self, interaction, motivo):

        global ticket_counter
        ticket_counter += 1

        name = interaction.user.display_name.replace(" ", "")
        channel = await interaction.guild.create_text_channel(
            f"{name}#{ticket_counter}"
        )

        embed = discord.Embed(
            title=f"Ticket - {motivo}",
            color=discord.Color.red()
        )

        await channel.send(embed=embed, view=TicketControl(interaction.user))

        await interaction.response.send_message(f"Criado: {channel.mention}", ephemeral=True)

class TicketControl(View):

    def __init__(self, user):
        super().__init__()
        self.user = user

    @discord.ui.button(label="📌 Reivindicar", style=discord.ButtonStyle.green)
    async def claim(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Reivindicado.", ephemeral=True)

    @discord.ui.button(label="🔔 Staff", style=discord.ButtonStyle.red)
    async def staff(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.send("<@&1506446576267038821> Staff chamado!")

    @discord.ui.button(label="👤 Membro", style=discord.ButtonStyle.blurple)
    async def member(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.send(f"{self.user.mention}")

    @discord.ui.button(label="🔒 Fechar", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.delete()

@bot.tree.command(name="setticket")
async def setticket(interaction: discord.Interaction):

    embed = discord.Embed(
        title="TICKETS",
        description="Clique para abrir ticket",
        color=discord.Color.red()
    )

    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("Ticket pronto.", ephemeral=True)

# =========================
# RUN
# =========================
bot.run(TOKEN)
