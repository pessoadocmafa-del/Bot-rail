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
        old_id = user_ids[uid]["id"]

        embed = discord.Embed(
            title="❌ Erro na geração",
            description=(
                f"Esse erro acontece pois você já tem um ID.\n\n"
                f"Seu ID antigo é **{old_id}**.\n"
                f"Não é possível gerar um novo ID enquanto você já tiver um."
            ),
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    numero_id = random.randint(1000, 9999)

    user_ids[uid] = {
        "id": numero_id,
        "data": agora.strftime("%d/%m"),
        "hora": agora.strftime("%H:%M")
    }

    try:
        nome_atual = interaction.user.display_name
        await interaction.user.edit(nick=f"{numero_id} | {nome_atual}")

        embed = discord.Embed(
            title="✅ ID gerado com sucesso!",
            description=(
                f"🆔 Seu novo ID é: **{numero_id}**\n\n"
                f"🆔 Guarde ele, vai ser essencial para o seu roleplay!\n\n"
                f"⚠️ Caso queira trocar peça para alguém de alto nível trocar (por motivo válido)."
            ),
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    except discord.Forbidden:

        embed = discord.Embed(
            title="❌ Erro na geração",
            description=(
                f"Não tenho permissão para alterar seu nome.\n\n"
                f"Se você for staff o erro pode ser comum.\n"
                f"Mas caso tenha cargo baixo, reporte o erro!"
            ),
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

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
        @bot.tree.command(name="anuncio", description="Envia um anúncio em embed")
@app_commands.describe(
    titulo="Título do anúncio",
    mensagem="Conteúdo do anúncio"
)
async def anuncio(
    interaction: discord.Interaction,
    titulo: str,
    mensagem: str
):

    embed = discord.Embed(
        title=titulo,
        description=mensagem,
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
