import os
import discord
from discord.ext import commands
from discord import app_commands
import random
import re
import datetime
import asyncio

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

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

# armazenar IDs já usados
user_ids = {}

def tem_cargo_permitido(interaction: discord.Interaction):
    return any(role.id in CARGOS_PERMITIDOS for role in interaction.user.roles)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logado como {bot.user}")

async def verificar_horario():
    await bot.wait_until_ready()
    while True:
        hora = datetime.datetime.now().hour
        if hora < 11 or hora >= 23:
            await bot.close()
            break
        await asyncio.sleep(60)

bot.loop.create_task(verificar_horario())

@bot.tree.command(name="pedirid")
async def pedirid(interaction: discord.Interaction):

    user_id = interaction.user.id
    agora = datetime.datetime.now()

    # se já tem ID
    if user_id in user_ids:
        data = user_ids[user_id]["data"]
        hora = user_ids[user_id]["hora"]
        id_antigo = user_ids[user_id]["id"]

        await interaction.response.send_message(
            f"❌ Não foi possível gerar um novo ID.\n"
            f"Você já obteve o ID `{id_antigo}` às `{hora}` no dia `{data}`.",
            ephemeral=True
        )
        return

    # gerar novo ID único
    numero_id = random.randint(1000, 9999)

    user_ids[user_id] = {
        "id": numero_id,
        "data": agora.strftime("%d/%m"),
        "hora": agora.strftime("%H:%M")
    }

    try:
        await interaction.user.edit(
            nick=f"{interaction.user.name} | {numero_id}"
        )
        await interaction.response.send_message(
            f"Seu novo ID é: {numero_id}",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            f"Não consegui alterar seu nickname. Seu ID é: {numero_id}",
            ephemeral=True
        )

@bot.tree.command(name="resetid")
@app_commands.describe(usuario="Usuário")
async def resetid(interaction: discord.Interaction, usuario: discord.Member):

    if not tem_cargo_permitido(interaction):
        await interaction.response.send_message(
            "Sem permissão",
            ephemeral=True
        )
        return

    nick = usuario.nick or usuario.name
    novo = re.sub(r'\s*\|\s*\d{4}$', '', nick).strip()

    try:
        await usuario.edit(nick=novo if novo != usuario.name else None)
        await interaction.response.send_message("ID removido", ephemeral=True)

    except discord.Forbidden:
        await interaction.response.send_message(
            "Sem permissão para alterar este usuário",
            ephemeral=True
        )

bot.run(TOKEN)
