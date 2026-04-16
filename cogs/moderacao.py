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
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao aplicar silenciamento: {e}", ephemeral=True)

    @app_commands.command(name="desmutar", description="Remove o castigo de um usuário.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def desmutar(self, interaction: discord.Interaction, usuario: discord.Member):
        try:
            await usuario.timeout(None)
            await interaction.response.send_message(f"✅ O silenciamento de {usuario.mention} foi revogado.", ephemeral=True)
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
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao limpar mensagens: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderacao(bot))