import discord
from discord import app_commands, ui
from discord.ext import commands
from datetime import datetime

from cogs.moderacao import CARGOS_HIERARQUIA


class ContratarStaffView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.usuario_selecionado: discord.Member | None = None
        self.cargo_selecionado: str | None = None

        opcoes = [
            discord.SelectOption(label=cargo, value=cargo, emoji="🔰")
            for cargo in CARGOS_HIERARQUIA
        ]
        self.select_cargo.options = opcoes

    @ui.select(cls=ui.UserSelect, placeholder="👤 Selecione o usuário...", min_values=1, max_values=1)
    async def select_user(self, interaction: discord.Interaction, select: ui.UserSelect):
        membro = select.values[0]
        if isinstance(membro, discord.Member):
            self.usuario_selecionado = membro
        else:
            self.usuario_selecionado = interaction.guild.get_member(membro.id)
        await interaction.response.defer()

    @ui.select(placeholder="🔰 Selecione o cargo de staff...", min_values=1, max_values=1, options=[discord.SelectOption(label="placeholder")])
    async def select_cargo(self, interaction: discord.Interaction, select: ui.Select):
        self.cargo_selecionado = select.values[0]
        await interaction.response.defer()

    @ui.button(label="Confirmar Contratação", style=discord.ButtonStyle.success, emoji="✅", row=2)
    async def confirmar(self, interaction: discord.Interaction, button: ui.Button):
        if not self.usuario_selecionado:
            return await interaction.response.send_message("❌ Você precisa selecionar um usuário.", ephemeral=True)
        if not self.cargo_selecionado:
            return await interaction.response.send_message("❌ Você precisa selecionar um cargo.", ephemeral=True)

        cargo = discord.utils.get(interaction.guild.roles, name=self.cargo_selecionado)
        if not cargo:
            return await interaction.response.send_message(
                f"❌ O cargo `{self.cargo_selecionado}` não existe neste servidor. Crie-o primeiro.",
                ephemeral=True
            )

        if cargo >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                f"❌ Não posso atribuir `{cargo.name}` porque ele está acima do meu cargo mais alto.",
                ephemeral=True
            )

        if cargo >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(
                f"❌ Você não pode entregar um cargo igual ou superior ao seu.",
                ephemeral=True
            )

        if cargo in self.usuario_selecionado.roles:
            return await interaction.response.send_message(
                f"⚠️ {self.usuario_selecionado.mention} já possui o cargo {cargo.mention}.",
                ephemeral=True
            )

        try:
            await self.usuario_selecionado.add_roles(cargo, reason=f"Contratado por {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message("❌ Não tenho permissão para adicionar este cargo.", ephemeral=True)
        except Exception as e:
            return await interaction.response.send_message(f"❌ Erro ao atribuir cargo: {e}", ephemeral=True)

        embed = discord.Embed(
            title="✅ Novo Staff Contratado",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Membro:", value=self.usuario_selecionado.mention, inline=False)
        embed.add_field(name="🔰 Cargo Atribuído:", value=cargo.mention, inline=False)
        embed.add_field(name="👮 Contratado por:", value=interaction.user.mention, inline=False)
        embed.set_footer(text="Troia Roleplay - Sistema de Gestão")

        await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            dm = discord.Embed(
                title="🎉 Bem-vindo(a) à Equipe!",
                description=f"Você foi promovido(a) a **{cargo.name}** em **{interaction.guild.name}**.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            dm.add_field(name="👮 Contratado por:", value=interaction.user.name, inline=False)
            await self.usuario_selecionado.send(embed=dm)
        except (discord.Forbidden, discord.HTTPException):
            pass


class DemitirStaffView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.usuario_selecionado: discord.Member | None = None
        self.cargo_selecionado: str | None = None

        opcoes = [
            discord.SelectOption(label=cargo, value=cargo, emoji="❌")
            for cargo in CARGOS_HIERARQUIA
        ]
        self.select_cargo.options = opcoes

    @ui.select(cls=ui.UserSelect, placeholder="👤 Selecione o staff a ser demitido...", min_values=1, max_values=1)
    async def select_user(self, interaction: discord.Interaction, select: ui.UserSelect):
        membro = select.values[0]
        if isinstance(membro, discord.Member):
            self.usuario_selecionado = membro
        else:
            self.usuario_selecionado = interaction.guild.get_member(membro.id)
        await interaction.response.defer()

    @ui.select(placeholder="🔰 Selecione o cargo a ser removido...", min_values=1, max_values=1, options=[discord.SelectOption(label="placeholder")])
    async def select_cargo(self, interaction: discord.Interaction, select: ui.Select):
        self.cargo_selecionado = select.values[0]
        await interaction.response.defer()

    @ui.button(label="Confirmar Demissão", style=discord.ButtonStyle.danger, emoji="🗑️", row=2)
    async def confirmar(self, interaction: discord.Interaction, button: ui.Button):
        if not self.usuario_selecionado:
            return await interaction.response.send_message("❌ Você precisa selecionar um usuário.", ephemeral=True)
        if not self.cargo_selecionado:
            return await interaction.response.send_message("❌ Você precisa selecionar um cargo.", ephemeral=True)

        cargo = discord.utils.get(interaction.guild.roles, name=self.cargo_selecionado)
        if not cargo:
            return await interaction.response.send_message(
                f"❌ O cargo `{self.cargo_selecionado}` não existe neste servidor.",
                ephemeral=True
            )

        if cargo not in self.usuario_selecionado.roles:
            return await interaction.response.send_message(
                f"⚠️ {self.usuario_selecionado.mention} não possui o cargo {cargo.mention}.",
                ephemeral=True
            )

        if cargo >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(
                "❌ Você não pode remover um cargo igual ou superior ao seu.",
                ephemeral=True
            )

        try:
            await self.usuario_selecionado.remove_roles(cargo, reason=f"Demitido por {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message("❌ Não tenho permissão para remover este cargo.", ephemeral=True)
        except Exception as e:
            return await interaction.response.send_message(f"❌ Erro ao remover cargo: {e}", ephemeral=True)

        embed = discord.Embed(
            title="🗑️ Staff Demitido",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Membro:", value=self.usuario_selecionado.mention, inline=False)
        embed.add_field(name="🔰 Cargo Removido:", value=cargo.mention, inline=False)
        embed.add_field(name="👮 Demitido por:", value=interaction.user.mention, inline=False)
        embed.set_footer(text="Troia Roleplay - Sistema de Gestão")

        await interaction.response.send_message(embed=embed, ephemeral=True)

        try:
            dm = discord.Embed(
                title="📤 Aviso de Desligamento",
                description=f"Você foi removido(a) do cargo **{cargo.name}** em **{interaction.guild.name}**.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            dm.add_field(name="👮 Responsável:", value=interaction.user.name, inline=False)
            await self.usuario_selecionado.send(embed=dm)
        except (discord.Forbidden, discord.HTTPException):
            pass


class StaffPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Contratar Staff", style=discord.ButtonStyle.primary, emoji="👥", custom_id="staff_panel:contratar")
    async def contratar(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message(
                "❌ Você precisa da permissão **Gerenciar Cargos** para contratar staff.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="👥 Contratação de Staff",
            description="Selecione o **usuário** e o **cargo** que deseja atribuir, depois clique em **Confirmar Contratação**.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=ContratarStaffView(), ephemeral=True)

    @ui.button(label="Demitir Staff", style=discord.ButtonStyle.danger, emoji="📤", custom_id="staff_panel:demitir")
    async def demitir(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message(
                "❌ Você precisa da permissão **Gerenciar Cargos** para demitir staff.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📤 Demissão de Staff",
            description="Selecione o **usuário** e o **cargo** que deseja remover, depois clique em **Confirmar Demissão**.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, view=DemitirStaffView(), ephemeral=True)


class StaffPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painel-staff", description="Envia o painel de contratação de staff neste canal.")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_staff(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="👥 Painel de Contratação de Staff",
            description=(
                "Este painel permite contratar novos membros para a equipe da **Troia Roleplay**.\n\n"
                "▫️ Clique no botão abaixo para iniciar uma contratação\n"
                "▫️ Selecione o **usuário** e o **cargo** desejado\n"
                "▫️ O membro será notificado por mensagem direta\n\n"
                "**Cargos disponíveis:**\n" + "\n".join(f"• `{c}`" for c in CARGOS_HIERARQUIA)
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Troia Roleplay - Sistema de Gestão")

        await interaction.channel.send(embed=embed, view=StaffPanelView())
        await interaction.response.send_message("✅ Painel enviado com sucesso!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(StaffPanel(bot))
