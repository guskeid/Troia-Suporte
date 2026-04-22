import discord
from discord import ui, app_commands
from discord.ext import commands

# --- CONFIGURAÇÃO ---
# Coloque aqui o ID do cargo que o jogador deve receber ao clicar no botão
ID_CARGO_VERIFICADO = 1496640175646838824
LINK_LOGO = "https://media.discordapp.net/attachments/1256047555435954291/1280596882405589093/Icon.png"

class VerificacaoView(ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Define como persistente

    @ui.button(label="Verificar", style=discord.ButtonStyle.success, emoji="✅", custom_id="verificar_usuario_troia")
    async def verificar(self, interaction: discord.Interaction, button: ui.Button):
        role = interaction.guild.get_role(ID_CARGO_VERIFICADO)
        
        if not role:
            return await interaction.response.send_message("❌ Erro: O cargo de verificação não foi encontrado nas configurações do bot.", ephemeral=True)
            
        if role in interaction.user.roles:
            return await interaction.response.send_message("⚠️ Você já possui acesso ao servidor!", ephemeral=True)

        try:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✅ Verificação concluída! Agora você pode ver o restante dos canais.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Eu não tenho permissão para entregar cargos. Verifique se o meu cargo está acima do cargo de verificação na lista de cargos do servidor!", ephemeral=True)

class Verificacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_verificacao", description="Envia o painel de verificação inicial.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_verificacao(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛡️ PORTAL DE SEGURANÇA - TROIA RP",
            description=(
                "Seja bem-vindo à nossa recepção.\n\n"
                "Para garantir a segurança da comunidade e evitar bots, pedimos que clique no botão abaixo para confirmar a sua identidade e libertar o acesso aos canais da cidade."
            ),
            color=0x2b2d31
        )
        embed.set_thumbnail(url=LINK_LOGO)
        embed.set_footer(text="Troia Roleplay • Sistema Anti-Bot")
        
        await interaction.channel.send(embed=embed, view=VerificacaoView())
        await interaction.response.send_message("✅ Painel de verificação enviado com sucesso!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Verificacao(bot))