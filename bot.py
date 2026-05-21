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

async def verificar_horario():
    await bot.wait_until_ready()
    while True:
        hora = datetime.datetime.now().hour
        if hora < 11 or hora >= 23:
            await bot.close()
            break
        await asyncio.sleep(60)

class MyBot(commands.Bot):
    async def setup_hook(self):
        self.loop.create_task(verificar_horario())
        await self.tree.sync()

bot = MyBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

@bot.tree.command(name="pedirid")
async def pedirid(interaction: discord.Interaction):

    uid = interaction.user.id
    agora = datetime.datetime.now()

    if uid in user_ids:
        data = user_ids[uid]["data"]
        hora = user_ids[uid]["hora"]
        old_id = user_ids[uid]["id"]

        await interaction.response.send_message(
            f"❌ Não foi possível gerar um novo ID.\n"
            f"Você já obteve o ID `{old_id}` às `{hora}` no dia `{data}`.",
            ephemeral=True
        )
        return

    numero_id = random.randint(1000, 9999)

    user_ids[uid] = {
        "id": numero_id,
        "data": agora.strftime("%d/%m"),
        "hora": agora.strftime("%H:%M")
    }

    try:
        await interaction.user.edit(nick=f"{interaction.user.name} | {numero_id}")
        await interaction.response.send_message(f"Seu novo ID é: {numero_id}", ephemeral=True)

    except discord.Forbidden:
        await interaction.response.send_message(
            f"Não consegui alterar seu nickname. Seu ID é: {numero_id}",
            ephemeral=True
        )

@bot.tree.command(name="resetid")
@app_commands.describe(usuario="Usuário")
async def resetid(interaction: discord.Interaction, usuario: discord.Member):

    if not tem_cargo_permitido(interaction):
        await interaction.response.send_message("Sem permissão", ephemeral=True)
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
