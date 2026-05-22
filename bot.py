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

WL_ROLE_ID = 1506446576267038821
REMOVE_ROLE_ID = 1506446577261084733

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
# PERMISSÃO
# =========================
def staff(interaction: discord.Interaction):
    return any(role.id in CARGOS_PERMITIDOS for role in interaction.user.roles)

# =========================
# HORÁRIO
# =========================
def horario_ok():
    hora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).hour
    return 11 <= hora < 23

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
# PEDIR ID
# =========================
@bot.tree.command(name="pedirid")
async def pedirid(interaction: discord.Interaction):

    if not horario_ok():
        embed = discord.Embed(
            title="❌ ERRO",
            description="Fora do horário (11h–23h).",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    uid = interaction.user.id

    if uid in user_ids:
        embed = discord.Embed(
            title="❌ ERRO",
            description=f"Você já tem ID: **{user_ids[uid]}**",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    numero = random.randint(1000, 9999)
    user_ids[uid] = numero

    nome = re.sub(r"^\d{4}\s*\|\s*", "", interaction.user.display_name)

    await interaction.user.edit(nick=f"{numero} | {nome}")

    embed = discord.Embed(
        title="🟢 ID CRIADO",
        description=f"Seu ID: **{numero}**",
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=embed)

# =========================
# RESET ID
# =========================
@bot.tree.command(name="resetid")
async def resetid(interaction: discord.Interaction, usuario: discord.Member):

    if not staff(interaction):
        embed = discord.Embed(
            title="❌ ERRO",
            description="Sem permissão.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    nome = re.sub(r"^\d{4}\s*\|\s*", "", usuario.display_name)

    await usuario.edit(nick=nome if nome != usuario.name else None)

    embed = discord.Embed(
        title="🟢 ID RESETADO",
        description=f"ID removido de {usuario.mention}",
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

# =========================
# ANÚNCIO
# =========================
@bot.tree.command(name="anuncio")
async def anuncio(interaction: discord.Interaction, mensagem: str):

    if not staff(interaction):
        embed = discord.Embed(
            title="❌ ERRO",
            description="Sem permissão.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    embed = discord.Embed(
        title="📢 ANÚNCIO",
        description=mensagem,
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=embed)

# =========================
# WHITELIST
# =========================
class WLModal(discord.ui.Modal, title="WHITE LIST RP"):

    def __init__(self):
        super().__init__()

        self.inputs = []
        for q in WHITELIST_QUESTIONS:
            t = discord.ui.TextInput(label=q[:45], style=discord.TextStyle.paragraph)
            self.inputs.append(t)
            self.add_item(t)

    async def on_submit(self, interaction: discord.Interaction):

        respostas = [i.value for i in self.inputs]

        log = bot.get_channel(LOG_CHANNEL_ID)

        embed = discord.Embed(
            title="📋 NOVA WL",
            description=interaction.user.mention,
            color=discord.Color.green()
        )

        for q, r in zip(WHITELIST_QUESTIONS, respostas):
            embed.add_field(name=q, value=r, inline=False)

        await log.send(embed=embed)

        ok = discord.Embed(
            title="🟢 WL ENVIADA",
            description="Sua whitelist foi enviada com sucesso.",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=ok, ephemeral=True)

class WLView(discord.ui.View):

    @discord.ui.button(label="✅ - Fazer WL", style=discord.ButtonStyle.green)
    async def wl(self, interaction, button):
        await interaction.response.send_modal(WLModal())

@bot.tree.command(name="setwhitelist")
async def setwhitelist(interaction: discord.Interaction):

    if not staff(interaction):
        embed = discord.Embed(
            title="❌ ERRO",
            description="Sem permissão.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    embed = discord.Embed(
        title="✅ WHITE LIST",
        description="Clique para iniciar sua WL RP.",
        color=discord.Color.green()
    )

    await interaction.channel.send(embed=embed, view=WLView())

    ok = discord.Embed(
        title="🟢 SUCESSO",
        description="Whitelist criada.",
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=ok, ephemeral=True)

# =========================
# TICKETS
# =========================
class TicketView(discord.ui.View):

    @discord.ui.button(label="🤝 Parceria", style=discord.ButtonStyle.blurple)
    async def p(self, i, b): await self.create(i, "Parceria")

    @discord.ui.button(label="🤔 Dúvidas", style=discord.ButtonStyle.blurple)
    async def d(self, i, b): await self.create(i, "Dúvidas")

    @discord.ui.button(label="⚠️ Denúncia", style=discord.ButtonStyle.red)
    async def dn(self, i, b): await self.create(i, "Denúncia")

    @discord.ui.button(label="❔ Outros", style=discord.ButtonStyle.gray)
    async def o(self, i, b): await self.create(i, "Outros")

    async def create(self, interaction, motivo):

        global ticket_counter
        ticket_counter += 1

        name = interaction.user.display_name.replace(" ", "")

        channel = await interaction.guild.create_text_channel(
            f"{name}-{ticket_counter}"
        )

        embed = discord.Embed(
            title=f"🎟️ {motivo}",
            description="Ticket criado com sucesso.",
            color=discord.Color.green()
        )

        await channel.send(embed=embed, view=TicketControl(interaction.user))

        ok = discord.Embed(
            title="🟢 TICKET CRIADO",
            description=f"{channel.mention}",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=ok, ephemeral=True)

class TicketControl(discord.ui.View):

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.claimed = None

    @discord.ui.button(label="🫴 Reivindicar", style=discord.ButtonStyle.green)
    async def claim(self, i, b):

        self.claimed = i.user
        b.label = f"🔒 {i.user.display_name}"
        b.disabled = True

        await i.message.edit(view=self)

        await i.response.send_message("🟢 Ticket reivindicado.", ephemeral=True)

    @discord.ui.button(label="📢 Chamar Staff", style=discord.ButtonStyle.red)
    async def staff(self, i, b):
        await i.channel.send("<@&1506446576267038821>")

    @discord.ui.button(label="👨 Chamar Membro", style=discord.ButtonStyle.blurple)
    async def member(self, i, b):
        await i.channel.send(self.user.mention)

    @discord.ui.button(label="❌ Fechar", style=discord.ButtonStyle.red)
    async def close(self, i, b):

        await i.response.send_message("Fechando...", ephemeral=True)

        for x in range(3, 0, -1):
            await asyncio.sleep(1)
            await i.channel.send(f"⏳ {x}")

        await i.channel.delete()

@bot.tree.command(name="setticket")
async def setticket(interaction: discord.Interaction):

    if not staff(interaction):
        embed = discord.Embed(
            title="❌ ERRO",
            description="Sem permissão.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    embed = discord.Embed(
        title="🎟️ TICKET RP",
        description="Clique para abrir ticket.",
        color=discord.Color.green()
    )

    await interaction.channel.send(embed=embed, view=TicketView())

    ok = discord.Embed(
        title="🟢 SUCESSO",
        description="Ticket sistema criado.",
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=ok, ephemeral=True)

# =========================
# RUN
# =========================
bot.run(TOKEN)
