import os
import discord
from discord.ext import commands
from discord import app_commands
import random
import re

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CARGOS_PERMITIDOS = ["Fundadores", "Donos"]

def tem_cargo_permitido(interaction: discord.Interaction) -> bool:
    nomes_cargos = [role.name for role in interaction.user.roles]
    return any(cargo in nomes_cargos for cargo in CARGOS_PERMITIDOS)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logado como {bot.user}')

@bot.tree.command(
    name="pedirid",
    description="Gera um ID aleatório e aplica no seu nickname"
)
async def pedirid(interaction: discord.Interaction):
    numero_id = random.randint(1000, 9999)

    try:
        await interaction.user.edit(
            nick=f"{interaction.user.name} | {numero_id}"
        )
        await interaction.response.send_message(
            f"Seu novo ID é: {numero_id}",
            ephemeral=True
        )
    except:
        await interaction.response.send_message(
            "Não consegui alterar seu nome. "
            "Verifique as permissões do bot.",
            ephemeral=True
        )

@bot.tree.command(
    name="resetid",
    description="Remove o ID do nickname de um usuário (apenas Fundadores e Donos)"
)
@app_commands.describe(usuario="O usuário que terá o ID removido")
async def resetid(interaction: discord.Interaction, usuario: discord.Member):
    if not tem_cargo_permitido(interaction):
        await interaction.response.send_message(
            "❌ Você não tem permissão para usar este comando. "
            "Apenas **Fundadores** e **Donos** podem usar o `/resetid`.",
            ephemeral=True
        )
        return

    nick_atual = usuario.nick or usuario.name
    novo_nick = re.sub(r'\s*\|\s*\d{4}$', '', nick_atual).strip()

    try:
        await usuario.edit(nick=novo_nick if novo_nick != usuario.name else None)
        await interaction.response.send_message(
            f"✅ ID removido do nickname de {usuario.mention}.",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Não consegui alterar o nickname desse usuário. "
            "Verifique se o bot tem permissão e se o cargo do usuário é menor que o do bot.",
            ephemeral=True
        )

bot.run(TOKEN)
