import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime

# Configurações
NOME_CARGO_STAFF = "Suporte"

class ConfirmCloseView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Finalizar Ticket", style=discord.ButtonStyle.red, custom_id="btn_fechar_ticket")
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verificação de permissão (Staff ou Admin)
        role_staff = discord.utils.get(interaction.guild.roles, name=NOME_CARGO_STAFF)
        is_staff = (role_staff in interaction.user.roles) if role_staff else False
        
        if not is_staff and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Apenas a equipe de suporte pode finalizar este ticket!", ephemeral=True)

        # Log de fechamento
        wl_cog = self.bot.get_cog("Whitelist")
        if wl_cog:
            await wl_cog.log_ticket(interaction, "Fechado", interaction.user, f"Ticket {interaction.channel.name} finalizado.")

        await interaction.response.send_message("✅ O ticket será arquivado e apagado em 5 segundos...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.green, custom_id="btn_abrir_ticket", emoji="🎫")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        
        # Gerenciamento de Categoria
        categoria = discord.utils.get(guild.categories, name="Tickets")
        if not categoria:
            categoria = await guild.create_category("Tickets")

        # Verificação de ticket existente (Correção para o erro de NoneType)
        for canal_existente in categoria.channels:
            if canal_existente.topic and str(interaction.user.id) in canal_existente.topic:
                return await interaction.response.send_message("⚠️ Você já possui um ticket em andamento!", ephemeral=True)

        # Criação do canal com tópico definido
        canal = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=categoria,
            topic=f"Ticket de {interaction.user.name} (ID: {interaction.user.id})"
        )
        
        # Configuração de Permissões
        await canal.set_permissions(guild.default_role, view_channel=False)
        await canal.set_permissions(interaction.user, view_channel=True, send_messages=True, attach_files=True, embed_links=True)
        
        cargo_staff = discord.utils.get(guild.roles, name=NOME_CARGO_STAFF)
        if cargo_staff:
            await canal.set_permissions(cargo_staff, view_channel=True, send_messages=True, manage_messages=True)

        # Log de Abertura
        wl_cog = self.bot.get_cog("Whitelist")
        if wl_cog:
            await wl_cog.log_ticket(interaction, "Aberto", interaction.user, "Suporte solicitado via painel.")

        embed = discord.Embed(
            title="🎫 Suporte Troia RP", 
            description=f"Olá {interaction.user.mention},\n\nObrigado por entrar em contato! Descreva sua dúvida ou problema detalhadamente abaixo para que nossa equipe possa te ajudar.",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="Aguarde um membro da equipe assumir o atendimento.")
        
        await canal.send(embed=embed, view=ConfirmCloseView(self.bot))
        await interaction.response.send_message(f"✅ Seu ticket foi criado com sucesso: {canal.mention}", ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_ticket", description="Envia o painel de abertura de tickets")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Central de Atendimento - Troia RP",
            description=(
                "Precisa de ajuda com algum problema, denúncia ou dúvida?\n\n"
                "• Clique no botão abaixo para abrir um atendimento privado.\n"
                "• O tempo de resposta pode variar conforme a demanda.\n"
                "• Evite marcar a staff desnecessariamente."
            ),
            color=0x2b2d31
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1256047555435954291/1280596882405589093/Icon.png")
        
        await interaction.channel.send(embed=embed, view=TicketView(self.bot))
        await interaction.response.send_message("✅ Painel de suporte configurado!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))