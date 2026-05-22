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
            description="Bot fora do horário de funcionamento (11h–23h UTC-3).",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    uid = interaction.user.id

    if uid in user_ids:
        embed = discord.Embed(
            title="❌ ERRO",
            description=f"Você já possui um ID registrado: **{user_ids[uid]}**",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    numero = random.randint(1000, 9999)
    user_ids[uid] = numero

    nome = re.sub(r"^\d{4}\s*\|\s*", "", interaction.user.display_name)

    await interaction.user.edit(nick=f"{numero} | {nome}")

    embed = discord.Embed(
        title="🟢 ID GERADO COM SUCESSO",
        description=f"🆔 Seu novo ID é: **{numero}**\n\nGuarde ele, ele será essencial para o seu roleplay.",
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
            description="Você não tem permissão para utilizar este comando.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    nome = re.sub(r"^\d{4}\s*\|\s*", "", usuario.display_name)

    await usuario.edit(nick=nome if nome != usuario.name else None)

    embed = discord.Embed(
        title="🟢 ID RESETADO COM SUCESSO",
        description=f"O ID de {usuario.mention} foi removido com sucesso.",
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
            description="Você não tem permissão para utilizar este comando.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    embed = discord.Embed(
        title="📢 ANÚNCIO OFICIAL",
        description=mensagem,
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=embed)

# =========================
# WHITELIST
# =========================
class WLModal(discord.ui.Modal, title="WHITELIST RP"):

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
            title="📋 NOVA WHITELIST ENVIADA",
            description=f"Usuário: {interaction.user.mention}",
            color=discord.Color.green()
        )

        for q, r in zip(WHITELIST_QUESTIONS, respostas):
            embed.add_field(name=q, value=r, inline=False)

        await log.send(embed=embed)

        ok = discord.Embed(
            title="🟢 WHITELIST ENVIADA COM SUCESSO",
            description="Sua whitelist foi enviada para análise.",
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
            description="Você não tem permissão para utilizar este comando.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    embed = discord.Embed(
        title="✅ - WHITE LIST",
        description=(
            "A whitelist é uma forma de se verificar rapidamente, sem precisar pedir a um administrador manualmente, antes de abrir é recomendado estudar as regras e criar um personagem e é obrigatório pedir id."
        ),
        color=discord.Color.green()
    )

    await interaction.channel.send(embed=embed, view=WLView())

    ok = discord.Embed(
        title="🟢 SUCESSO",
        description="Whitelist configurada com sucesso.",
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

    @discord.ui.button(label="⚠️ Denúncias", style=discord.ButtonStyle.red)
    async def dn(self, i, b): await self.create(i, "Denúncias")

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
            title="🎟️ - TICKET",
            description=(
                "Crie um ticket para falar diretamente com staffs sem precisar entrar em DMS, abra tickets já com motivo em mente e fale direto, não espere alguém  falar primeiro, categorias de ticket:\n\n"
                "🤝 - Parceria\nPeça parceria (apenas fundadores e donos podem aceitar)\n\n"
                "🤔 - Dúvidas \nPergunte sobre algo que você não tem certeza ou não sabe.\n\n"
                "⚠️ - Denúncias\nDenuncie atos de anti roleplay, assédio, discurso de odio, risco de raid entre outros.\n\n"
                "❔ - Outros\nFaça alguma pergunta que não está na lista.\n\n"
                "@everyone"
            ),
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

    @discord.ui.button(label="🫴 Reivindicar Ticket", style=discord.ButtonStyle.green)
    async def claim(self, i, b):

        self.claimed = i.user
        b.label = f"🔒 Reivindicado por {i.user.display_name}"
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

        await i.response.send_message("Deletando em 3...", ephemeral=True)

        await i.channel.send("1...")
        await asyncio.sleep(1)
        await i.channel.send("2...")
        await asyncio.sleep(1)
        await i.channel.send("3...")
        await asyncio.sleep(1)
        await i.channel.send("Deletando!")

        await i.channel.delete()

@bot.tree.command(name="setticket")
async def setticket(interaction: discord.Interaction):

    if not staff(interaction):
        embed = discord.Embed(
            title="❌ ERRO",
            description="Você não tem permissão para utilizar este comando.",
            color=discord.Color.red()
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    embed = discord.Embed(
        title="🎟️ - TICKET",
        description="Sistema de tickets ativado.",
        color=discord.Color.green()
    )

    await interaction.channel.send(embed=embed, view=TicketView())

    ok = discord.Embed(
        title="🟢 SUCESSO",
        description="Sistema de tickets configurado.",
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=ok, ephemeral=True)

# =========================
# RUN
# =========================
bot.run(TOKEN)
