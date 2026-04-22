import discord
from discord.ext import commands
from datetime import datetime

ID_CANAL_BOAS_VINDAS = 1493390749142618202
LINK_LOGO = "https://media.discordapp.net/attachments/1256047555435954291/1280596882405589093/Icon.png"


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        canal = member.guild.get_channel(ID_CANAL_BOAS_VINDAS)
        if not canal:
            return

        total_membros = member.guild.member_count

        embed = discord.Embed(
            title="🏙️ BEM-VINDO À TROIA ROLEPLAY",
            description=(
                f"Olá {member.mention}, é uma honra ter você conosco!\n\n"
                f"Você é o **membro nº {total_membros}** da nossa comunidade.\n\n"
                "**📋 Primeiros passos:**\n"
                "▫️ Realize sua **verificação** para liberar o servidor\n"
                "▫️ Leia as **regras** com atenção\n"
                "▫️ Faça sua **whitelist** para entrar na cidade\n"
                "▫️ Em caso de dúvidas, abra um **ticket** no suporte\n\n"
                "Seja muito bem-vindo(a) e bons RPs!"
            ),
            color=0x2b2d31,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=LINK_LOGO)
        embed.set_author(name=f"{member.name} entrou no servidor", icon_url=member.display_avatar.url)
        embed.set_footer(
            text=f"Troia Roleplay • Conta criada em {member.created_at.strftime('%d/%m/%Y')}",
            icon_url=member.guild.icon.url if member.guild.icon else None
        )

        await canal.send(content=member.mention, embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
