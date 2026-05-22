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
# CONFIGURAÇÕES
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
# HORÁRIO (11h–23h UTC-3)
# =========================
def horario_ok():
    return 11 <= (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).hour < 23

# =========================
# PERMISSÃO STAFF
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
# 🆔 PEDIR ID
# =========================
@bot.tree.command(name="pedirid")
async def pedirid(interaction: discord.Interaction):

    if not horario_ok():
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ ERRO",
                description="⛔ Fora do horário (11h–23h UTC-3).",
                color=discord.Color.red()
            ),
            ephemeral=True
        )

    uid = interaction.user.id

    if uid in user_ids:
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ ERRO",
                description=f"Você já tem ID: **{user_ids[uid]}**",
                color=discord.Color.red()
            ),
            ephemeral=True
        )

    numero = random.randint(1000, 9999)
    user_ids[uid] = numero

    nome = re.sub(r"^\d{4}\s*\|\s*", "", interaction.user.display_name)

    await interaction.user.edit(nick=f"{numero} | {nome}")

    await interaction.response.send_message(
        embed=discord.Embed(
            title="🟢 ID GERADO",
            description=f"Seu ID: **{numero}**",
            color=discord.Color.green()
        )
    )

# =========================
# 📢 ANÚNCIO
# =========================
@bot.tree.command(name="anuncio")
async def anuncio(interaction: discord.Interaction, mensagem: str):

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

    await interaction.response.send_message(
        embed=discord.Embed(
            title="📢 ANÚNCIO",
            description=mensagem,
            color=discord.Color.green()
        )
    )

# =========================
# 🎟️ WHITELIST
# =========================
class WLReviewView(discord.ui.View):

    def __init__(self, user):
        super().__init__()
        self.user = user

    @discord.ui.button(label="🟢 Aprovar WL", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(WL_ROLE_ID)
        remove_role = interaction.guild.get_role(WL_REMOVE_ROLE_ID)

        if role:
            await self.user.add_roles(role)
        if remove_role:
            await self.user.remove_roles(remove_role)

        try:
            await self.user.send(
                embed=discord.Embed(
                    title="🟢 WL APROVADA",
                    description="Sua whitelist foi aprovada no servidor!",
                    color=discord.Color.green()
                )
            )
        except:
            pass

        await interaction.response.send_message("Aprovado.", ephemeral=True)

    @discord.ui.button(label="🔴 Reprovar WL", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):

        try:
            await self.user.send(
                embed=discord.Embed(
                    title="🔴 WL REPROVADA",
                    description="Sua whitelist foi reprovada.",
                    color=discord.Color.red()
                )
            )
        except:
            pass

        await interaction.response.send_message("Reprovado.", ephemeral=True)

class WLModal(discord.ui.Modal, title="WHITELIST RP"):

    def __init__(self):
        super().__init__()
        self.inputs = []

        for q in WHITELIST_QUESTIONS:
            t = discord.ui.TextInput(label=q[:45], style=discord.TextStyle.paragraph)
            self.inputs.append(t)
            self.add_item(t)

    async def on_submit(self, interaction: discord.Interaction):

        log = bot.get_channel(LOG_CHANNEL_ID)

        embed = discord.Embed(
            title="📋 WHITELIST ENVIADA",
            description=f"👤 {interaction.user.mention}",
            color=discord.Color.green()
        )

        for q, r in zip(WHITELIST_QUESTIONS, [i.value for i in self.inputs]):
            embed.add_field(name=q, value=r, inline=False)

        await log.send(embed=embed, view=WLReviewView(interaction.user))

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🟢 WL ENVIADA",
                description="Sua whitelist foi enviada.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

class WLView(discord.ui.View):

    @discord.ui.button(label="✅ Fazer WL", style=discord.ButtonStyle.green)
    async def wl(self, i, b):
        await i.response.send_modal(WLModal())

@bot.tree.command(name="setwhitelist")
async def setwhitelist(interaction: discord.Interaction):

    if not staff(interaction):
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ ERRO",
                description="Sem permissão.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )

    await interaction.channel.send(
        embed=discord.Embed(
            title="📋 WHITE LIST",
            description=(
                "A whitelist é uma forma de se verificar rapidamente.\n\n"
                "Estude as regras antes de abrir.\n"
                "É obrigatório pedir ID."
            ),
            color=discord.Color.green()
        ),
        view=WLView()
    )

    await interaction.response.send_message("WL ativada.", ephemeral=True)

# =========================
# 🎟️ TICKETS
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

    async def create(self, interaction, opcao):

        global ticket_counter
        ticket_counter += 1

        name = interaction.user.display_name.replace(" ", "")

        channel = await interaction.guild.create_text_channel(
            f"{name}-{ticket_counter}"
        )

        await channel.send(
            embed=discord.Embed(
                title="🎟️ TICKET",
                description=(
                    "Crie um ticket para falar diretamente com staffs sem precisar de DM.\n"
                    "Abra tickets já com motivo em mente.\n\n"
                    "@everyone"
                ),
                color=discord.Color.green()
            )
        )

        await channel.send(
            embed=discord.Embed(
                title="🎟️ TICKET ABERTO",
                description=(
                    f'Opção: "{opcao}"\n\n'
                    "Comente antes de um staff chegar."
                ),
                color=discord.Color.green()
            ),
            view=TicketControl(interaction.user)
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🟢 TICKET CRIADO",
                description=channel.mention,
                color=discord.Color.green()
            ),
            ephemeral=True
        )

class TicketControl(discord.ui.View):

    def __init__(self, user):
        super().__init__()
        self.user = user

    @discord.ui.button(label="🫴 Reivindicar Ticket", style=discord.ButtonStyle.green)
    async def claim(self, i, b):
        b.label = f"🔒 {i.user.display_name}"
        b.disabled = True
        await i.message.edit(view=self)
        await i.response.send_message("OK", ephemeral=True)

    @discord.ui.button(label="📢 Chamar Staff", style=discord.ButtonStyle.red)
    async def staff(self, i, b):
        await i.channel.send(f"<@&{CALL_STAFF_ROLE}>")

    @discord.ui.button(label="👨 Chamar Membro", style=discord.ButtonStyle.blurple)
    async def member(self, i, b):
        await i.channel.send(self.user.mention)

    @discord.ui.button(label="❌ Fechar", style=discord.ButtonStyle.red)
    async def close(self, i, b):

        await i.response.send_message("Fechando em 3...", ephemeral=True)

        for x in range(3, 0, -1):
            await asyncio.sleep(1)
            await i.channel.send(f"{x}...")

        await i.channel.send("Deletando!")
        await i.channel.delete()

# =========================
# RUN
# =========================
bot.run(TOKEN)
