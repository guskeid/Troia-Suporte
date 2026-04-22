import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta

# --- HIERARQUIA DE CARGOS (Do maior para o menor) ---
# Esta lista define a ordem de importância para evitar abusos entre a equipe.
CARGOS_HIERARQUIA = [
    "Troia | Dono",
    "Troia | Diretor",
    "Troia | Developer",
    "Troia | Administrador",
    "Troia | Moderador",
    "Troia | Suporte",
    "Troia | Equipe"
]

# Canal onde os logs de moderação serão enviados
ID_CANAL_LOG_MODERACAO = 1496640878062600212


async def enviar_log_moderacao(interaction: discord.Interaction, embed: discord.Embed):
    """Envia o embed de moderação para o canal de logs configurado."""
    canal = interaction.guild.get_channel(ID_CANAL_LOG_MODERACAO)
    if canal:
        try:
            await canal.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

class Moderacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def tem_hierarquia_superior(self, autor: discord.Member, alvo: discord.Member) -> bool:
        """
        Verifica se o autor do comando tem uma posição superior ao alvo na lista de cargos.
        Retorna True se o autor puder punir o alvo.
        """
        if autor.guild_permissions.administrator and not alvo.guild_permissions.administrator:
            return True
            
        def get_peso(member):
            for i, nome_cargo in enumerate(CARGOS_HIERARQUIA):
                if discord.utils.get(member.roles, name=nome_cargo):
                    return len(CARGOS_HIERARQUIA) - i
            return 0

        return get_peso(autor) > get_peso(alvo)

    def criar_embed_mod(self, titulo, cor, usuario, staff, motivo, extra_name=None, extra_val=None):
        embed = discord.Embed(
            title=titulo,
            color=cor,
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Usuário Afetado:", value=f"{usuario.mention} (`{usuario.id}`)", inline=False)
        embed.add_field(name="👮 Responsável:", value=f"{staff.mention}", inline=False)
        if extra_name and extra_val:
            embed.add_field(name=extra_name, value=extra_val, inline=True)
        embed.add_field(name="📝 Motivo:", value=motivo, inline=False)
        embed.set_footer(text="Troia Roleplay - Sistema de Gestão")
        return embed

    @app_commands.command(name="banir", description="Bane um usuário do servidor.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def banir(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Violação das diretrizes"):
        if usuario.id == interaction.user.id:
            return await interaction.response.send_message("❌ Você não pode banir a si mesmo.", ephemeral=True)
        
        if not self.tem_hierarquia_superior(interaction.user, usuario):
            return await interaction.response.send_message("❌ Hierarquia insuficiente! Você não pode banir um membro com cargo igual ou superior ao seu.", ephemeral=True)

        try:
            embed = self.criar_embed_mod("🔨 Usuário Banido", discord.Color.red(), usuario, interaction.user, motivo)
            await usuario.ban(reason=motivo)
            await interaction.response.send_message(embed=embed)
            await enviar_log_moderacao(interaction, embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao processar banimento: {e}", ephemeral=True)

    @app_commands.command(name="kickar", description="Expulsa um usuário do servidor.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kickar(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Comportamento inadequado"):
        if not self.tem_hierarquia_superior(interaction.user, usuario):
            return await interaction.response.send_message("❌ Hierarquia insuficiente para expulsar este membro.", ephemeral=True)

        try:
            embed = self.criar_embed_mod("👢 Usuário Expulso", discord.Color.orange(), usuario, interaction.user, motivo)
            await usuario.kick(reason=motivo)
            await interaction.response.send_message(embed=embed)
            await enviar_log_moderacao(interaction, embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao expulsar: {e}", ephemeral=True)

    @app_commands.command(name="mutar", description="Aplica um castigo (timeout) ao usuário.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mutar(self, interaction: discord.Interaction, usuario: discord.Member, minutos: int, motivo: str = "Não especificado"):
        if not self.tem_hierarquia_superior(interaction.user, usuario):
            return await interaction.response.send_message("❌ Você não pode silenciar um superior.", ephemeral=True)

        try:
            tempo = timedelta(minutes=minutos)
            await usuario.timeout(tempo, reason=motivo)
            
            embed = self.criar_embed_mod("🔇 Usuário Silenciado", discord.Color.gold(), usuario, interaction.user, motivo, "⏳ Duração:", f"{minutos} minuto(s)")
            await interaction.response.send_message(embed=embed)
            await enviar_log_moderacao(interaction, embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao aplicar silenciamento: {e}", ephemeral=True)

    @app_commands.command(name="desmutar", description="Remove o castigo de um usuário.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def desmutar(self, interaction: discord.Interaction, usuario: discord.Member):
        try:
            await usuario.timeout(None)
            await interaction.response.send_message(f"✅ O silenciamento de {usuario.mention} foi revogado.", ephemeral=True)

            embed = discord.Embed(title="🔊 Silenciamento Revogado", color=discord.Color.green(), timestamp=datetime.now())
            embed.add_field(name="👤 Usuário:", value=f"{usuario.mention} (`{usuario.id}`)", inline=False)
            embed.add_field(name="👮 Responsável:", value=interaction.user.mention, inline=False)
            embed.set_footer(text="Troia Roleplay - Sistema de Gestão")
            await enviar_log_moderacao(interaction, embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao remover silenciamento: {e}", ephemeral=True)

    @app_commands.command(name="limpar", description="Remove mensagens do canal atual.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def limpar(self, interaction: discord.Interaction, quantidade: int):
        if quantidade < 1 or quantidade > 100:
            return await interaction.response.send_message("❌ Por favor, escolha um valor entre 1 e 100.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            deletadas = await interaction.channel.purge(limit=quantidade)
            await interaction.followup.send(f"🧹 Foram removidas `{len(deletadas)}` mensagens.", ephemeral=True)

            embed = discord.Embed(title="🧹 Mensagens Removidas", color=discord.Color.light_grey(), timestamp=datetime.now())
            embed.add_field(name="📁 Canal:", value=interaction.channel.mention, inline=False)
            embed.add_field(name="📊 Quantidade:", value=f"`{len(deletadas)}` mensagens", inline=True)
            embed.add_field(name="👮 Responsável:", value=interaction.user.mention, inline=True)
            embed.set_footer(text="Troia Roleplay - Sistema de Gestão")
            await enviar_log_moderacao(interaction, embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao limpar mensagens: {e}", ephemeral=True)

    @app_commands.command(name="advertir", description="Aplica uma advertência a um usuário.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def advertir(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Não especificado"):
        if usuario.id == interaction.user.id:
            return await interaction.response.send_message("❌ Você não pode advertir a si mesmo.", ephemeral=True)

        if usuario.bot:
            return await interaction.response.send_message("❌ Não é possível advertir bots.", ephemeral=True)

        if not self.tem_hierarquia_superior(interaction.user, usuario):
            return await interaction.response.send_message("❌ Hierarquia insuficiente para advertir este membro.", ephemeral=True)

        embed = self.criar_embed_mod("⚠️ Usuário Advertido", discord.Color.yellow(), usuario, interaction.user, motivo)

        try:
            dm_embed = discord.Embed(
                title="⚠️ Você recebeu uma advertência",
                description=f"Você foi advertido em **{interaction.guild.name}**.",
                color=discord.Color.yellow(),
                timestamp=datetime.now()
            )
            dm_embed.add_field(name="📝 Motivo:", value=motivo, inline=False)
            dm_embed.add_field(name="👮 Aplicado por:", value=interaction.user.name, inline=False)
            await usuario.send(embed=dm_embed)
        except (discord.Forbidden, discord.HTTPException):
            embed.add_field(name="📬 DM:", value="Não foi possível notificar o usuário por mensagem direta.", inline=False)

        await interaction.response.send_message(embed=embed)
        await enviar_log_moderacao(interaction, embed)

    @app_commands.command(name="desbanir", description="Remove o banimento de um usuário pelo ID.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def desbanir(self, interaction: discord.Interaction, user_id: str, motivo: str = "Banimento revogado"):
        try:
            user_id_int = int(user_id)
        except ValueError:
            return await interaction.response.send_message("❌ ID inválido. Forneça um ID numérico do usuário.", ephemeral=True)

        try:
            user = await self.bot.fetch_user(user_id_int)
            await interaction.guild.unban(user, reason=motivo)

            embed = discord.Embed(
                title="🔓 Usuário Desbanido",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="👤 Usuário:", value=f"{user.mention} (`{user.id}`)", inline=False)
            embed.add_field(name="👮 Responsável:", value=interaction.user.mention, inline=False)
            embed.add_field(name="📝 Motivo:", value=motivo, inline=False)
            embed.set_footer(text="Troia Roleplay - Sistema de Gestão")
            await interaction.response.send_message(embed=embed)
            await enviar_log_moderacao(interaction, embed)
        except discord.NotFound:
            await interaction.response.send_message("❌ Este usuário não está banido ou não existe.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao desbanir: {e}", ephemeral=True)

    @app_commands.command(name="slowmode", description="Define o modo lento do canal (em segundos).")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, segundos: int):
        if segundos < 0 or segundos > 21600:
            return await interaction.response.send_message("❌ O valor deve estar entre 0 e 21600 segundos (6 horas).", ephemeral=True)

        try:
            await interaction.channel.edit(slowmode_delay=segundos)
            if segundos == 0:
                await interaction.response.send_message("✅ Modo lento **desativado** neste canal.")
            else:
                await interaction.response.send_message(f"🐢 Modo lento definido para **{segundos} segundo(s)** neste canal.")

            embed = discord.Embed(title="🐢 Slowmode Alterado", color=discord.Color.teal(), timestamp=datetime.now())
            embed.add_field(name="📁 Canal:", value=interaction.channel.mention, inline=False)
            embed.add_field(name="⏱️ Novo valor:", value=f"`{segundos}` segundo(s)" if segundos > 0 else "Desativado", inline=True)
            embed.add_field(name="👮 Responsável:", value=interaction.user.mention, inline=True)
            embed.set_footer(text="Troia Roleplay - Sistema de Gestão")
            await enviar_log_moderacao(interaction, embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao alterar o modo lento: {e}", ephemeral=True)

    @app_commands.command(name="lockar", description="Bloqueia o canal atual para os membros comuns.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lockar(self, interaction: discord.Interaction, motivo: str = "Não especificado"):
        try:
            everyone = interaction.guild.default_role
            overwrite = interaction.channel.overwrites_for(everyone)
            overwrite.send_messages = False
            await interaction.channel.set_permissions(everyone, overwrite=overwrite, reason=motivo)

            embed = discord.Embed(
                title="🔒 Canal Bloqueado",
                description=f"O canal {interaction.channel.mention} foi bloqueado.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="👮 Responsável:", value=interaction.user.mention, inline=False)
            embed.add_field(name="📝 Motivo:", value=motivo, inline=False)
            embed.set_footer(text="Troia Roleplay - Sistema de Gestão")
            await interaction.response.send_message(embed=embed)
            await enviar_log_moderacao(interaction, embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao bloquear o canal: {e}", ephemeral=True)

    @app_commands.command(name="desbloquear", description="Desbloqueia o canal atual.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def desbloquear(self, interaction: discord.Interaction):
        try:
            everyone = interaction.guild.default_role
            overwrite = interaction.channel.overwrites_for(everyone)
            overwrite.send_messages = None
            await interaction.channel.set_permissions(everyone, overwrite=overwrite, reason=f"Desbloqueado por {interaction.user}")

            embed = discord.Embed(
                title="🔓 Canal Desbloqueado",
                description=f"O canal {interaction.channel.mention} foi desbloqueado.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="👮 Responsável:", value=interaction.user.mention, inline=False)
            embed.set_footer(text="Troia Roleplay - Sistema de Gestão")
            await interaction.response.send_message(embed=embed)
            await enviar_log_moderacao(interaction, embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao desbloquear o canal: {e}", ephemeral=True)

    @app_commands.command(name="nick", description="Altera o apelido de um usuário (deixe em branco para resetar).")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def nick(self, interaction: discord.Interaction, usuario: discord.Member, novo_nick: str = None):
        if not self.tem_hierarquia_superior(interaction.user, usuario) and usuario.id != interaction.user.id:
            return await interaction.response.send_message("❌ Hierarquia insuficiente para alterar o apelido deste membro.", ephemeral=True)

        if novo_nick and len(novo_nick) > 32:
            return await interaction.response.send_message("❌ O apelido deve ter no máximo 32 caracteres.", ephemeral=True)

        try:
            apelido_antigo = usuario.display_name
            await usuario.edit(nick=novo_nick, reason=f"Alterado por {interaction.user}")

            embed = discord.Embed(
                title="✏️ Apelido Alterado",
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )
            embed.add_field(name="👤 Usuário:", value=usuario.mention, inline=False)
            embed.add_field(name="📛 Antes:", value=f"`{apelido_antigo}`", inline=True)
            embed.add_field(name="🆕 Agora:", value=f"`{novo_nick if novo_nick else usuario.name}`", inline=True)
            embed.add_field(name="👮 Responsável:", value=interaction.user.mention, inline=False)
            embed.set_footer(text="Troia Roleplay - Sistema de Gestão")
            await interaction.response.send_message(embed=embed)
            await enviar_log_moderacao(interaction, embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Não tenho permissão para alterar o apelido deste usuário.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao alterar apelido: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderacao(bot))