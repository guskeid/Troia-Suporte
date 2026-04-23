import discord
from discord import app_commands, ui
from discord.ext import commands
from datetime import datetime
import json
import os

# --- CONFIGURAÇÕES DE CANAIS E CARGOS ---
ID_CANAL_RESPOSTAS_STAFF = 1493387255425794048
ID_CANAL_LOG_AUDITORIA = 1494088845082497115
ID_CANAL_LOG_TICKETS = 1494092811862147164

NOME_CARGO_CIDADAO = "Cidadão"
NOME_CARGO_STAFF = "Suporte"
DIAS_MINIMOS_CONTA = 7

# Persistência de aplicações pendentes
WHITELIST_STATE_FILE = "data/whitelist_state.json"


def carregar_estado() -> dict:
    if not os.path.exists(WHITELIST_STATE_FILE):
        return {"pending": []}
    try:
        with open(WHITELIST_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("pending", [])
            return data
    except Exception:
        return {"pending": []}


def salvar_estado(estado: dict) -> None:
    os.makedirs(os.path.dirname(WHITELIST_STATE_FILE), exist_ok=True)
    with open(WHITELIST_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2)


def marcar_pendente(user_id: int) -> None:
    estado = carregar_estado()
    if user_id not in estado["pending"]:
        estado["pending"].append(user_id)
        salvar_estado(estado)


def remover_pendente(user_id: int) -> None:
    estado = carregar_estado()
    if user_id in estado["pending"]:
        estado["pending"].remove(user_id)
        salvar_estado(estado)


def esta_pendente(user_id: int) -> bool:
    return user_id in carregar_estado()["pending"]


# ============================================================
# DECISÃO DA STAFF (Aprovar / Reprovar / Em Análise)
# ============================================================

class MotivoReprovacaoModal(ui.Modal, title="Motivo da Reprovação"):
    motivo = ui.TextInput(
        label="Por que essa Whitelist está sendo reprovada?",
        placeholder="Ex: Respostas copiadas / Não compreende as regras de RP",
        style=discord.TextStyle.paragraph,
        min_length=10,
        max_length=500
    )

    def __init__(self, decision_view: "WhitelistDecisionView"):
        super().__init__()
        self.decision_view = decision_view

    async def on_submit(self, interaction: discord.Interaction):
        await self.decision_view.executar_reprovacao(interaction, self.motivo.value)


class WhitelistDecisionView(ui.View):
    """Botões de decisão no canal da Staff."""
    def __init__(self, user_id: int, character_name: str, answers: dict):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.character_name = character_name
        self.answers = answers

    async def check_permissions(self, interaction: discord.Interaction) -> bool:
        role = discord.utils.get(interaction.guild.roles, name=NOME_CARGO_STAFF)
        is_staff = (role in interaction.user.roles) if role else False
        if is_staff or interaction.user.guild_permissions.administrator:
            return True
        await interaction.response.send_message(
            f"❌ Apenas a equipe de **{NOME_CARGO_STAFF}** pode fazer isso.",
            ephemeral=True
        )
        return False

    async def send_audit_log(self, interaction: discord.Interaction, action: str, color: discord.Color, motivo: str | None = None):
        canal_log = interaction.guild.get_channel(ID_CANAL_LOG_AUDITORIA)
        if not canal_log:
            return

        embed = discord.Embed(
            title=f"📑 Auditoria: Whitelist {action}",
            color=color,
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Candidato:", value=f"<@{self.user_id}> (`{self.user_id}`)", inline=True)
        embed.add_field(name="👮 Responsável:", value=interaction.user.mention, inline=True)
        embed.add_field(name="🎭 Nome RP:", value=f"`{self.character_name}`", inline=False)

        if motivo:
            embed.add_field(name="📝 Motivo:", value=motivo, inline=False)

        res_txt = ""
        for p, r in self.answers.items():
            res_txt += f"**{p}:** {r}\n\n"
        embed.add_field(name="📋 Respostas:", value=res_txt[:1024], inline=False)

        embed.set_footer(text="Troia Roleplay - Sistema de Segurança")
        await canal_log.send(embed=embed)

    @ui.button(label="Em Análise", style=discord.ButtonStyle.primary, emoji="🟡", custom_id="wl_em_analise")
    async def em_analise(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_permissions(interaction):
            return

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.gold()

        # Atualiza ou adiciona o campo "Em análise por"
        for i, field in enumerate(embed.fields):
            if field.name.startswith("🔍 Em análise por"):
                embed.set_field_at(i, name="🔍 Em análise por:", value=interaction.user.mention, inline=False)
                break
        else:
            embed.add_field(name="🔍 Em análise por:", value=interaction.user.mention, inline=False)

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(
            f"✅ Você marcou esta WL como **em análise**. Agora outros membros sabem que você já está avaliando.",
            ephemeral=True
        )

    @ui.button(label="Aprovar", style=discord.ButtonStyle.green, emoji="✅", custom_id="wl_approve_final")
    async def approve(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_permissions(interaction):
            return

        guild = interaction.guild
        member = guild.get_member(self.user_id)
        cargo = discord.utils.get(guild.roles, name=NOME_CARGO_CIDADAO)

        if not member:
            return await interaction.response.send_message("❌ Jogador não encontrado no servidor.", ephemeral=True)
        if not cargo:
            return await interaction.response.send_message(f"❌ Cargo `{NOME_CARGO_CIDADAO}` não encontrado.", ephemeral=True)

        await member.add_roles(cargo)
        await self.send_audit_log(interaction, "APROVADA", discord.Color.green())
        remover_pendente(self.user_id)

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ Whitelist Aprovada"
        await interaction.message.edit(content=f"Aprovado por: {interaction.user.mention}", embed=embed, view=None)

        try:
            await member.send(
                "✅ **Boas notícias!** Sua Whitelist na **Troia Roleplay** foi aprovada.\n"
                "Bem-vindo(a) à cidade. Bons RPs!"
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

        await interaction.response.send_message(f"✅ {member.mention} foi aprovado(a)!", ephemeral=True)

    @ui.button(label="Reprovar", style=discord.ButtonStyle.red, emoji="❌", custom_id="wl_reject_final")
    async def reject(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_permissions(interaction):
            return
        await interaction.response.send_modal(MotivoReprovacaoModal(self))

    async def executar_reprovacao(self, interaction: discord.Interaction, motivo: str):
        await self.send_audit_log(interaction, "REPROVADA", discord.Color.red(), motivo)
        remover_pendente(self.user_id)

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Whitelist Reprovada"
        embed.add_field(name="📝 Motivo da reprovação:", value=motivo, inline=False)
        await interaction.message.edit(content=f"Reprovado por: {interaction.user.mention}", embed=embed, view=None)

        member = interaction.guild.get_member(self.user_id)
        if member:
            try:
                dm = discord.Embed(
                    title="❌ Whitelist Reprovada",
                    description=(
                        f"Sua Whitelist na **{interaction.guild.name}** foi reprovada.\n\n"
                        "**Motivo informado pela staff:**\n"
                        f"> {motivo}\n\n"
                        "Revise o motivo, estude as regras e tente novamente quando se sentir preparado(a)."
                    ),
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                await member.send(embed=dm)
            except (discord.Forbidden, discord.HTTPException):
                pass

        await interaction.response.send_message("✅ Reprovação registrada e candidato notificado por DM.", ephemeral=True)


# ============================================================
# FORMULÁRIO - ETAPA 2 (Hard RP)
# ============================================================

class WhitelistEtapa2Modal(ui.Modal, title="Whitelist - Etapa 2/2 (Hard RP)"):
    p1 = ui.TextInput(
        label="1. Fuga policial após assalto",
        placeholder="Você é baleado em fuga (HP 30%). Como reage considerando preservação e medo IC?",
        style=discord.TextStyle.paragraph,
        min_length=50,
        max_length=600
    )
    p2 = ui.TextInput(
        label="2. Refém em cativeiro",
        placeholder="Você foi rendido e levado refém. Como age sabendo que NÃO pode usar conhecimento OOC?",
        style=discord.TextStyle.paragraph,
        min_length=50,
        max_length=600
    )
    p3 = ui.TextInput(
        label="3. Fair RP vs Power Gaming",
        placeholder="Explique a diferença e cite um exemplo prático onde a linha entre os dois é sutil.",
        style=discord.TextStyle.paragraph,
        min_length=50,
        max_length=600
    )
    p4 = ui.TextInput(
        label="4. CK (Character Kill)",
        placeholder="O que é CK, como ocorre e quais são as consequências para memórias e relações do personagem?",
        style=discord.TextStyle.paragraph,
        min_length=50,
        max_length=600
    )

    def __init__(self, dados_etapa1: dict):
        super().__init__()
        self.dados_etapa1 = dados_etapa1

    async def on_submit(self, interaction: discord.Interaction):
        canal_staff = interaction.guild.get_channel(ID_CANAL_RESPOSTAS_STAFF)
        if not canal_staff:
            return await interaction.response.send_message(
                "❌ Erro interno: canal da staff não configurado.", ephemeral=True
            )

        respostas_completas = {
            "ID no Jogo": self.dados_etapa1["id"],
            "Conceitos básicos (VDM/RDM/Meta)": self.dados_etapa1["regras"],
            "História do Personagem": self.dados_etapa1["historia"],
            "1. Fuga policial após assalto": self.p1.value,
            "2. Refém em cativeiro (sem OOC)": self.p2.value,
            "3. Fair RP vs Power Gaming": self.p3.value,
            "4. CK e suas consequências": self.p4.value,
        }

        embed = discord.Embed(
            title="📥 Nova Whitelist Recebida",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Candidato:", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=True)
        embed.add_field(
            name="🎭 Personagem:",
            value=f"`{self.dados_etapa1['nome']}` (ID: `{self.dados_etapa1['id']}`)",
            inline=True
        )

        for label, valor in respostas_completas.items():
            embed.add_field(name=f"📝 {label}:", value=valor[:1024], inline=False)

        role_staff = discord.utils.get(interaction.guild.roles, name=NOME_CARGO_STAFF)
        mention = role_staff.mention if role_staff else "@Suporte"

        view = WhitelistDecisionView(interaction.user.id, self.dados_etapa1["nome"], respostas_completas)

        # Cria uma thread privada para essa WL
        nome_thread = f"WL • {self.dados_etapa1['nome'][:40]} ({interaction.user.name[:20]})"
        try:
            thread = await canal_staff.create_thread(
                name=nome_thread,
                type=discord.ChannelType.private_thread,
                invitable=False,
                reason=f"Nova Whitelist de {interaction.user}"
            )
        except (discord.Forbidden, discord.HTTPException):
            # Fallback: se não conseguir criar thread privada, manda no canal normal
            await canal_staff.send(content=f"🔔 {mention}, nova avaliação pendente!", embed=embed, view=view)
        else:
            await thread.send(content=f"🔔 {mention}, nova avaliação pendente!", embed=embed, view=view)

        marcar_pendente(interaction.user.id)

        await interaction.response.send_message(
            "✅ **Formulário enviado com sucesso!**\n\n"
            "Suas respostas foram encaminhadas para nossa equipe. Você receberá uma DM assim que a análise for concluída.\n"
            "⚠️ Você não pode enviar outra Whitelist enquanto esta estiver em análise.",
            ephemeral=True
        )


class ContinuarEtapa2View(ui.View):
    def __init__(self, dados_etapa1: dict):
        super().__init__(timeout=600)
        self.dados_etapa1 = dados_etapa1

    @ui.button(label="Continuar para Etapa 2", style=discord.ButtonStyle.primary, emoji="➡️")
    async def continuar(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(WhitelistEtapa2Modal(self.dados_etapa1))


# ============================================================
# FORMULÁRIO - ETAPA 1 (Dados básicos)
# ============================================================

class WhitelistEtapa1Modal(ui.Modal, title="Whitelist - Etapa 1/2"):
    nome_rp = ui.TextInput(label="Nome do Personagem", placeholder="Ex: João Silva", min_length=3, max_length=50)
    id_rp = ui.TextInput(label="ID no Jogo", placeholder="Ex: 123", min_length=1, max_length=10)
    regras = ui.TextInput(
        label="Conceitos: VDM, RDM e MetaGaming",
        placeholder="Explique cada um dos 3 termos com suas próprias palavras.",
        style=discord.TextStyle.paragraph,
        min_length=30,
        max_length=600
    )
    historia = ui.TextInput(
        label="História do Personagem",
        placeholder="Conte de onde veio, motivações, profissão e objetivos na cidade.",
        style=discord.TextStyle.paragraph,
        min_length=50,
        max_length=800
    )

    async def on_submit(self, interaction: discord.Interaction):
        dados = {
            "nome": self.nome_rp.value,
            "id": self.id_rp.value,
            "regras": self.regras.value,
            "historia": self.historia.value
        }

        embed = discord.Embed(
            title="📋 Etapa 1 concluída! Vamos para a Etapa 2",
            description=(
                "Agora você responderá **4 perguntas de Hard Roleplay**. "
                "Leia com calma e responda com profundidade — respostas curtas ou copiadas serão reprovadas.\n\n"
                "**Perguntas que você vai responder:**\n"
                "1️⃣ Cenário: Fuga policial após assalto (baleado, HP 30%)\n"
                "2️⃣ Cenário: Você foi feito refém — como agir sem OOC?\n"
                "3️⃣ Diferença entre Fair RP e Power Gaming\n"
                "4️⃣ O que é CK (Character Kill) e suas consequências\n\n"
                "Quando estiver pronto, clique em **Continuar para Etapa 2**."
            ),
            color=0x2b2d31
        )
        embed.set_footer(text="Troia Roleplay • Hard RP")

        await interaction.response.send_message(embed=embed, view=ContinuarEtapa2View(dados), ephemeral=True)


# ============================================================
# BOTÃO INICIAL DO CANAL DE WHITELIST
# ============================================================

class WhitelistView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Iniciar Whitelist", style=discord.ButtonStyle.success, emoji="📝", custom_id="start_wl_v3")
    async def start_wl(self, interaction: discord.Interaction, button: ui.Button):
        # Bloqueia se já tem WL pendente
        if esta_pendente(interaction.user.id):
            return await interaction.response.send_message(
                "⚠️ Você já possui uma Whitelist **em análise**!\n"
                "Aguarde a decisão da staff antes de enviar uma nova.",
                ephemeral=True
            )

        # Verifica idade da conta
        delta = datetime.now(interaction.user.created_at.tzinfo) - interaction.user.created_at
        if delta.days < DIAS_MINIMOS_CONTA:
            return await interaction.response.send_message(
                f"❌ Sua conta do Discord é muito recente ({delta.days} dias). "
                f"Você precisa de pelo menos {DIAS_MINIMOS_CONTA} dias de conta para realizar a Whitelist.",
                ephemeral=True
            )

        await interaction.response.send_modal(WhitelistEtapa1Modal())


# ============================================================
# COG PRINCIPAL
# ============================================================

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_wl", description="Configura o painel de Whitelist")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_wl(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏙️ BEM-VINDO À TROIA ROLEPLAY",
            description=(
                "Para acessar a nossa cidade, você precisa realizar a nossa Whitelist.\n\n"
                "📌 **Regras Importantes:**\n"
                "• Responda com honestidade e profundidade.\n"
                "• Proibido o uso de IA, plágio ou respostas copiadas.\n"
                "• Contas fakes não são permitidas.\n"
                "• Você só pode ter **uma WL em análise por vez**.\n\n"
                "**O formulário tem 2 etapas:**\n"
                "1️⃣ Dados básicos do personagem + conceitos\n"
                "2️⃣ Cenários de Hard Roleplay\n\n"
                "Clique no botão abaixo para começar!"
            ),
            color=0x2b2d31
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1256047555435954291/1280596882405589093/Icon.png")
        await interaction.channel.send(embed=embed, view=WhitelistView())
        await interaction.response.send_message("✅ Painel de Whitelist configurado com sucesso!", ephemeral=True)

    # --- SISTEMA DE LOGS DE TICKET (mantido para uso pelos tickets) ---
    async def log_ticket(self, interaction: discord.Interaction, acao: str, usuario: discord.Member, motivo: str = "Não informado"):
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


async def setup(bot):
    await bot.add_cog(Whitelist(bot))
