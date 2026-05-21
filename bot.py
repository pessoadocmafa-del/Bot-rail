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

class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

@bot.tree.command(
    name="pedirid",
    description="Gera um ID para o jogador"
)
async def pedirid(interaction: discord.Interaction):

    uid = interaction.user.id

    if uid in user_ids:
        old_id = user_ids[uid]

        embed = discord.Embed(
            title="❌ Erro na geração",
            description=(
                f"Esse erro acontece pois você já tem um ID.\n\n"
                f"Seu ID antigo é **{old_id}**.\n"
                f"Não é possível gerar um novo ID enquanto você já tiver um."
            ),
            color=discord.Color.red()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
        return

    numero_id = random.randint(1000, 9999)

    while numero_id in user_ids.values():
        numero_id = random.randint(1000, 9999)

    user_ids[uid] = numero_id

    try:
        nome_original = interaction.user.display_name

        nome_original = re.sub(
            r"^\d{4}\s*\|\s*",
            "",
            nome_original
        ).strip()

        await interaction.user.edit(
            nick=f"{numero_id} | {nome_original}"
        )

        embed = discord.Embed(
            title="✅ ID gerado com sucesso!",
            description=(
                f"🆔 Seu novo ID é: **{numero_id}**\n\n"
                f"🆔 Guarde ele, vai ser essencial para o seu roleplay!\n\n"
                f"⚠️ Caso queira trocar peça para alguém de alto nível trocar (explique um motivo)."
            ),
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    except discord.Forbidden:

        embed = discord.Embed(
            title="❌ Erro na geração",
            description=(
                "Não tenho permissão para alterar seu nome.\n\n"
                "Caso você seja staff o erro é comum, mas caso tenha um cargo baixo reporte o erro."
            ),
            color=discord.Color.red()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

@bot.tree.command(
    name="resetid",
    description="Remove o ID de um usuário"
)
@app_commands.describe(usuario="Usuário que terá o ID removido")
async def resetid(
    interaction: discord.Interaction,
    usuario: discord.Member
):

    if not tem_cargo_permitido(interaction):
        await interaction.response.send_message(
            "Sem permissão.",
            ephemeral=True
        )
        return

    if usuario.id in user_ids:
        del user_ids[usuario.id]

    nome = usuario.display_name

    nome_sem_id = re.sub(
        r"^\d{4}\s*\|\s*",
        "",
        nome
    ).strip()

    try:
        await usuario.edit(
            nick=nome_sem_id if nome_sem_id else None
        )

        await interaction.response.send_message(
            f"✅ ID removido de {usuario.mention}.",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "Não tenho permissão para alterar este usuário.",
            ephemeral=True
        )

@bot.tree.command(
    name="anuncio",
    description="Envia um anúncio em embed"
)
@app_commands.describe(
    mensagem="Mensagem do anúncio"
)
async def anuncio(
    interaction: discord.Interaction,
    mensagem: str
):

    if not tem_cargo_permitido(interaction):
        await interaction.response.send_message(
            "Sem permissão.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        description=mensagem,
        color=discord.Color.blue()
    )

    await interaction.response.send_message(
        embed=embed
    )

bot.run(TOKEN)
