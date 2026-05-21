import os
import discord
from discord.ext import commands
from discord import app_commands
import random
import re
import datetime
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("DISCORD_TOKEN não configurado!")
    exit()

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 🔒 CARGOS PERMITIDOS (IDS QUE VOCÊ MANDOU)
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

def tem_cargo_permitido(interaction: discord.Interaction) -> bool:
    ids_cargos = [role.id for role in interaction.user.roles]
    return any(cargo in ids_cargos for cargo in CARGOS_PERMITIDOS)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logado como {bot.user}')

# ⏰ SISTEMA DE HORÁRIO (11h até 23h)
async def verificar_horario():
    await bot.wait_until_ready()

    while True:
        hora = datetime.datetime.now().hour

        if hora < 11 or hora >= 23:
            print("Fora do horário, desligando bot...")
            await bot.close()
            break

        await asyncio.sleep(60)

bot.loop.create_task(verificar_horario())

# 🎯 /pedirid
@bot.tree.command(name="pedirid", description="Gera um ID aleatório e aplica no nickname")
async def pedirid(interaction: discord.Interaction):
    numero_id = random.randint(1000, 9999)

    try:
        await interaction.user.edit(nick=f"{interaction.user.name} | {numero_id}")
        await interaction.response.send_message(
            f"Seu novo ID é: {numero_id}",
            ephemeral=True
        )
    except:
        await interaction.response.send_message(
            "Não consegui alterar seu nome. Verifique permissões.",
            ephemeral=True
        )

# 🔐 /resetid (SÓ CARGOS PERMITIDOS)
@bot.tree.command(
    name="resetid",
    description="Remove o ID do nickname de um usuário"
)
@app_commands.describe(usuario="Usuário que terá o ID removido")
async def resetid(interaction: discord.Interaction, usuario: discord.Member):

    if not tem_cargo_permitido(interaction):
        await interaction.response.send_message(
            "❌ Você não tem permissão para usar isso.",
            ephemeral=True
        )
        return

    nick_atual = usuario.nick or usuario.name
    novo_nick = re.sub(r'\s*\|\s*\d{4}$', '', nick_atual).strip()

    try:
        await usuario.edit(nick=novo_nick if novo_nick != usuario.name else None)
        await interaction.response.send_message(
            f"✅ ID removido de {usuario.mention}",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Não consegui alterar esse usuário.",
            ephemeral=True
        )

bot.run(TOKEN)
