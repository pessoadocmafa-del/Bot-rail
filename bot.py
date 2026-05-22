import os
import discord
from discord.ext import commands
from discord import app_commands
import random
import re
import datetime
import asyncio

TOKEN = os.environ["DISCORD_TOKEN"]
WHITELIST_QUESTIONS = []
WHITELIST_LOG_CHANNEL = None
WHITELIST_PANEL_CHANNEL = None
wl_responses = {}

intents = discord.Intents.default()
intents.members = True

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

def horario_permitido():
    hora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).hour
    return 11 <= hora < 23

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()
        self.loop.create_task(verificar_horario())

async def verificar_horario():
    await asyncio.sleep(5)
    while True:
        if not horario_permitido():
            print("Fora do horário (11h–23h UTC-3). Desligando bot...")
            await bot.close()
            break
        await asyncio.sleep(60)

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
        await interaction.response.send_message(
            "⛔ O bot está fora do horário de funcionamento (11h–23h).",
            ephemeral=True
        )
        return

    uid = interaction.user.id

    if uid in user_ids:
        old_id = user_ids[uid]

        embed = discord.Embed(
            title="❌ Erro na geração",
            description=(
                f"Você já possui um ID.\n\n"
                f"Seu ID antigo é **{old_id}**.\n"
                f"Não é possível gerar outro enquanto já tiver um."
            ),
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    numero_id = random.randint(1000, 9999)
    user_ids[uid] = numero_id

    try:
        nome = interaction.user.display_name

        nome = re.sub(r"^\d{4}\s*\|\s*", "", nome).strip()

        await interaction.user.edit(
            nick=f"{numero_id} | {nome}"
        )

        embed = discord.Embed(
            title="✅ ID gerado com sucesso!",
            description=(
                f"🆔 Seu novo ID é: **{numero_id}**\n\n"
                "Guarde ele, ele é essencial para o roleplay."
            ),
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Não tenho permissão para alterar seu nome.",
            ephemeral=True
        )

# =========================
# /ANUNCIO
# =========================
@bot.tree.command(name="anuncio", description="Faz um anúncio para o servidor")
@app_commands.describe(mensagem="Mensagem do anúncio")
async def anuncio(interaction: discord.Interaction, mensagem: str):

    if not horario_permitido():
        await interaction.response.send_message(
            "⛔ Fora do horário de funcionamento.",
            ephemeral=True
        )
        return

    if not tem_cargo_permitido(interaction):
        await interaction.response.send_message(
            "❌ Sem permissão.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        description=mensagem,
        color=discord.Color.red()
    )

    await interaction.response.send_message(embed=embed)
    from discord.ui import View, Button, Modal, TextInput

wl_responses = {}


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
            title="📥 Nova Whitelist enviada",
            description=f"Usuário: {interaction.user.mention}",
            color=discord.Color.orange()
        )

        canal = bot.get_channel(WHITELIST_LOG_CHANNEL)
        if canal:
            await canal.send(embed=embed)

        await interaction.response.send_message(
            "✅ Sua whitelist foi enviada!",
            ephemeral=True
        )


class WLButton(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fazer Whitelist",
        style=discord.ButtonStyle.green
    )
    async def wl_button(self, interaction: discord.Interaction, button: Button):

        await interaction.response.send_modal(WhitelistModal())


@bot.tree.command(name="setwhitelist", description="Configurar whitelist PRO + painel")
@app_commands.describe(
    perguntas="Use | para separar perguntas",
    canal_logs="ID do canal de logs",
    canal_painel="ID do canal do painel"
)
async def setwhitelist(interaction: discord.Interaction, perguntas: str, canal_logs: str, canal_painel: str):

    if not tem_cargo_permitido(interaction):
        await interaction.response.send_message("Sem permissão.", ephemeral=True)
        return

    global WHITELIST_QUESTIONS, WHITELIST_LOG_CHANNEL, WHITELIST_PANEL_CHANNEL

    WHITELIST_QUESTIONS = perguntas.split("|")
    WHITELIST_LOG_CHANNEL = int(canal_logs)
    WHITELIST_PANEL_CHANNEL = int(canal_painel)

    canal = bot.get_channel(WHITELIST_PANEL_CHANNEL)

    embed = discord.Embed(
        title="📋 WHITELIST RP",
        description="Clique no botão abaixo para fazer sua whitelist.",
        color=discord.Color.red()
    )

    await canal.send(embed=embed, view=WLButton())

    await interaction.response.send_message(
        "✅ Whitelist configurada com painel.",
        ephemeral=True
    )


@bot.tree.command(name="wl_aprovar", description="Aprovar whitelist")
async def wl_aprovar(interaction: discord.Interaction, usuario: discord.Member):

    if not tem_cargo_permitido(interaction):
        await interaction.response.send_message("Sem permissão.", ephemeral=True)
        return

    embed = discord.Embed(
        title="✅ Whitelist aprovada",
        description=f"{usuario.mention} foi aprovado.",
        color=discord.Color.green()
    )

    canal = bot.get_channel(WHITELIST_LOG_CHANNEL)
    if canal:
        await canal.send(embed=embed)

    await interaction.response.send_message("Aprovado.", ephemeral=True)


@bot.tree.command(name="wl_recusar", description="Recusar whitelist")
async def wl_recusar(interaction: discord.Interaction, usuario: discord.Member, motivo: str):

    if not tem_cargo_permitido(interaction):
        await interaction.response.send_message("Sem permissão.", ephemeral=True)
        return

    embed = discord.Embed(
        title="❌ Whitelist recusada",
        description=f"{usuario.mention}\nMotivo: {motivo}",
        color=discord.Color.red()
    )

    canal = bot.get_channel(WHITELIST_LOG_CHANNEL)
    if canal:
        await canal.send(embed=embed)

    await interaction.response.send_message("Recusado.", ephemeral=True)

bot.run(TOKEN)
