import discord
from discord import app_commands, ui
from discord.ext import commands
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES DE CANAIS E CARGOS ---
ID_CANAL_RESPOSTAS_STAFF = 1493387255425794048 # Canal onde a staff avalia
ID_CANAL_LOG_AUDITORIA = 1494088845082497115    # Canal de logs de WL (Aprovados/Reprovados)
ID_CANAL_LOG_TICKETS = 1494092811862147164      # Canal de logs de suporte/tickets

NOME_CARGO_CIDADAO = "Cidadão"
NOME_CARGO_STAFF = "Suporte" 
DIAS_MINIMOS_CONTA = 7 # Segurança: conta deve ter +7 dias

class WhitelistDecisionView(ui.View):
    """Gerencia os botões de Aprovar/Reprovar no canal da Staff."""
    def __init__(self, user_id, character_name, answers):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.character_name = character_name
        self.answers = answers

    async def check_permissions(self, interaction: discord.Interaction) -> bool:
        """Verifica se quem clicou tem cargo de Suporte ou é Admin."""
        role = discord.utils.get(interaction.guild.roles, name=NOME_CARGO_STAFF)
        is_staff = (role in interaction.user.roles) if role else False
        if is_staff or interaction.user.guild_permissions.administrator:
            return True
        
        await interaction.response.send_message(f"❌ Apenas a equipe de **{NOME_CARGO_STAFF}** pode fazer isso.", ephemeral=True)
        return False

    async def send_audit_log(self, interaction: discord.Interaction, action: str, color: discord.Color):
        """Envia um log detalhado da decisão para o canal de auditoria."""
        canal_log = interaction.guild.get_channel(ID_CANAL_LOG_AUDITORIA)
        if not canal_log: return

        embed = discord.Embed(
            title=f"📑 Auditoria: Whitelist {action}",
            color=color,
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Candidato:", value=f"<@{self.user_id}> (`{self.user_id}`)", inline=True)
        embed.add_field(name="👮 Responsável:", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="🎭 Nome RP:", value=f"`{self.character_name}`", inline=False)

        # Formata as respostas para o log
        res_txt = ""
        for p, r in self.answers.items():
            res_txt += f"**{p}:** {r}\n"
        
        embed.add_field(name="📝 Respostas:", value=res_txt[:1024], inline=False)
        embed.set_footer(text="Troia Roleplay - Sistema de Segurança")
        await canal_log.send(embed=embed)

    @ui.button(label="Aprovar", style=discord.ButtonStyle.green, custom_id="wl_approve_final")
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_permissions(interaction): return

        guild = interaction.guild
        member = guild.get_member(self.user_id)
        cargo = discord.utils.get(guild.roles, name=NOME_CARGO_CIDADAO)

        if not member:
            return await interaction.response.send_message("❌ Jogador não encontrado no servidor.", ephemeral=True)

        await member.add_roles(cargo)
        await self.send_audit_log(interaction, "APROVADA", discord.Color.green())
        
        # Atualiza a mensagem original para evitar cliques duplos
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Whitelist Aprovada"
        await interaction.message.edit(content=f"Aprovado por: {interaction.user.mention}", embed=embed, view=None)
        
        try:
            await member.send("✅ Boas notícias! Sua Whitelist na **Troia Roleplay** foi aprovada. Divirta-se na cidade!")
        except: pass

    @ui.button(label="Reprovar", style=discord.ButtonStyle.red, custom_id="wl_reject_final")
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_permissions(interaction): return

        await self.send_audit_log(interaction, "REPROVADA", discord.Color.red())
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Whitelist Reprovada"
        await interaction.message.edit(content=f"Reprovado por: {interaction.user.mention}", embed=embed, view=None)
        
        member = interaction.guild.get_member(self.user_id)
        if member:
            try:
                await member.send("❌ Sua Whitelist na **Troia Roleplay** foi reprovada. Revise as regras e tente novamente mais tarde.")
            except: pass

class WhitelistModal(ui.Modal, title="Formulário de Whitelist - Troia RP"):
    """Formulário que o jogador preenche."""
    nome_rp = ui.TextInput(label="Nome do Personagem", placeholder="Ex: João Silva", min_length=3)
    id_rp = ui.TextInput(label="ID no Jogo", placeholder="Ex: 123", min_length=1)
    regras = ui.TextInput(label="Conceitos (VDM, RDM, MetaGaming)", style=discord.TextStyle.paragraph, min_length=20)
    historia = ui.TextInput(label="História Curta do Personagem", style=discord.TextStyle.paragraph, min_length=30)

    async def on_submit(self, interaction: discord.Interaction):
        canal_staff = interaction.guild.get_channel(ID_CANAL_RESPOSTAS_STAFF)
        
        form_data = {
            "ID": self.id_rp.value,
            "Regras": self.regras.value,
            "História": self.historia.value
        }

        embed = discord.Embed(title="📥 Nova Whitelist Recebida", color=discord.Color.blue(), timestamp=datetime.now())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Candidato:", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=True)
        embed.add_field(name="🎭 Personagem:", value=f"`{self.nome_rp.value}` (ID: `{self.id_rp.value}`)", inline=True)
        
        # Menção para alertar a staff
        role_staff = discord.utils.get(interaction.guild.roles, name=NOME_CARGO_STAFF)
        mention = role_staff.mention if role_staff else "@Suporte"

        view = WhitelistDecisionView(interaction.user.id, self.nome_rp.value, form_data)
        await canal_staff.send(content=f"🔔 {mention}, nova avaliação pendente!", embed=embed, view=view)
        await interaction.response.send_message("✅ Seu formulário foi enviado com sucesso! Aguarde a análise da nossa equipe.", ephemeral=True)

class WhitelistView(ui.View):
    """Botão inicial do canal de Whitelist."""
    def __init__(self): super().__init__(timeout=None)
    @ui.button(label="Iniciar Whitelist", style=discord.ButtonStyle.success, emoji="📝", custom_id="start_wl_v3")
    async def start_wl(self, interaction: discord.Interaction, button: ui.Button):
        # Verifica idade da conta
        delta = datetime.now(interaction.user.created_at.tzinfo) - interaction.user.created_at
        if delta.days < DIAS_MINIMOS_CONTA:
            return await interaction.response.send_message(f"❌ Sua conta do Discord é muito recente ({delta.days} dias). Você precisa de pelo menos {DIAS_MINIMOS_CONTA} dias de conta para realizar a Whitelist.", ephemeral=True)
        
        await interaction.response.send_modal(WhitelistModal())

class Whitelist(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="setup_wl", description="Configura o painel de Whitelist")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_wl(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏙️ BEM-VINDO À TROIA ROLEPLAY",
            description="Para acessar a nossa cidade, você precisa realizar a nossa Whitelist.\n\n"
                        "📌 **Regras Importantes:**\n"
                        "• Responda com honestidade.\n"
                        "• Proibido o uso de IA ou plágio.\n"
                        "• Contas fakes não são permitidas.\n\n"
                        "Clique no botão abaixo para começar o seu formulário!",
            color=0x2b2d31
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1256047555435954291/1280596882405589093/Icon.png")
        await interaction.channel.send(embed=embed, view=WhitelistView())
        await interaction.response.send_message("Painel de Whitelist configurado com sucesso!", ephemeral=True)

    # --- SISTEMA DE LOGS DE TICKET ---
    async def log_ticket(self, interaction: discord.Interaction, acao: str, usuario: discord.Member, motivo: str = "Não informado"):
        """
        Função para ser chamada quando um ticket é aberto, fechado ou assumido.
        Ação pode ser: 'Aberto', 'Fechado', 'Assumido'.
        """
        canal = self.bot.get_channel(ID_CANAL_LOG_TICKETS)
        if not canal:
            return

        cores = {
            "Aberto": discord.Color.blue(),
            "Fechado": discord.Color.red(),
            "Assumido": discord.Color.gold()
        }

        emb = discord.Embed(
            title=f"🎟️ Log de Ticket: {acao}", 
            color=cores.get(acao, discord.Color.light_grey()), 
            timestamp=datetime.now()
        )
        
        emb.add_field(name="👤 Usuário:", value=f"{usuario.mention} (`{usuario.id}`)", inline=True)
        emb.add_field(name="👮 Staff Responsável:", value=f"{interaction.user.mention}", inline=True)
        emb.add_field(name="📁 Canal:", value=f"{interaction.channel.mention}", inline=False)
        emb.add_field(name="📝 Motivo/Nota:", value=motivo, inline=False)
        
        emb.set_footer(text="Troia Roleplay - Logs de Suporte", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await canal.send(embed=emb)

async def setup(bot): await bot.add_cog(Whitelist(bot))