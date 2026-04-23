import discord
from discord import ui, app_commands
from discord.ext import commands
import random
import string
from datetime import datetime

# --- CONFIGURAÇÃO ---
ID_CARGO_VERIFICADO = 1496640175646838824
LINK_LOGO = "https://media.discordapp.net/attachments/1256047555435954291/1280596882405589093/Icon.png"
DIAS_MINIMOS_CONTA = 7


def gerar_codigo() -> str:
    """Gera um código aleatório de 6 caracteres, evitando letras/números confusos."""
    caracteres = string.ascii_uppercase + string.digits
    for c in ("O", "0", "I", "1", "L"):
        caracteres = caracteres.replace(c, "")
    return "".join(random.choices(caracteres, k=6))


class CaptchaModal(ui.Modal, title="🛡️ Verificação - Troia RP"):
    codigo_input = ui.TextInput(
        label="Digite o código exatamente como mostrado",
        placeholder="Ex: A7F2XK",
        min_length=6,
        max_length=6
    )

    def __init__(self, codigo_correto: str):
        super().__init__()
        self.codigo_correto = codigo_correto

    async def on_submit(self, interaction: discord.Interaction):
        if self.codigo_input.value.strip().upper() != self.codigo_correto:
            return await interaction.response.send_message(
                "❌ **Código incorreto!** Clique novamente em **Verificar** no painel para receber um novo código.",
                ephemeral=True
            )

        role = interaction.guild.get_role(ID_CARGO_VERIFICADO)
        if not role:
            return await interaction.response.send_message(
                "❌ Erro: o cargo de verificação não foi encontrado. Avise um administrador.",
                ephemeral=True
            )

        if role in interaction.user.roles:
            return await interaction.response.send_message("⚠️ Você já está verificado!", ephemeral=True)

        try:
            await interaction.user.add_roles(role, reason="Captcha de verificação concluído")
            await interaction.response.send_message(
                "✅ **Verificação concluída com sucesso!** Bem-vindo(a) à Troia Roleplay.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não tenho permissão para entregar o cargo. Verifique se meu cargo está acima do cargo de verificação.",
                ephemeral=True
            )


class CaptchaConfirmView(ui.View):
    def __init__(self, codigo: str):
        super().__init__(timeout=300)
        self.codigo = codigo

    @ui.button(label="Inserir Código", style=discord.ButtonStyle.success, emoji="🔑")
    async def inserir(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(CaptchaModal(self.codigo))


class VerificacaoView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Verificar", style=discord.ButtonStyle.success, emoji="✅", custom_id="verificar_usuario_troia")
    async def verificar(self, interaction: discord.Interaction, button: ui.Button):
        role = interaction.guild.get_role(ID_CARGO_VERIFICADO)

        if not role:
            return await interaction.response.send_message(
                "❌ Erro: O cargo de verificação não foi configurado.",
                ephemeral=True
            )

        if role in interaction.user.roles:
            return await interaction.response.send_message("⚠️ Você já possui acesso ao servidor!", ephemeral=True)

        # Verifica idade mínima da conta
        delta = datetime.now(interaction.user.created_at.tzinfo) - interaction.user.created_at
        if delta.days < DIAS_MINIMOS_CONTA:
            return await interaction.response.send_message(
                f"❌ Sua conta do Discord tem apenas **{delta.days} dia(s)** de idade.\n"
                f"É necessário ter pelo menos **{DIAS_MINIMOS_CONTA} dias** para se verificar na Troia RP.",
                ephemeral=True
            )

        # Gera o captcha
        codigo = gerar_codigo()

        embed = discord.Embed(
            title="🛡️ Captcha de Verificação",
            description=(
                "Para confirmar que você é uma pessoa real, **digite o código abaixo**:\n\n"
                f"# `{codigo}`\n\n"
                "▫️ Clique no botão **🔑 Inserir Código**\n"
                "▫️ Digite o código **exatamente** como mostrado (em maiúsculas)\n"
                "▫️ Você tem **5 minutos** para concluir"
            ),
            color=0x2b2d31
        )
        embed.set_footer(text="Troia Roleplay • Sistema Anti-Bot")

        await interaction.response.send_message(embed=embed, view=CaptchaConfirmView(codigo), ephemeral=True)


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
                "Para garantir a segurança da comunidade e evitar bots, clique no botão abaixo "
                "para iniciar a verificação.\n\n"
                "**Como funciona:**\n"
                "▫️ Você receberá um **código de captcha** único\n"
                "▫️ Digite-o corretamente para liberar o acesso\n\n"
                f"⚠️ Sua conta deve ter no mínimo **{DIAS_MINIMOS_CONTA} dias** de idade."
            ),
            color=0x2b2d31
        )
        embed.set_thumbnail(url=LINK_LOGO)
        embed.set_footer(text="Troia Roleplay • Sistema Anti-Bot")

        await interaction.channel.send(embed=embed, view=VerificacaoView())
        await interaction.response.send_message("✅ Painel de verificação enviado com sucesso!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Verificacao(bot))
